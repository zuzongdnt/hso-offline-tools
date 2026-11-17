"""Repackage the verified offline 26 PC update with the offline 27 server."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--previous', type=Path, required=True)
parser.add_argument('--server', type=Path, required=True)
parser.add_argument('--version', type=int, default=27)
parser.add_argument('--client', type=Path)
parser.add_argument('--cosmetics', type=Path)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    parser.error('Choose a new output path.')
with ZipFile(args.previous) as previous:
    if previous.testzip() is not None:
        raise ValueError('Previous update is corrupt.')
    manifest = json.loads(previous.read('files.json'))
    if manifest['version'] >= args.version:
        raise ValueError('New version must be greater than the previous update.')
    names = set(previous.namelist())
    expected = {'CAP_NHAT.ps1', 'files.json'} | {'payload/' + row['path'] for row in manifest['files']}
    if names != expected:
        raise ValueError('Unexpected files in the previous update.')
    server_name = 'server/target/HSO_Re_2-1.0-jar-with-dependencies.jar'
    if 'payload/' + server_name not in names or 'payload/offline-version.txt' not in names:
        raise ValueError('Previous update is missing its server or version.')
    replacements = {
        'payload/' + server_name: args.server.read_bytes(),
        'payload/offline-version.txt': str(args.version).encode(),
        'payload/CAP_NHAT_TU_DONG.ps1': (Path(__file__).resolve().parents[1] / 'pc/CAP_NHAT_TU_DONG.ps1').read_text(encoding='utf-8-sig').encode('utf-8-sig'),
    }
    if args.client:
        replacements['payload/client/hso_v403_Data/Managed/Assembly-CSharp.dll'] = args.client.read_bytes()
    if args.cosmetics:
        with ZipFile(args.cosmetics) as cosmetics:
            for name in cosmetics.namelist():
                path = Path(name)
                if not name.startswith('data/') or '..' in path.parts or path.is_absolute():
                    raise ValueError('Invalid cosmetic path: ' + name)
                replacements['payload/server/' + name] = cosmetics.read(name)
    new_manifest = dict(version=args.version, files=[])
    with ZipFile(args.out, 'x', ZIP_DEFLATED) as output:
        for row in manifest['files']:
            name = 'payload/' + row['path']
            data = replacements.pop(name, None)
            if data is None:
                data = previous.read(name)
                if hashlib.sha256(data).hexdigest() != row['sha256']:
                    raise ValueError('Previous update failed a manifest hash: ' + name)
            new_manifest['files'].append(dict(path=row['path'], sha256=hashlib.sha256(data).hexdigest()))
            output.writestr(name, data)
        for name, data in replacements.items():
            new_manifest['files'].append(dict(path=name.removeprefix('payload/'), sha256=hashlib.sha256(data).hexdigest()))
            output.writestr(name, data)
        output.writestr('CAP_NHAT.ps1', (Path(__file__).resolve().parents[1] / 'pc/CAP_NHAT.ps1').read_text(encoding='utf-8-sig').encode('utf-8-sig'))
        output.writestr('files.json', json.dumps(new_manifest, ensure_ascii=False, indent=2).encode())
with ZipFile(args.out) as result:
    if result.testzip() is not None:
        raise ValueError('New update failed ZIP integrity check.')
print(args.out.resolve())
