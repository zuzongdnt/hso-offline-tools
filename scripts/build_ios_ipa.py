"""Bundle an arm64 embedded server with the existing privately supplied iOS client."""

import argparse
import hashlib
import plistlib
import struct
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from stage_ios_client import CLIENT, patch_client

BUNDLE = "Payload/IOSLauncher.app/"
LIBRARY = "@executable_path/Frameworks/HSOOfflineWorld.dylib"
LEGACY_LOADS = {
    "@executable_path/Frameworks/AppCenterLib.framework/AppCenterLib",
    "@executable_path/Frameworks/SDKGame.framework/SDKGame",
    "@executable_path/hhhhsd.dylib",
}
LEGACY_FILES = (
    BUNDLE + "Frameworks/AppCenterLib.framework/",
    BUNDLE + "Frameworks/SDKGame.framework/",
    BUNDLE + "hhhhsd.dylib",
)


def commands(binary):
    if binary[:8] != bytes.fromhex("cffaedfe0c000001"):
        raise ValueError("Expected a thin arm64 Mach-O.")
    count, size = struct.unpack_from("<II", binary, 16)
    end = 32 + size
    offset = 32
    for _ in range(count):
        if offset + 8 > end:
            raise ValueError("Invalid Mach-O load command bounds.")
        kind, length = struct.unpack_from("<II", binary, offset)
        if length < 8 or offset + length > end:
            raise ValueError("Invalid Mach-O load command length.")
        yield kind, offset, length
        offset += length
    if offset != end:
        raise ValueError("Invalid Mach-O command table.")


def add_library(binary):
    load_commands = list(commands(binary))
    count, size = struct.unpack_from("<II", binary, 16)
    first_section = len(binary)
    for kind, offset, command_length in load_commands:
        if kind == 0x19:
            sections = struct.unpack_from("<I", binary, offset + 64)[0]
            for index in range(sections):
                file_offset = struct.unpack_from("<I", binary, offset + 72 + index * 80 + 48)[0]
                if file_offset:
                    first_section = min(first_section, file_offset)
        if kind == 0xC and LIBRARY.encode() in binary[offset:offset + command_length]:
            raise ValueError("Embedded server is already linked.")
    name = LIBRARY.encode() + b"\0"
    length = (24 + len(name) + 7) & ~7
    end = 32 + size
    if end + length > first_section or any(binary[end:end + length]):
        raise ValueError("The client has insufficient load command padding.")
    result = bytearray(binary)
    result[end:end + length] = (struct.pack("<6I", 0xC, length, 24, 0, 0, 0) + name).ljust(length, b"\0")
    struct.pack_into("<II", result, 16, count + 1, size + length)
    list(commands(result))
    return bytes(result)


def hide_top_up_menu(client):
    # TabConfig.init normally skips the purchase entry only below level 10.
    offset = 0x344FAC
    if client[offset:offset + 8] != bytes.fromhex("cb000054828240f9"):
        raise ValueError("Unexpected iOS top-up menu layout")
    return client[:offset] + bytes.fromhex("06000014") + client[offset + 4:]


def read_uleb(data, offset):
    value = 0
    shift = 0
    while offset < len(data) and shift <= 63:
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
        shift += 7
    raise ValueError("Invalid binding integer.")


def binding_ordinals(data):
    offset = 0
    ordinal = 0
    used = set()
    while offset < len(data):
        byte = data[offset]
        offset += 1
        operation, immediate = byte & 240, byte & 15
        if operation == 0:
            ordinal = 0
        elif operation == 0x10:
            ordinal = immediate
        elif operation == 0x20:
            ordinal, offset = read_uleb(data, offset)
        elif operation == 0x30:
            ordinal = 0 if immediate == 0 else immediate - 16
        elif operation == 0x40:
            offset = data.index(0, offset) + 1
        elif operation == 0x50:
            continue
        elif operation in (0x60, 0x70, 0x80):
            _, offset = read_uleb(data, offset)
        elif operation in (0x90, 0xA0, 0xB0):
            used.add(ordinal)
            if operation == 0xA0:
                _, offset = read_uleb(data, offset)
        elif operation == 0xC0:
            count, offset = read_uleb(data, offset)
            _, offset = read_uleb(data, offset)
            if count:
                used.add(ordinal)
        elif operation == 0xD0 and immediate == 0:
            _, offset = read_uleb(data, offset)
        elif operation != 0xD0 or immediate != 1:
            raise ValueError(f"Unsupported binding opcode {byte:#x}.")
    return used


