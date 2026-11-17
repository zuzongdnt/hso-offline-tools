from pathlib import Path
from io import BytesIO
import json, shutil, struct, zipfile
from PIL import Image

root = Path('build/offline22-assets')
shutil.copytree('build/offline21-assets', root, dirs_exist_ok=True)
data = root / 'data'
catalog = data / 'offline-skins.json'
items = json.loads(catalog.read_text(encoding='utf8'))
by_id = {item['id']: item for item in items}
for item_id, effect, idle, label, icon in (
    (4807, 253, 250, 'Hiệp sĩ mộng mơ', 16468),
    (4808, 254, 251, 'Hiệp sĩ mộng mơ nữ', 16469),
):
    row = by_id[item_id]
    row.update(name=label, type=15, part=0, icon=icon, bodyEffect=effect,
               fashion=[-2,-2,-2,-1,-1,-2,-2])
    row.pop('effect', None)
    for zoom in range(1,5):
        parts = data / f'part_char/imgver/x{zoom}'
        raw = (parts/f'113_{idle}').read_bytes()
        start = 4 + struct.unpack_from('>I', raw)[0]
        pos = start + 1 + raw[start]*5
        descriptors = [tuple(raw[start+1+5*i:start+6+5*i]) for i in range(raw[start])]
        count = struct.unpack_from('>H', raw, pos)[0]
        pos += 2
        frames = []
        for _ in range(count):
            n = raw[pos]
            pos += 1
            frames.append([struct.unpack_from('>hhBBB', raw, pos+7*i) for i in range(n)])
            pos += n*7
        preview = Image.new('RGBA',(64*zoom,68*zoom))
        sheet = Image.open(BytesIO(raw[4:start])).convert('RGBA')
        for x,y,piece,_,_ in frames[0]:
            if piece == 0:
                continue
            _,sx,sy,w,h = descriptors[piece]
            pic = sheet.crop((sx*zoom,sy*zoom,(sx+w)*zoom,(sy+h)*zoom))
            preview.alpha_composite(pic,((32+x)*zoom,(53+y)*zoom))
        preview = preview.crop(preview.getbbox())
        preview.thumbnail((17*zoom,17*zoom),Image.Resampling.NEAREST)
        thumbnail = Image.new('RGBA',(18*zoom,18*zoom))
        thumbnail.alpha_composite(preview,((thumbnail.width-preview.width)//2,(thumbnail.height-preview.height)//2))
        thumbnail.save(data/f'icon/x{zoom}/{icon+2000}.png')
        # Existing directional assets contain one complete 18-frame cycle per colour phase.
        base = (parts/f'113_{231+item_id-4807}').read_bytes()
        off = 4 + struct.unpack_from('>I', base)[0]
        pos = off + 1 + base[off]*5
        assert struct.unpack_from('>H',base,pos)[0] == 72
        output = bytearray(base[:pos]) + struct.pack('>H',18)
        pos += 2
        for i in range(18):
            n = base[pos]
            pos += 1
            frame = [struct.unpack_from('>hhBBB',base,pos+7*j) for j in range(n)]
            pos += n*7
            # The normal costume draws the body, face and hair. Idle particles belong to the 10-second effect.
            if 12 <= i <= 16 and len(frame) > 3:
                frame = [piece for piece in frame if descriptors[piece[2]][3:5] != (19,21)]
            output.append(len(frame))
            for piece in frame:
                output += struct.pack('>hhBBB', *piece)
        (parts/f'113_{effect}').write_bytes(output+bytes(5))
catalog.write_text(json.dumps(items, ensure_ascii=False, indent=2),encoding='utf8')
with zipfile.ZipFile('build/offline22-assets.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        if path.is_file():
            archive.write(path,path.relative_to(root))
