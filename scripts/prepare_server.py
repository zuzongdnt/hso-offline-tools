"""Apply the published patch to the pinned upstream checkout without modifying it."""
import argparse,json,shutil,subprocess
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--upstream',type=Path,required=True)
parser.add_argument('--out',type=Path,default=repo/'build/server')
args=parser.parse_args()
pin=json.loads((repo/'upstream.json').read_text(encoding='utf-8'))
commit=subprocess.check_output(['git','-C',str(args.upstream),'rev-parse','HEAD'],text=True).strip()
if commit!=pin['commit']:raise SystemExit('Checkout upstream commit '+pin['commit']+' first.')
if args.out.exists():raise SystemExit('Output already exists. Choose a new --out directory to preserve it.')
args.out.mkdir(parents=True)
shutil.copytree(args.upstream/'src',args.out/'src')
shutil.copy2(args.upstream/'pom.xml',args.out/'pom.xml')
for source in (args.out/'src').rglob('*.java'):
    source.write_text(source.read_text(encoding='utf-8-sig'),encoding='utf-8',newline='\n')
for name in ('server-offline.patch', 'server-offline-3.patch', 'server-offline-4.patch', 'server-offline-5.patch', 'server-offline-6.patch', 'server-offline-7.patch', 'server-offline-8.patch', 'server-offline-9.patch', 'server-offline-10.patch', 'server-offline-11.patch', 'server-offline-12.patch', 'server-offline-13.patch', 'server-offline-14.patch', 'server-offline-15.patch', 'server-offline-16.patch', 'server-offline-17.patch', 'server-offline-18.patch', 'server-offline-19.patch'):
    patch=str(repo/'patches'/name)
    subprocess.run(['git','-C',str(args.out),'apply',patch],check=True)
print('Prepared patched server source:',args.out.resolve())
