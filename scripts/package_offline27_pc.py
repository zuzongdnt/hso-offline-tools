"""Repackage the verified offline 26 PC update with the offline 27 server."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--previous', type=Path, required=True)
parser.add_argument('--server', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    parser.error('Choose a new output path.')
with ZipFile(args.previous) as previous:
    if previous.testzip() is not None:
        raise ValueError('Previous update is corrupt.')
    manifest = json.loads(previous.read('files.json'))
    if manifest['version'] != 26:
        raise ValueError('Expected the offline 26 update.')
    names = set(previous.namelist())
    expected = {'CAP_NHAT.ps1', 'files.json'} | {'payload/' + row['path'] for row in manifest['files']}
    if names != expected:
        raise ValueError('Unexpected files in the previous update.')
    server_name = 'server/target/HSO_Re_2-1.0-jar-with-dependencies.jar'
    if 'payload/' + server_name not in names or 'payload/offline-version.txt' not in names:
        raise ValueError('Previous update is missing its server or version.')
    replacements = {
        'payload/' + server_name: args.server.read_bytes(),
        'payload/offline-version.txt': b'27',
    }
    new_manifest = dict(version=27, files=[])
    with ZipFile(args.out, 'x', ZIP_DEFLATED) as output:
        for row in manifest['files']:
            name = 'payload/' + row['path']
            data = replacements.get(name)
            if data is None:
                data = previous.read(name)
                if hashlib.sha256(data).hexdigest() != row['sha256']:
                    raise ValueError('Previous update failed a manifest hash: ' + name)
            new_manifest['files'].append(dict(path=row['path'], sha256=hashlib.sha256(data).hexdigest()))
            output.writestr(name, data)
        output.writestr('CAP_NHAT.ps1', previous.read('CAP_NHAT.ps1'))
        output.writestr('files.json', json.dumps(new_manifest, ensure_ascii=False, indent=2).encode())
with ZipFile(args.out) as result:
    if result.testzip() is not None:
        raise ValueError('New update failed ZIP integrity check.')
print(args.out.resolve())
