"""Retain native costume animation and create seated variants from the same pieces."""
import argparse
import struct
import io
import json
from pathlib import Path
from PIL import Image
from zipfile import ZipFile, ZIP_DEFLATED

parser = argparse.ArgumentParser()
parser.add_argument('--previous', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--staff-cache', type=Path)
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
    if args.staff_cache:
        cached = args.staff_cache.read_bytes()
        size = struct.unpack_from('>I', cached, 2)[0]
        image = Image.open(io.BytesIO(cached[6:6 + size])).convert('RGBA')
        metadata_size = struct.unpack_from('>H', cached, 6 + size)[0]
        metadata = cached[8 + size:]
        assert len(metadata) == metadata_size and metadata[0] == 8
        offset = 1 + metadata[0] * 5
        assert struct.unpack_from('>H', metadata, offset)[0] == 144
        catalog = json.loads(old.read('data/offline-skins.json'))
        staff = next(row for row in catalog if row['id'] == 4869)
        assert (staff['part'] % 256) + 41 == 248
        for zoom in range(1, 5):
            png = io.BytesIO()
            image.resize((image.width * zoom // 2, image.height * zoom // 2), Image.Resampling.NEAREST).save(png, format='PNG')
            data = png.getvalue()
            replacements[f'data/part_char/imgver/x{zoom}/113_248'] = struct.pack('>I', len(data)) + data + metadata
            icon = image.crop((0, 0, 74, 86))
            icon.thumbnail((17 * zoom, 17 * zoom), Image.Resampling.LANCZOS)
            canvas = Image.new('RGBA', (18 * zoom, 18 * zoom))
            canvas.alpha_composite(icon, ((canvas.width - icon.width) // 2, (canvas.height - icon.height) // 2))
            png = io.BytesIO(); canvas.save(png, format='PNG')
            replacements[f'data/icon/x{zoom}/{staff["icon"] + 2000}.png'] = png.getvalue()
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
