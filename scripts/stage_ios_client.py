"""Prepare the native client for an embedded server. This does not build an IPA."""

import argparse
import struct
from pathlib import Path
from zipfile import ZipFile


CLIENT = "Payload/IOSLauncher.app/IOSLauncher"
OLD_HOST = b"100.106.181.57"
LOCAL_HOST = b"127.0.0.1"
OLD_LABEL = b"Zuzong"
LOCAL_LABEL = b"Offline"
OLD_PORT = 19129
LOCAL_PORT = 19139


def mov_w3(value: int) -> bytes:
    return struct.pack("<I", 0x52800003 | (value << 5))


def call_arm64(offset: int, target: int) -> bytes:
    return struct.pack("<I", 0x94000000 | (((target - offset) // 4) & 0x03FFFFFF))


def patch_client(original: bytes) -> bytes:
    if original[:8] != bytes.fromhex("cffaedfe0c000001"):
        raise ValueError("Expected the arm64 IOSLauncher from the Tailscale v2 IPA.")

    # These calls should already target the string helper in the v2 client.
    if tuple(struct.unpack_from("<I", original, offset)[0] for offset in (0x386550, 0x386568)) != (
        0x9400004C,
        0x94000046,
    ):
        raise ValueError("The v2 connection hook is missing.")

    edits = [
        (0xEF7065, OLD_HOST.ljust(16, b"\0"), LOCAL_HOST.ljust(16, b"\0")),
        (0xEE5041, OLD_HOST.ljust(16, b"\0"), LOCAL_HOST.ljust(16, b"\0")),
        (0xEE5030, OLD_LABEL.ljust(17, b"\0"), LOCAL_LABEL.ljust(17, b"\0")),
        (0x386698, mov_w3(len(OLD_HOST)), mov_w3(len(LOCAL_HOST))),
        (0x241634, mov_w3(len(OLD_HOST)), mov_w3(len(LOCAL_HOST))),
        (0x24160C, mov_w3(len(OLD_LABEL)), mov_w3(len(LOCAL_LABEL))),
        (0x386574, mov_w3(OLD_PORT), mov_w3(LOCAL_PORT)),
    ]
    # RoboVM ReadMessenge.mainCharInfo and the four bulk inventory counts.
    # The server sends shorts for these fields. Change both the read and sign extension.
    for offset in (0x9194F8, 0x936920, 0x936CC8, 0x937498, 0x937B10):
        edits.append((offset, call_arm64(offset, 0x6EC288), call_arm64(offset, 0x6EC63C)))
        edits.append((offset + 4, bytes.fromhex("081c0013"), bytes.fromhex("083c0013")))
    # Log exceptions that Skill_List otherwise silently catches. x0 is the
    # caught Throwable here; printStackTrace receives the VM env and Throwable.
    edits.append((0x929658, bytes.fromhex("e06700f9e86740f9e86300f9"),
                  bytes.fromhex("e10300aae00313aa") + call_arm64(0x929660, 0x755178)))
    patched = bytearray(original)
    for offset, expected, replacement in edits:
        end = offset + len(expected)
        if original[offset:end] != expected:
            raise ValueError(f"Unexpected bytes at {offset:#x}. Use the Tailscale v2 IPA.")
        patched[offset:end] = replacement
    return bytes(patched)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    parser.add_argument("output", type=Path, help="New .bin file for the patched IOSLauncher")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".bin":
        parser.error("Output must end in .bin.")

    try:
        with ZipFile(args.ipa) as archive:
            patched = patch_client(archive.read(CLIENT))
        with args.output.open("xb") as client:
            client.write(patched)
    except (OSError, KeyError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Prepared {args.output} for {LOCAL_HOST.decode()}:{LOCAL_PORT}")


if __name__ == "__main__":
    main()
