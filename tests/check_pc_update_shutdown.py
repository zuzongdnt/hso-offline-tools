"""The prior launcher must finish shutting down before the updated game restarts."""
from pathlib import Path
from uuid import uuid4
import hashlib
import json
import shutil
import subprocess

repo=Path(__file__).resolve().parents[1]
root=repo/'build'/('pc-update-shutdown-'+uuid4().hex)
game=root/'game';package=root/'package';(package/'payload').mkdir(parents=True)
for name in ['client','runtime','database']:(game/name).mkdir(parents=True,exist_ok=True)
(game/'BAT_DAU.ps1').write_text('# fixture',encoding='utf-8-sig')
(game/'database/character.txt').write_text('preserved character',encoding='utf-8')
(game/'CHOI_OFFLINE.ps1').write_text("Start-Sleep -Seconds 2\nSet-Content -LiteralPath (Join-Path $PSScriptRoot 'launcher-exited.txt') -Value done",encoding='utf-8-sig')
(game/'TAT_SERVER.ps1').write_text("if(-not(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'launcher-exited.txt'))){throw 'Old launcher has not finished'}",encoding='utf-8-sig')
payload=b'29';(package/'payload/offline-version.txt').write_bytes(payload)
(package/'files.json').write_text(json.dumps({'version':29,'files':[{'path':'offline-version.txt','sha256':hashlib.sha256(payload).hexdigest()}]}))
shutil.copy2(repo/'pc/CAP_NHAT.ps1',package/'CAP_NHAT.ps1')
launcher=subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(game/'CHOI_OFFLINE.ps1')],creationflags=subprocess.CREATE_NO_WINDOW)
result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(package/'CAP_NHAT.ps1'),'-GameRoot',str(game)],capture_output=True,timeout=35)
launcher.wait(timeout=5)
assert result.returncode==0,result.stderr.decode(errors='replace')
assert (game/'offline-version.txt').read_bytes()==payload
assert (game/'database/character.txt').read_text()=='preserved character'
assert len(list((game/'backups').glob('offline29-*/database/character.txt')))==1
print('PC_UPDATE_SHUTDOWN_PASS prior launcher exits before installation; database backup preserved')
