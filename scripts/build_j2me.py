"""Build an Android/J2ME Loader-specific offline MIDlet from privately supplied inputs."""
import argparse
import hashlib
import os
import re
import sqlite3
import subprocess
import zipfile
from pathlib import Path

repo = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([str(x) for x in args], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ['client', 'server', 'source', 'world', 'sdk', 'jdk', 'asm', 'out']:
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--cosmetics', type=Path)
    p.add_argument('--compact', action='store_true', help='Keep x1 artwork only. Requires offline31 or later.')
    p.add_argument('--version', type=int, help='Offline release number to record in the MIDlet manifest.')
    a = p.parse_args()
    if a.version is not None and a.version < 1:
        p.error('--version must be positive.')
    if a.out.exists():
        raise SystemExit('Output exists; use a new --out directory to preserve previous builds.')
    with zipfile.ZipFile(a.client) as z:
        assert 'com/silverknight/TemMidlet.class' in z.namelist(), 'Supply the original online v403 Java client, not another offline game.'
    original_hash = hashlib.sha256(a.client.read_bytes()).hexdigest()
    a.out.mkdir(parents=True)
    java, javac = [a.jdk / 'bin' / (x + '.exe') for x in ['java', 'javac']]
    android = a.sdk / 'platforms/android-36/android.jar'
    tools = sorted((a.sdk / 'build-tools').iterdir(), key=lambda x: tuple(map(int, re.findall(r'\d+', x.name))))[-1]
    classes = a.out / 'engine-classes'
    classes.mkdir()
    sources = list((repo / 'android/src').rglob('*.java')) + list((repo / 'java-j2me/engine').rglob('*.java'))
    for name in ['Util', 'Log']:
        text = (a.source / 'src/main/java/core' / (name + '.java')).read_text(encoding='utf-8')
        text = text.replace('new FileInputStream(url)', 'new FileInputStream(new java.io.File(System.getProperty("hso.root"),url))')
        text = text.replace('new File(path)', 'new File(System.getProperty("hso.root"),path)')
        text = re.sub(r'random\.nextInt\(a1,\s*a2\)', 'a1 + random.nextInt(a2 - a1)', text)
        text = re.sub(r'random\.nextInt\(0,\s*a2\)', 'random.nextInt(a2)', text)
        target = a.out / 'source/core' / (name + '.java')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        sources.append(target)
    run(javac, '--release', 17, '-encoding', 'UTF-8', '-cp', str(android) + os.pathsep + str(a.server), '-d', classes, *sources)
    replacements = {f.relative_to(classes).as_posix(): f for f in classes.rglob('*.class')}
    engine = a.out / 'engine.jar'
    with zipfile.ZipFile(a.server) as src, zipfile.ZipFile(engine, 'w', zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            if not name.endswith('.class') or name.startswith(('META-INF/', 'com/', 'net/')):
                continue
            if name.startswith('org/') and not name.startswith('org/json/simple/'):
                continue
            if name not in replacements:
                dst.writestr(name, src.read(name))
        for name, f in replacements.items():
            dst.write(f, name)
    dex = a.out / 'dex'
    dex.mkdir()
    run(java, '-cp', tools / 'lib/d8.jar', 'com.android.tools.r8.D8', '--min-api', 33, '--lib', android, '--output', dex, engine)
    assert len(list(dex.glob('*.dex'))) == 1, 'Engine must fit in one DEX.'
    bootstrap = a.out / 'bootstrap'
    bootstrap.mkdir()
    run(javac, '-source', 8, '-target', 8, '-encoding', 'UTF-8', '-cp', android, '-d', bootstrap,
        *list((repo / 'java-j2me/src').rglob('*.java')))
    patcher = a.out / 'patcher'
    patcher.mkdir()
    run(javac, '-cp', a.asm, '-d', patcher, repo / 'java-j2me/tools/PatchJ2me.java')
    output = a.out / 'HSO_Java_Offline_Zuzong.jar'
    version = f'{a.version}.0.0' if a.version is not None else '1.0.0'
    run(java, '-cp', str(patcher) + os.pathsep + str(a.asm), 'PatchJ2me', a.client, output, version)

    # Reject private saves rather than silently packaging an existing character or account.
    world = a.out / 'world.zip'
    with zipfile.ZipFile(a.world) as src:
        dbfile = a.out / 'world-check.sqlite'
        dbfile.write_bytes(src.read('hso.sqlite'))
        with sqlite3.connect(dbfile) as db:
            for table in ['account', 'clan', 'pet', 'giftcode', 'wedding', 'naptien']:
                assert db.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0] == 0, 'Use a world exported without private saves: ' + table
            assert db.execute('SELECT COUNT(*) FROM player WHERE id <> -1').fetchone()[0] == 0, 'World contains player saves.'
            assert db.execute('SELECT COUNT(*) FROM player WHERE id = -1').fetchone()[0] == 1, 'World needs the system boss template (player.id=-1); export again with the updated exporter.'
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        config = src.read('hso.conf').decode('utf-8-sig')
        for key, value in [('port', '19149'), ('mysql-user', 'offline'), ('mysql-host', '127.0.0.1'), ('mysql-database', 'offline'), ('mysql-password', 'offline')]:
            config = re.sub(r'(?m)^' + key + r':.*$', key + ': ' + value, config)
        def keep(name):
            return not a.compact or re.match(r'^data/(?:icon|part_char|part_char/imgver)/x[234]/', name) is None
        overlay = {}
        if a.cosmetics:
            with zipfile.ZipFile(a.cosmetics) as assets:
                for item in assets.infolist():
                    name = item.filename
                    if not name.startswith('data/') or '..' in Path(name).parts:
                        raise ValueError('Expected a data-only overlay')
                    if not item.is_dir() and keep(name):
                        overlay[name] = assets.read(item)
        if a.compact:
            overlay['data/j2me-x1'] = b'1'
        with zipfile.ZipFile(world, 'w', zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                if not keep(item.filename) or item.filename in overlay:
                    continue
                if item.filename == 'hso.conf':
                    dst.writestr(item.filename, config)
                else:
                    dst.writestr(item, src.read(item.filename))
            for name, data in overlay.items():
                dst.writestr(name, data)
    engine_bytes = (dex / 'classes.dex').read_bytes()
    world_hash = hashlib.sha256(world.read_bytes()).hexdigest()
    with zipfile.ZipFile(output, 'a') as dst:
        for f in bootstrap.rglob('*.class'):
            dst.write(f, f.relative_to(bootstrap).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
        dst.writestr('offline/engine.bin', engine_bytes, compress_type=zipfile.ZIP_DEFLATED)
        dst.writestr('offline/engine-id.txt', hashlib.sha256(engine_bytes).hexdigest())
        dst.writestr('offline/world-id.txt', world_hash)
        count = 0
        with world.open('rb') as stream:
            while chunk := stream.read(4 * 1024 * 1024):
                dst.writestr('offline/world-' + str(count) + '.bin', chunk, compress_type=zipfile.ZIP_STORED)
                count += 1
        dst.writestr('offline/world-count.txt', str(count))
    with zipfile.ZipFile(output) as check:
        assert check.testzip() is None
        assert check.read('offline/engine.bin').startswith(b'dex\n')
        count = int(check.read('offline/world-count.txt'))
        digest = hashlib.sha256()
        for i in range(count):
            digest.update(check.read('offline/world-' + str(i) + '.bin'))
        assert digest.hexdigest() == world_hash
    assert original_hash == hashlib.sha256(a.client.read_bytes()).hexdigest(), 'Original client changed!'
    (a.out / 'SHA256.txt').write_text(hashlib.sha256(output.read_bytes()).hexdigest() + '  ' + output.name + '\n', encoding='utf-8')
    print('Built:', output.resolve())
    print('Android 13+, J2ME Loader only; runtime verification still required.')


if __name__ == '__main__':
    main()
