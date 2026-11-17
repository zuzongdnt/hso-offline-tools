"""Keep the native carp rider height steady in both horizontal directions."""
import argparse
from pathlib import Path
import struct
from zipfile import ZipFile,ZIP_DEFLATED

p=argparse.ArgumentParser();p.add_argument('--previous',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.out.exists():p.error('Choose an unused output file.')
with ZipFile(a.previous) as src,ZipFile(a.out,'x',ZIP_DEFLATED) as dst:
    packet=bytearray(src.read('data/msg/msg_26'));pos=2;patched=False
    for _ in range(struct.unpack_from('>H',packet)[0]):
        pos+=2;pos+=8+struct.unpack_from('>H',packet,pos)[0]
    for table in range(8):
        count=packet[pos];pos+=1
        for profile in range(count):
            size=packet[pos];pos+=1
            if table==2 and profile==24:
                assert size==12
                packet[pos:pos+6]=bytes([29]*6);patched=True
            pos+=size
    assert patched
    for entry in src.infolist():
        content=src.read(entry)
        if entry.filename=='data/msg/msg_26':content=packet
        if entry.filename=='data/offline-tools.html':content=(Path(__file__).resolve().parents[1]/'shared/offline-tools.html').read_bytes()
        dst.writestr(entry,content)
with ZipFile(a.out) as output:assert output.testzip() is None
print(a.out.resolve())
