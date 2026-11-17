"""Install the Hiệp sĩ Mộng Mơ renderer for the known arm64 IOSLauncher."""

import struct
from pathlib import Path


CODE = 0x13C3600
EYE = CODE + 0x200
HAIR = CODE + 0x240
TABLE = 0x1C1E000
TABLE_SIZE = 128 * 32
BASE = 0x100000000


def patch_ios_dream(client: bytes) -> bytes:
    from keystone import KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN, Ks

    patched = bytearray(client)
    assembler = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    source = Path(__file__).with_name("ios_dream_arm64.s").read_text(encoding="utf-8")
    render, other = source.split("// EYE HOOK", 1)
    eye, hair = other.split("// HAIR HOOK", 1)

    # Validate and reserve the executable padding after __eh_frame and the
    # zero-fill padding after __common. No binary contents or offsets move.
    text_bounds = None
    text_used = 0
    table_reserved = False
    command = 32
    for _ in range(struct.unpack_from("<I", client, 16)[0]):
        kind, length = struct.unpack_from("<II", client, command)
        if kind == 0x19:
            name, address, size, fileoff, filesize, _, prot, count, _ = struct.unpack_from(
                "<16sQQQQIIII", client, command + 8
            )
            name = name.rstrip(b"\0")
            if name == b"__TEXT" and address == BASE and prot == 5 and fileoff == 0:
                text_bounds = filesize
            if name in (b"__TEXT", b"__DATA"):
                for index in range(count):
                    section = command + 72 + index * 80
                    section_name, _, start, span, offset = struct.unpack_from("<16s16sQQI", client, section)
                    if name == b"__TEXT":
                        text_used = max(text_used, offset + span)
                    if name == b"__DATA" and section_name.rstrip(b"\0") == b"__common":
                        if offset != 0 or not (address + filesize <= start + span <= BASE + TABLE
                                and BASE + TABLE + TABLE_SIZE <= address + size and prot == 3):
                            raise ValueError("Unexpected iOS dream timer storage layout")
                        if index != count - 1:
                            raise ValueError("Expected __common to be the last data section")
                        struct.pack_into("<Q", patched, section + 40, BASE + TABLE + TABLE_SIZE - start)
                        table_reserved = True
        command += length
    if not table_reserved or text_bounds is None or not text_used <= CODE < EYE < HAIR < text_bounds:
        raise ValueError("No reserved room for the iOS dream renderer")

    mounts = CODE + 0x280
    mount_sites = (0x2B5268, 0x2B5640)
    blocks = [(CODE, EYE, render), (EYE, HAIR, eye), (HAIR, mounts, hair)]
    for index, site in enumerate(mount_sites):
        address = mounts + index * 0x40
        blocks.append((address, address + 0x40, f'''
            ldrsb w10, [x9, #0x323]
            cmp w10, #24
            b.lt native_frame
            ldr w8, [x9, #0x16c]
        native_frame:
            strb w8, [x9, #0x31b]
            b {site + 4:#x}
        '''))
    body_frame = mounts + 0x80
    blocks.append((body_frame, body_frame + 0x60, '''
        ldrh w8, [x1, #0x2ce]
        sub w8, w8, #253
        cmp w8, #1
        b.hi native_body
        ldr w8, [x1, #0x164]
        cmp w8, #2
        mov w9, #2
        csel w8, w8, w9, lo
        ldr w9, [x1, #0x1c8]
        mov w10, #6
        udiv w11, w9, w10
        msub w9, w11, w10, w9
        madd w0, w8, w10, w9
        ret
    native_body:
        sub sp, sp, #0x10
        b 0x2a80a8
    '''))
    for offset, limit, assembly in blocks:
        if limit > text_bounds:
            raise ValueError("No room for iOS mount renderer")
        encoded = bytes(assembler.asm(assembly, addr=offset)[0])
        end = offset + len(encoded)
        if end > limit or any(client[offset:end]):
            raise ValueError("iOS dream renderer overlaps existing code")
        patched[offset:end] = encoded

    for offset, expected, target in (
        (0x2A8A74, "fc6fbca9", CODE),  # MainObject.paintPlayer
        (0x2AD8B0, "20b841b9", EYE),   # MainObject.getTypePart: eye
        (0x2A85E4, "f85fbca9", HAIR),  # MainObject.getEffMatNa
        (0x2A80A4, "ff4300d1", body_frame),  # MainObject.getFrameBody
    ):
        if client[offset:offset + 4] != bytes.fromhex(expected):
            raise ValueError(f"Unexpected original iOS dream hook at {offset:#x}")
        patched[offset:offset + 4] = bytes(assembler.asm(f"b {target:#x}", addr=offset)[0])
    expected = bytes(assembler.asm("strb w8, [x9, #0x31b]")[0])
    for index, site in enumerate(mount_sites):
        if client[site:site + 4] != expected:
            raise ValueError(f"Unexpected original iOS mount hook at {site:#x}")
        target = mounts + index * 0x40
        patched[site:site + 4] = bytes(assembler.asm(f"b {target:#x}", addr=site)[0])
    return bytes(patched)
