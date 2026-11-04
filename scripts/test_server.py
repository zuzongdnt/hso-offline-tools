import argparse,subprocess
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for name in ['jdk','jar','fixtures','runtime']:p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--out',type=Path,default=repo/'build/tests')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
subprocess.run([str(a.jdk/'bin/javac.exe'),'--release','17','-encoding','UTF-8',
    '-cp',str(a.jar),'-d',str(a.out),*[str(x) for x in (repo/'tests').glob('*.java')]],check=True)
result=subprocess.run([str(a.jdk/'bin/java.exe'),'-cp',str(a.out)+';'+str(a.jar),
    'OfflineFixCheck',str(a.fixtures)],cwd=a.runtime,capture_output=True,text=True,encoding='utf-8')
print(result.stdout)
if result.returncode or 'all 14 egg IDs deposit and round-trip' not in result.stdout:
    print(result.stderr);raise SystemExit('Regression checks did not complete.')
