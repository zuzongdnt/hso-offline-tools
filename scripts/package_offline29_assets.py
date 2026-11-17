"""Correct the fire mount's native origin and refresh the portable-data instructions."""
import argparse
import json
from pathlib import Path
import struct
import io
from PIL import Image
from zipfile import ZipFile,ZIP_DEFLATED

p=argparse.ArgumentParser()
p.add_argument('--previous',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--native-parts',type=Path,required=True)
a=p.parse_args()
if a.out.exists():p.error('Choose a new output file.')
with ZipFile(a.previous) as old,ZipFile(a.out,'x',ZIP_DEFLATED) as out:
    mounts=json.loads(old.read('data/offline-mounts.json'))
    index=next(i for i,row in enumerate(mounts) if row['id']==332)
    fire=mounts[index]
    assert fire['effect']==220 and fire['y']==[0,0,0,0]
    fire['y']=[-25,-25,-25,-25]
    packet=bytearray(old.read('data/msg/msg_26'))
    pos=2
    for _ in range(struct.unpack_from('>H',packet)[0]):
        pos+=2;pos+=8+struct.unpack_from('>H',packet,pos)[0]
    patched=False
    for table in range(8):
        count=packet[pos];pos+=1
        assert count==24+len(mounts)
        for profile in range(count):
            size=packet[pos];pos+=1
            if table==4 and profile==24+index:
                assert size==8
                packet[pos:pos+8]=struct.pack('8b',*[-25]*8);patched=True
            pos+=size
    assert patched
    replacements={
        'data/offline-mounts.json':json.dumps(mounts,ensure_ascii=False,indent=2).encode(),
        'data/msg/msg_26':packet,
        'data/offline-tools.html':(Path(__file__).resolve().parents[1]/'shared/offline-tools.html').read_bytes(),
    }
    # Reuse the native character's two eyes for the owner's invisibility indicator.
    raw=(a.native_parts/'x2/4_0').read_bytes()
    size=struct.unpack_from('>I',raw)[0]
    image=Image.open(io.BytesIO(raw[4:4+size])).convert('RGBA')
    x,y,w,h=raw[4+size:8+size]
    native_eye=image.crop((x*2,y*2,(x+w)*2,(y+h)*2))
    for zoom in range(1,5):
        name=f'data/part_char/imgver/x{zoom}/112_54'
        assert name not in old.namelist()
        eye=native_eye.resize((w*zoom,h*zoom),Image.Resampling.NEAREST)
        png=io.BytesIO();eye.save(png,format='PNG');data=png.getvalue()
        metadata=bytes([1,0,0,0,w,h])+struct.pack('>H',1)+bytes([1])+struct.pack('>hhBBB',-w//2,-28,0,0,1)
        metadata+=bytes([1])+struct.pack('>H',0)+bytes(4)
        replacements[name]=struct.pack('>I',len(data))+data+metadata
    for item in old.infolist():out.writestr(item,replacements.pop(item.filename,old.read(item)))
    for name,data in replacements.items():out.writestr(name,data)
with ZipFile(a.out) as output:assert output.testzip() is None
print(a.out.resolve())