def remove_legacy_loads(binary):
    table = list(commands(binary))
    ordinal = 0
    removed_ordinals = set()
    kept = []
    dependencies = []
    used = set()
    for kind, offset, length in table:
        command = binary[offset:offset + length]
        if kind in (0xC, 0x80000018, 0x8000001F, 0x80000023):
            ordinal += 1
            name_offset = struct.unpack_from("<I", command, 8)[0]
            name = command[name_offset:].split(b"\0", 1)[0].decode()
            dependencies.append(name)
            if name in LEGACY_LOADS:
                removed_ordinals.add(ordinal)
                continue
        if kind in (0x22, 0x80000022):
            fields = struct.unpack_from("<10I", command, 8)
            for index in (2, 4, 6):
                position, size = fields[index:index + 2]
                used.update(binding_ordinals(binary[position:position + size]))
        if kind == 0x80000034:
            raise ValueError("Chained-fixup client needs a different dependency check.")
        kept.append(command)
    if set(dependencies[-3:]) != LEGACY_LOADS:
        raise ValueError("Expected three appended packaging libraries in the source client.")
    if used & removed_ordinals:
        raise ValueError("Client imports symbols from the legacy libraries.")
    first_removed = min(removed_ordinals)
    if any(order > first_removed for order in used):
        raise ValueError("Removing these libraries would renumber existing bindings.")
    content = b"".join(kept)
    previous_size = struct.unpack_from("<I", binary, 20)[0]
    result = bytearray(binary)
    result[32:32 + previous_size] = content.ljust(previous_size, b"\0")
    struct.pack_into("<II", result, 16, len(kept), len(content))
    list(commands(result))
    return bytes(result)


def minimum_os(binary):
    result = (10, 0, 0)
    for kind, offset, _ in commands(binary):
        if kind == 0x25:
            encoded = struct.unpack_from("<I", binary, offset + 8)[0]
        elif kind == 0x32:
            platform, encoded = struct.unpack_from("<II", binary, offset + 8)
            if platform != 2:
                raise ValueError("Embedded library must target iPhone devices.")
        else:
            continue
        result = max(result, (encoded >> 16, (encoded >> 8) & 255, encoded & 255))
    return ".".join(str(value) for value in result)


