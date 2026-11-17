"""Compile the embedded server and rebuild a privately supplied game APK."""
import argparse,os,re,shutil,subprocess,zipfile
from pathlib import Path
from patch_android_client import MIN_SDK,patch

repo=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for name in ['apk','server','source','world','apktool','sdk','jdk','keystore']:
    p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--cosmetics',type=Path)
p.add_argument('--client-base',type=Path,help='Reuse a previously patched client when its world/cosmetic assets match.')
p.add_argument('--alias',default='offline')
p.add_argument('--out',type=Path,default=repo/'build/android')
a=p.parse_args()
password=os.environ.get('HSO_KEYSTORE_PASSWORD')
if not password:raise SystemExit('Set HSO_KEYSTORE_PASSWORD locally; do not commit signing keys or passwords.')
if a.out.exists():raise SystemExit('Choose an unused --out directory.')
a.out.mkdir(parents=True)
def run(*args):subprocess.run([str(x) for x in args],check=True)
java=a.jdk/'bin/java.exe';javac=a.jdk/'bin/javac.exe'
buildtools=sorted((a.sdk/'build-tools').iterdir(),key=lambda x:tuple(map(int,re.findall(r'\d+',x.name))))[-1]
android=a.sdk/'platforms/android-36/android.jar'
if not android.is_file():raise SystemExit('Install Android SDK Platform 36.')
decoded=a.out/'decoded'
base=a.out/'client-base.apk'
if a.client_base:
    import hashlib
    with zipfile.ZipFile(a.client_base) as previous:
        for name,path in [('offline-world.zip',a.world),('offline-cosmetics.zip',a.cosmetics)]:
            if path and hashlib.sha256(previous.read('assets/'+name)).digest()!=hashlib.sha256(path.read_bytes()).digest():
                raise ValueError('Reused client has different '+name)
    shutil.copy2(a.client_base,base)
else:
    run(java,'-jar',a.apktool,'d','-f',a.apk,'-o',decoded)
    patch(decoded)
    shutil.copy2(a.world,decoded/'assets/offline-world.zip')
    if a.cosmetics: shutil.copy2(a.cosmetics,decoded/'assets/offline-cosmetics.zip')
    run(java,'-jar',a.apktool,'b','-f',decoded,'-o',base)
sources=list((repo/'android/src').rglob('*.java'))
for name in ['Util','Log']:
    text=(a.source/'src/main/java/core'/f'{name}.java').read_text(encoding='utf-8')
    text=text.replace('new FileInputStream(url)','new FileInputStream(new java.io.File(System.getProperty("hso.root"),url))')
    text=text.replace('new File(path)','new File(System.getProperty("hso.root"),path)')
    text=re.sub(r'random\.nextInt\(a1,\s*a2\)','a1 + random.nextInt(a2 - a1)',text)
    text=re.sub(r'random\.nextInt\(0,\s*a2\)','random.nextInt(a2)',text)
    target=a.out/'source/core'/f'{name}.java';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(text,encoding='utf-8');sources.append(target)
classes=a.out/'classes';classes.mkdir()
run(javac,'--release','17','-encoding','UTF-8','-cp',str(android)+os.pathsep+str(a.server),'-d',classes,*sources)
replacements={x.relative_to(classes).as_posix():x for x in classes.rglob('*.class')}
engine=a.out/'engine.jar'
with zipfile.ZipFile(a.server) as src,zipfile.ZipFile(engine,'w',zipfile.ZIP_DEFLATED) as dst:
    for name in src.namelist():
        if not name.endswith('.class') or name.startswith(('META-INF/','com/','net/')):continue
        if name.startswith('org/') and not name.startswith('org/json/simple/'):continue
        if name not in replacements:dst.writestr(name,src.read(name))
    for name,path in replacements.items():dst.write(path,name)
dex=a.out/'dex';dex.mkdir()
run(java,'-cp',buildtools/'lib/d8.jar','com.android.tools.r8.D8','--min-api',MIN_SDK,'--lib',android,'--output',dex,engine)
unsigned=a.out/'unsigned.apk'
with zipfile.ZipFile(base) as src,zipfile.ZipFile(unsigned,'w',zipfile.ZIP_DEFLATED) as dst:
    indices=[1 if name=='classes.dex' else int(re.fullmatch(r'classes(\d+)\.dex',name)[1]) for name in src.namelist() if re.fullmatch(r'classes\d*\.dex',name)]
    for item in src.infolist():
        if not item.filename.startswith('META-INF/'):dst.writestr(item,src.read(item.filename))
    number=max(indices)+1
    for file in sorted(dex.glob('*.dex')):dst.write(file,'classes'+str(number)+'.dex');number+=1
aligned=a.out/'aligned.apk';output=a.out/'HSO_Offline.apk'
run(buildtools/'zipalign.exe','-f','-P','16','4',unsigned,aligned)
run(java,'-jar',buildtools/'lib/apksigner.jar','sign','--ks',a.keystore,'--ks-key-alias',a.alias,
    '--ks-pass','env:HSO_KEYSTORE_PASSWORD','--key-pass','env:HSO_KEYSTORE_PASSWORD','--out',output,aligned)
run(java,'-jar',buildtools/'lib/apksigner.jar','verify','--verbose',output)
with zipfile.ZipFile(output) as archive:assert archive.testzip() is None
print('Built:',output.resolve())
