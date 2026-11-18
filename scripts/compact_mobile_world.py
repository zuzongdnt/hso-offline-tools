"""Keep x1 and x2 server images from a previously built offline mobile package."""
import argparse
import io
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('package', type=Path)
parser.add_argument('out', type=Path)
args = parser.parse_args()
prefix = {'apk': 'assets/', 'ipa': 'Payload/IOSLauncher.app/offline/'}[args.package.suffix[1:].lower()]
high_resolution = re.compile(r'^data/(?:icon|part_char(?:/imgver)?)/x[34]/')
args.out.mkdir()
with ZipFile(args.package) as package:
    for name in ('offline-world.zip', 'offline-cosmetics.zip'):
        with ZipFile(io.BytesIO(package.read(prefix + name))) as source:
            with ZipFile(args.out / name, 'x', ZIP_DEFLATED, compresslevel=9) as output:
                for entry in source.infolist():
                    if not entry.is_dir() and not high_resolution.match(entry.filename):
                        output.writestr(entry.filename, source.read(entry))
        with ZipFile(args.out / name) as output:
            assert output.testzip() is None
        print(name, (args.out / name).stat().st_size)
