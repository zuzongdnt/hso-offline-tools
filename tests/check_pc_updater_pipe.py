"""Regression: a hidden updater must finish without its parent draining pipes."""
import base64
from pathlib import Path
import subprocess
from uuid import uuid4
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1]
source = (root / 'pc/CAP_NHAT_TU_DONG.ps1').read_text(encoding='utf-8-sig')
assert "$ProgressPreference='SilentlyContinue'" in source
fixture = root / 'build' / ('pc-updater-pipe-' + uuid4().hex)
fixture.mkdir(parents=True)
archive = fixture / 'small.zip'
with ZipFile(archive, 'w') as output:
    for index in range(500):
        output.writestr(f'file-{index}.txt', 'fixture')
script = ("$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';"
          f"Expand-Archive -LiteralPath '{archive}' -DestinationPath '{fixture / 'unpacked'}'")
encoded = base64.b64encode(script.encode('utf-16le')).decode()
process = subprocess.Popen(
    ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encoded],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW,
)
try:
    process.wait(timeout=15)
except subprocess.TimeoutExpired:
    # Drain rather than kill a process that may still be writing files.
    process.communicate(timeout=30)
    raise AssertionError('Updater blocked before the parent drained its pipes')
stdout, stderr = process.communicate()
assert process.returncode == 0, stderr.decode(errors='replace')
assert len(list((fixture / 'unpacked').glob('*.txt'))) == 500
print('PC_UPDATER_PIPE_PASS extraction completes with unread output pipes')
