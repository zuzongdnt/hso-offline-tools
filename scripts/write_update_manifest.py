"""Write a GitHub release manifest for platforms with tested update packages."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version', type=int, required=True)
parser.add_argument('--pc', type=Path, required=True)
parser.add_argument('--android', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    parser.error('Choose a new output path.')
tag = f'offline-{args.version}'
base = f'https://github.com/zuzongdnt/hso-offline-tools/releases/download/{tag}/'
manifest = {'version': args.version, 'tag': tag}
for platform, path in (('pc', args.pc), ('android', args.android)):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    manifest[platform] = {'url': base + path.name, 'sha256': digest.hexdigest(),
                          'size': path.stat().st_size}
args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(args.out.resolve())
