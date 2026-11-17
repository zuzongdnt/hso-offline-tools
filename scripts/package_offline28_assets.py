"""Retain native costume animation and create seated variants from the same pieces."""
import argparse
import struct
from zipfile import ZipFile, ZIP_DEFLATED

parser = argparse.ArgumentParser()
parser.add_argument('--previous', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()

def seated(raw):
    offset = 4 + struct.unpack_from('>I', raw)[0]
    count = raw[offset]
    descriptors = [tuple(raw[offset + 1 + i * 5:offset + 6 + i * 5]) for i in range(count)]
    position = offset + 1 + count * 5
    frame_count = struct.unpack_from('>H', raw, position)[0]
    position += 2
    frames = []
    cropped = {}
    for _ in range(frame_count):
        size = raw[position]; position += 1
        frame = []
        for _ in range(size):
            x, y, piece, flip, layer = struct.unpack_from('>hhBBB', raw, position); position += 7
            d = descriptors[piece]
            height = min(d[4], -8 - y)
            if height <= 0: continue
            if height < d[4]:
                key = (piece, height)
                if key not in cropped:
                    cropped[key] = len(descriptors)
                    descriptors.append((len(descriptors), d[1], d[2], d[3], height))
                piece = cropped[key]
            frame.append((x, y, piece, flip, layer))
        frames.append(frame)
    assert len(descriptors) < 256 and frame_count == 72
    output = bytearray(raw[:offset]); output.append(len(descriptors))
    for d in descriptors: output.extend(bytes(d))
    output.extend(struct.pack('>H', frame_count))
    for frame in frames:
        output.append(len(frame))
        for piece in frame: output.extend(struct.pack('>hhBBB', *piece))
    output.extend(raw[position:])
    return bytes(output)

with ZipFile(args.previous) as old, ZipFile(args.out, 'x', ZIP_DEFLATED) as out:
    replacements = {}
    for zoom in range(1, 5):
        for source, target in ((231, 253), (232, 254)):
            prefix = f'data/part_char/imgver/x{zoom}/113_'
            raw = old.read(prefix + str(source))
            replacements[prefix + str(target)] = raw
            replacements[prefix + str(target + 2)] = seated(raw)
    for item in old.infolist():
        out.writestr(item, replacements.pop(item.filename, old.read(item)))
    for name, data in replacements.items(): out.writestr(name, data)
with ZipFile(args.out) as result: assert result.testzip() is None
print(args.out)
