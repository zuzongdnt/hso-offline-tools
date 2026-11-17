"""HSO framing used by the native-world regression check."""

import socket
import struct
from io import BytesIO


def utf(text):
    data = text.encode("utf-8")
    return struct.pack(">H", len(data)) + data


def read_utf(data, offset=0):
    length = int.from_bytes(data[offset:offset + 2], "big")
    end = offset + 2 + length
    if end > len(data):
        raise ValueError("Truncated HSO string")
    return data[offset + 2:end].decode("utf-8"), end


def read_ios_skills(data):
    """Read command 29 in the order observed in the iOS Skill_List method."""
    packet = BytesIO(data)

    def take(size):
        result = packet.read(size)
        if len(result) != size:
            raise ValueError("Truncated iOS skill packet")
        return result

    def string():
        return take(int.from_bytes(take(2), "big")).decode("utf-8")

    skills = []
    for _ in range(take(1)[0]):
        skill_id, _ = take(2)
        name = string()
        take(3)
        string()
        take(2)
        levels = take(1)[0]
        if not 0 < levels <= 30:
            raise ValueError("Invalid iOS skill level count")
        for _ in range(levels):
            take(19)
            take(take(1)[0] * 5 + 3)
        take(3)
        skills.append((skill_id, name, levels))
    if packet.read(1):
        raise ValueError("Unexpected trailing iOS skill data")
    return skills


class Connection:
    def __init__(self):
        self.socket = socket.create_connection(("127.0.0.1", 19139), timeout=15)
        self.socket.settimeout(15)
        self.key = b""
        self.read_index = 0
        self.write_index = 0

    def close(self):
        self.socket.close()

    def exact(self, size):
        result = bytearray()
        while len(result) < size:
            chunk = self.socket.recv(size - len(result))
            if not chunk:
                raise EOFError("HSO server closed the connection")
            result.extend(chunk)
        return bytes(result)

    def xor(self, data, receiving=False):
        result = bytearray()
        position = self.read_index if receiving else self.write_index
        for byte in data:
            result.append(byte ^ self.key[position])
            position = (position + 1) % len(self.key)
        if receiving:
            self.read_index = position
        else:
            self.write_index = position
        return bytes(result)

    def send(self, command, data=b""):
        packet = struct.pack(">BH", command & 255, len(data)) + data
        self.socket.sendall(self.xor(packet) if self.key else packet)

    def receive(self):
        header = self.exact(1)
        command = (self.xor(header, True) if self.key else header)[0]
        command = command if command < 128 else command - 256
        if self.key and command == 126:
            command = self.xor(self.exact(1), True)[0]
        length_size = 4 if self.key and command in (-51, -52, -54, 25) else 2
        length = self.exact(length_size)
        if self.key:
            length = self.xor(length[::-1], True)[::-1] if length_size == 4 else self.xor(length, True)
        size = int.from_bytes(length, "big")
        if size > 8 * 1024 * 1024:
            raise ValueError("Invalid HSO packet size")
        data = self.exact(size)
        return command, self.xor(data, True) if self.key else data

    def handshake(self):
        self.send(-40)
        command, data = self.receive()
        if command != -40 or data[0] != len(data) - 1:
            raise ValueError("Invalid HSO handshake")
        key = bytearray(data[1:])
        for index in range(1, len(key)):
            key[index] ^= key[index - 1]
        self.key = bytes(key)

    def login(self, username, password, zoom, parts_index):
        payload = b"".join(utf(value) for value in (username, password, "4.0.0", "0", "0", "0"))
        payload += struct.pack(">BBibBBBBh", zoom, 3, -1, -1, 0, 9, 1, 0, parts_index)
        payload += utf("com.zuzong.hso.offline403")
        self.send(1, payload)
        self.send(61)
