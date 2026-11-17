import socket
import subprocess
import time
import struct
import re
from pathlib import Path
from hso_protocol import Connection, read_ios_skills, read_utf, utf

root = Path.cwd()
with (root / "startup.log").open("w") as log:
    process = subprocess.Popen(
        [str(root / "native-world"), str(root / "world"), str(root / "fixture")],
        stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            report = (root / "startup.log").read_text(errors="replace")
            if process.poll() is not None:
                raise RuntimeError("Native world exited before readiness")
            if "IOS_WORLD_READY" in report:
                break
            time.sleep(0.5)
        else:
            raise TimeoutError("Native world failed to become ready")
        with socket.create_connection(("127.0.0.1", 19139), timeout=5) as client:
            client.sendall(bytes((216, 0, 0)))
            reply = client.recv(128)
            if not reply or reply[0] != 216:
                raise RuntimeError("Invalid native HSO handshake")
        print("Native world initialized and completed HSO handshake")
        scheduler = re.search(r"IOS_MAP_SCHEDULER maps=(\d+) workers=(\d+) javaThreads=(\d+)", report)
        if not scheduler or int(scheduler[1]) < 700 or int(scheduler[2]) != 4 or int(scheduler[3]) > 96:
            raise AssertionError("Embedded map worker/thread limit regression")
        print("Bounded map scheduler:", scheduler.group(0))
        for zoom, parts_index in ((2, 0), (4, -22031)):
            acknowledged = (root / "startup.log").read_text(errors="replace").count("IOS_CLIENT_MAP_READY map=")
            client = Connection()
            try:
                client.handshake()
                client.login("1", "1", zoom, parts_index)
                characters = None
                credentials = None
                part_messages = 0
                for _ in range(1600):
                    command, data = client.receive()
                    if command == 2:
                        raise RuntimeError("New Game login rejected")
                    if command == 13:
                        characters = data
                    if command == 31:
                        username, offset = read_utf(data)
                        password, _ = read_utf(data, offset)
                        credentials = (username, password)
                    if command == -52:
                        part_messages += 1
                    if characters is not None and credentials is not None:
                        break
                if characters != b"\0":
                    raise AssertionError("New Game must return an empty character list")
                if parts_index != 0 and part_messages != 966:
                    raise AssertionError("New Game resource synchronization is incomplete")
                name = "guestqa" + str(zoom)
                client.send(14, b"\0" + utf(name) + b"\0\0\0")
                for _ in range(1600):
                    command, data = client.receive()
                    if command == 37:
                        raise RuntimeError("New Game character creation failed")
                    if command == 13:
                        break
                if command != 13 or data[0] != 1:
                    raise AssertionError("New Game character is missing")
                character_id = struct.unpack_from(">i", data, 1)[0]
                client.send(13, struct.pack(">bi", 0, character_id))
                skills = None
                for _ in range(1800):
                    command, data = client.receive()
                    if command == 29:
                        skills = read_ios_skills(data)
                    if command == 12:
                        if skills is None or len(skills) != 21 or len({skill[0] for skill in skills}) != 21:
                            raise AssertionError("Client cannot finish loading the skill table")
                        client.send(12)
                        break
                if command != 12:
                    raise AssertionError("New Game did not enter a map")
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    if (root / "startup.log").read_text(errors="replace").count("IOS_CLIENT_MAP_READY map=") > acknowledged:
                        break
                    time.sleep(0.05)
                else:
                    raise AssertionError("Server did not receive the map acknowledgement")
                print(f"New Game passed: zoom={zoom}, parts={part_messages}, character creation and map entry")
            finally:
                client.close()
            time.sleep(1.2)
    except Exception:
        print((root / "startup.log").read_text(errors="replace")[-16000:])
        raise
    finally:
        process.terminate()
        process.wait(timeout=10)
