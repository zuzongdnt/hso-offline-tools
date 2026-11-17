"""Update side-view seat positions in an offline cosmetics overlay."""
import argparse
import json
import struct
from pathlib import Path

FIRST_IMPORTED_PROFILE = 24
DRAGONS = {326, 327}
PANDA = 333


def tune(data: Path):
    catalog = data / "offline-mounts.json"
    mounts = json.loads(catalog.read_text(encoding="utf-8"))
    # Category 4 icons are requested as icon + 4000 and routed before 5000.
    for index, mount in enumerate(mounts):
        icon = 920 + index
        for zoom in range(1, 5):
            directory = data / "icon" / f"x{zoom}"
            artwork = (directory / f"{22000 + index}.png").read_bytes()
            (directory / f"{4000 + icon}.png").write_bytes(artwork)
        mount["icon"] = icon
    packet = data / "msg/msg_26"
    payload = bytearray(packet.read_bytes())

    # Skip the mount templates to reach the per-profile animation tables.
    offset = 2
    for _ in range(struct.unpack_from(">H", payload)[0]):
        offset += 2
        offset += 8 + struct.unpack_from(">H", payload, offset)[0]

    for table in range(8):
        count = payload[offset]
        offset += 1
        if count != FIRST_IMPORTED_PROFILE + len(mounts):
            raise ValueError("Mount template and animation tables disagree")
        for profile in range(count):
            size = payload[offset]
            offset += 1
            if profile >= FIRST_IMPORTED_PROFILE:
                mount = mounts[profile - FIRST_IMPORTED_PROFILE]
                expected_size = {1: 4, 2: 12, 3: 8}.get(table)
                if expected_size is not None and size != expected_size:
                    raise ValueError(f"Invalid animation table {table} for mount {mount['id']}")
                if table == 1 and mount["id"] in DRAGONS:
                    mount["lift"][:2] = [19, 19]
                if table == 3 and mount["id"] in DRAGONS:
                    mount["x"][:2] = [-1, 1]

                if table == 1:
                    payload[offset:offset + 2] = bytes(mount["lift"][:2])
                elif table == 2:
                    # Each direction's slots are used for mount frames 3, 2, 4.
                    for side, height in enumerate(mount["lift"][:2]):
                        if mount["id"] in DRAGONS or mount["id"] == PANDA:
                            # These atlases raise the saddle by one unit per visible step.
                            phases = (height, height - 1, height + 1)
                        else:
                            phases = (height + 2, height + 1, height - 2)
                        struct.pack_into("3b", payload, offset + 3 * side, *phases)
                elif table == 3:
                    side_offsets = [x for x in mount["x"][:2] for _ in range(2)]
                    struct.pack_into("4b", payload, offset, *side_offsets)
            offset += size

    packet.write_bytes(payload)
    catalog.write_text(json.dumps(mounts, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    tune(parser.parse_args().data_dir)
