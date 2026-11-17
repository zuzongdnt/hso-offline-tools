from pathlib import Path
from io import BytesIO
import json, struct, shutil, zipfile
from PIL import Image
from tune_mount_seats import tune

root = Path("build/offline21-assets")
shutil.copytree("build/offline20-assets", root, dirs_exist_ok=True)
data = root / "data"
cache = Path.home() / "AppData/LocalLow/HiepSiOnline_400/HiepSiOnline_400"
rows_path = data / "offline-mounts.json"
rows = json.loads(rows_path.read_text(encoding="utf8"))
panda = next(row for row in rows if row["id"] == 333)
panda["lift"] = [28, 28, 25, 24]
rows_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf8")
tune(data)
packet = data / "msg/msg_26"
b = bytearray(packet.read_bytes())
p = 2
for _ in range(struct.unpack_from(">H", b)[0]):
    p += 2
    p += 8 + struct.unpack_from(">H", b, p)[0]
for t in range(3):
    count = b[p]
    p += 1
    for i in range(count):
        size = b[p]
        p += 1
        if i == 32 and t == 1:
            b[p+2:p+4] = bytes([25, 24])
        if i == 32 and t == 2:
            b[p+6:p+12] = bytes([25]*3+[24]*3)
        if i == 24 and t == 2:
            b[p:p+6] = bytes([31,29,27]*2)
        p += size
packet.write_bytes(b)

def write_effect(effect, atlas, meta):
    for zoom in range(1, 5):
        png = BytesIO()
        atlas.resize((atlas.width*zoom//2, atlas.height*zoom//2), Image.Resampling.NEAREST).save(png, 'PNG')
        raw = png.getvalue()
        (data / f'part_char/imgver/x{zoom}/113_{effect}').write_bytes(struct.pack('>I', len(raw)) + raw + meta)

for native, dest in ((137, 250), (138, 251)):
    raw = (cache / f'img_data_char_111_{native}').read_bytes()
    length = struct.unpack_from('>I', raw, 2)[0]
    atlas = Image.open(BytesIO(raw[6:6+length])).convert('RGBA')
    pos = length + 8
    end = pos + 1 + raw[pos] * 5
    metadata = bytearray(raw[pos:end])
    count = struct.unpack_from('>H', raw, end)[0]
    assert count == 144
    pos = end + 2
    frames = []
    for _ in range(count):
        parts = raw[pos]
        frame = bytearray([parts])
        pos += 1
        for _ in range(parts):
            frame += raw[pos:pos+5] + bytes([0, 1])
            pos += 5
        frames.append(frame)
    count = struct.unpack_from('>H', raw, pos)[0]
    assert count == 112
    indices = struct.unpack_from('>112H', raw, pos+2)
    metadata += struct.pack('>H', count) + b''.join(frames[i] for i in indices) + bytes(5)
    write_effect(dest, atlas, metadata)

# The rabbit is a small ornament with a direction-specific head anchor.
previous = (data/'part_char/imgver/x2/113_249').read_bytes()
length = struct.unpack_from('>I', previous)[0]
front = Image.open(BytesIO(previous[4:4+length])).convert('RGBA').crop((0,0,46,60))
front = front.crop(front.getbbox()).resize((20,21), Image.Resampling.LANCZOS)
atlas = Image.new('RGBA', (20,22))
atlas.alpha_composite(front)
frames = [struct.pack('>BhhBBB',1,x,y,0,0,1) for x,y in ((4,-38),(5,-37),(5,-36),(-15,-36))]
write_effect(252, atlas, bytes([1,0,0,0,10,11])+struct.pack('>H',4)+b''.join(frames)+bytes(5))

with zipfile.ZipFile('build/offline21-assets.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        if path.is_file():
            archive.write(path, path.relative_to(root))
