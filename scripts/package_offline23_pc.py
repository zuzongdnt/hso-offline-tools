"""Create a PC update containing application files and asset overlays only."""
import hashlib
import argparse
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--stage', type=Path, default=root / 'build/pc-offline23-update')
parser.add_argument('--version', type=int, default=23)
parser.add_argument('--client', type=Path, default=root / 'build/Assembly-CSharp.offline23-final.dll')
args = parser.parse_args()
stage = args.stage
stage.mkdir(exist_ok=True)
payload = stage / 'payload'
shutil.copytree(root / 'build/offline23-assets/data', payload / 'server/data', dirs_exist_ok=True)
for source, target in (
    ('build/server-offline23/target/HSO_Re_2-1.0-jar-with-dependencies.jar', 'server/target/HSO_Re_2-1.0-jar-with-dependencies.jar'),
    (args.client, 'client/hso_v403_Data/Managed/Assembly-CSharp.dll'),
    ('pc/CAP_NHAT_TU_DONG.ps1', 'CAP_NHAT_TU_DONG.ps1'),
    ('pc/DU_LIEU.ps1', 'DU_LIEU.ps1'),
):
    destination = payload / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix == '.ps1':
        destination.write_text((root / source).read_text(encoding='utf-8-sig'), encoding='utf-8-sig')
    else:
        shutil.copy2(root / source, destination)
(payload / 'offline-version.txt').write_text(str(args.version), encoding='utf-8')
files = []
for path in sorted(payload.rglob('*'), key=lambda path: (path.name == 'offline-version.txt', str(path))):
    if path.is_file():
        files.append(dict(path=path.relative_to(payload).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
assert all('database/' not in row['path'] and not row['path'].endswith(('.sqlite', '.conf')) for row in files)
(stage / 'files.json').write_text(json.dumps(dict(version=args.version, files=files), indent=2), encoding='utf-8')
(stage / 'CAP_NHAT.ps1').write_text((root / 'pc/CAP_NHAT.ps1').read_text(encoding='utf-8-sig'), encoding='utf-8-sig')
out = Path(f'E:/Codex/2026-11-04/tui-x20/outputs/HSO_Offline_PC_offline{args.version}_update.zip')
pending = out.with_name(out.name + '.building')
with ZipFile(pending, 'x', ZIP_DEFLATED) as archive:
    for path in sorted(stage.rglob('*')):
        if path.is_file():
            archive.write(path, path.relative_to(stage))
pending.replace(out)
print(out)