def verify_library(binary):
    if struct.unpack_from("<I", binary, 12)[0] != 6:
        raise ValueError("The embedded server must be a Mach-O dynamic library.")
    required = {
        "_hso_world_start", "_hso_world_save", "_hso_world_error",
        "_graal_create_isolate", "_graal_attach_thread", "_graal_detach_thread",
    }
    for kind, offset, _ in commands(binary):
        if kind != 2:
            continue
        symbols, count, strings, string_size = struct.unpack_from("<4I", binary, offset + 8)
        if symbols + count * 16 > len(binary) or strings + string_size > len(binary):
            raise ValueError("Invalid native symbol table bounds.")
        table = binary[strings:strings + string_size]
        for index in range(count):
            name_offset, symbol_type, _, description, value = struct.unpack_from("<IBBHQ", binary, symbols + 16 * index)
            end = table.find(b"\0", name_offset)
            if end < 0:
                raise ValueError("Invalid native symbol name.")
            name = table[name_offset:end].decode("utf-8")
            if symbol_type & 0x0E:
                required.discard(name)
            elif value == 0 and (description >> 8) in (0xFE, 0xFF) and name.startswith("_JVM_"):
                raise ValueError(f"Unresolved Java runtime function: {name}")
    if required:
        raise ValueError("Missing embedded server entry points: " + ", ".join(sorted(required)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ipa", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--cosmetics", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--build", default="9")
    parser.add_argument("--lite", action="store_true", help="Use x1/x2 assets and a compatible offline world")
    parser.add_argument("--dream-fashion", action="store_true", help="Enable the native iOS dream costume renderer")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Choose an unused output path.")
    native = args.library.read_bytes()
    list(commands(native))
    verify_library(native)
    pending = args.out.with_name(args.out.name + ".building")
    if pending.exists():
        parser.error("A pending output already exists. Choose an unused output path.")
    original_hash = hashlib.sha256(args.ipa.read_bytes()).digest()
    with ZipFile(args.world) as world:
        if "hso.sqlite" not in world.namelist() or "hso.conf" not in world.namelist():
            parser.error("World archive is missing its database or configuration.")
    with ZipFile(args.ipa) as source:
        executable = patch_client(source.read(CLIENT), lite=args.lite)
        executable = hide_top_up_menu(executable)
        if args.dream_fashion:
            from patch_ios_dream import patch_ios_dream
            executable = patch_ios_dream(executable)
        executable = add_library(remove_legacy_loads(executable))
        info = plistlib.loads(source.read(BUNDLE + "Info.plist"))
        info.update({
            "CFBundleIdentifier": "com.zuzong.hso.offline403",
            "CFBundleDisplayName": "HSO Offline",
            "CFBundleName": "HSO Offline",
            "CFBundleShortVersionString": "4.0.3",
            "CFBundleVersion": args.build,
            "MinimumOSVersion": minimum_os(native),
            "UIFileSharingEnabled": True,
            "LSSupportsOpeningDocumentsInPlace": True,
            "NSAppTransportSecurity": {
                "NSAllowsLocalNetworking": True,
                "NSExceptionDomains": {"127.0.0.1": {"NSExceptionAllowsInsecureHTTPLoads": True}},
            },
        })
        with ZipFile(pending, "x", ZIP_DEFLATED) as output:
            for entry in source.infolist():
                if args.lite and entry.filename.startswith((BUNDLE + "res/x3/", BUNDLE + "res/x4/")):
                    continue
                if "/_CodeSignature/" in entry.filename or entry.filename.endswith("/embedded.mobileprovision"):
                    continue
                if entry.filename.startswith(LEGACY_FILES):
                    continue
                if entry.filename == CLIENT:
                    data = executable
                elif entry.filename == BUNDLE + "Info.plist":
                    data = plistlib.dumps(info, fmt=plistlib.FMT_BINARY)
                else:
                    data = source.read(entry)
                output.writestr(entry, data)
            library_entry = ZipInfo(BUNDLE + "Frameworks/HSOOfflineWorld.dylib")
            library_entry.create_system = 3
            library_entry.external_attr = 0o100755 << 16
            library_entry.compress_type = ZIP_DEFLATED
            output.writestr(library_entry, native)
            output.write(args.world, BUNDLE + "offline/offline-world.zip", compress_type=ZIP_STORED)
            output.write(args.cosmetics, BUNDLE + "offline/offline-cosmetics.zip", compress_type=ZIP_STORED)
            if args.lite:
                output.writestr(BUNDLE + "offline/offline-lite", "2")
    with ZipFile(pending) as output:
        if output.testzip() is not None:
            raise ValueError("Output IPA archive failed integrity verification.")
        if output.read(CLIENT) != executable:
            raise ValueError("Output client does not match the patched executable.")
    if hashlib.sha256(args.ipa.read_bytes()).digest() != original_hash:
        raise ValueError("Source IPA changed during packaging.")
    pending.rename(args.out)
    print(args.out.resolve())
    print("Unsigned experimental offline IPA. Device gameplay verification is pending.")


if __name__ == "__main__":
    main()
