"""Build offline23 with the existing local signing key. Never print its password."""
import os
import argparse
import re
import subprocess
import sys
from pathlib import Path

base = Path('E:/Codex/2026-11-04/tui-x20/work/hso403')
settings = (base / 'offline-independent/build_android_binary.ps1').read_text(encoding='utf-8-sig')
match = re.search(r'--ks-pass\s+["\']?pass:([^\s"\']+)', settings)
assert match, 'Local signing configuration is missing'
parser = argparse.ArgumentParser()
parser.add_argument('--out', default='build/android-offline23-final')
parser.add_argument('--data', type=Path, default=Path('build/offline23-package-final'))
args = parser.parse_args()
subprocess.run([sys.executable, 'scripts/build_android.py',
    '--apk', str(base / 'android403/original.apk'),
    '--server', 'build/server-offline23/target/HSO_Re_2-1.0-jar-with-dependencies.jar',
    '--source', 'build/server-offline23',
    '--world', str(args.data / 'offline-world.zip'),
    '--cosmetics', str(args.data / 'offline-cosmetics.zip'),
    '--apktool', 'E:/Codex/2026-11-04/tui-x20/work/tools/apktool_3.0.3.jar',
    '--sdk', 'D:/Android/Sdk', '--jdk', 'C:/Program Files/Android/Android Studio/jbr',
    '--keystore', str(base / 'android403/zuzong-android.jks'), '--alias', 'zuzong',
    '--out', args.out],
    env={**os.environ, 'HSO_KEYSTORE_PASSWORD': match.group(1)}, check=True)
