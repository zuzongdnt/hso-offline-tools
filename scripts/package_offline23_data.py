"""Package the overlay and a clean seed without personal accounts or characters."""
import json
import argparse
import sqlite3
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=root / 'build/offline23-package-final')
stage = parser.parse_args().out
stage.mkdir(exist_ok=True)
seed = stage / 'hso.sqlite'
if seed.exists():
    raise SystemExit('Choose a fresh package staging directory.')
source = root / 'build/android-offline22/decoded/assets/offline-world.zip'
with ZipFile(source) as archive:
    seed.write_bytes(archive.read('hso.sqlite'))
with sqlite3.connect(seed) as database:
    for table in ('account', 'clan', 'wedding', 'naptien'):
        database.execute('DELETE FROM ' + table)
    database.execute('DELETE FROM player WHERE id >= 0')
    database.commit()
    database.execute('VACUUM')
    assert database.execute('SELECT COUNT(*) FROM account').fetchone()[0] == 0
    assert database.execute('SELECT COUNT(*) FROM player WHERE id >= 0').fetchone()[0] == 0
with ZipFile(source) as original, ZipFile(stage / 'offline-world.zip', 'x', ZIP_DEFLATED) as output:
    for entry in original.infolist():
        output.writestr(entry, seed.read_bytes() if entry.filename == 'hso.sqlite' else original.read(entry))
with ZipFile(stage / 'offline-cosmetics.zip', 'x', ZIP_DEFLATED) as output:
    assets = root / 'build/offline23-assets'
    for path in sorted(assets.rglob('*')):
        if path.is_file():
            output.write(path, path.relative_to(assets))
print('Packaged clean seed and offline23 cosmetics')
