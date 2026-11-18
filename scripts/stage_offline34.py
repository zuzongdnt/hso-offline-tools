"""Stage the maze event rooms and teleport stones over Offline 33."""
import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    parser.error('Choose an unused output directory.')
shutil.copytree(args.source / 'src', args.out / 'src')
shutil.copy2(args.source / 'pom.xml', args.out / 'pom.xml')
java = args.out / 'src/main/java'
patch = Path(__file__).resolve().parents[1] / 'patches/offline34'
shutil.copy2(patch / 'core/MazeRun.java', java / 'core/MazeRun.java')


def edit(file, old, new):
    path = java / file
    source = path.read_text(encoding='utf-8')
    if source.count(old) != 1:
        raise ValueError(f'Unexpected source: {file}: {old[:65]}')
    path.write_text(source.replace(old, new), encoding='utf-8')


edit('core/OfflineTools.java', 'VERSION = 33;', 'VERSION = 34;')
edit('map/Map.java', '        // mob mo tai nguyen\n', '''        if (p.maze != null) p.maze.sendStone();
        // mob mo tai nguyen
''')
edit('core/MenuController.java', '        byte idnpc = m.reader().readByte();\n', '''        byte idnpc = m.reader().readByte();
        if (idnpc == MazeRun.STONE_NPC && conn.p.maze != null) {
            conn.p.maze.openStone();
            return;
        }
''')
edit('core/MenuController.java', '''        if (idnpc == 12005) { if(conn.p.maze!=null){if(index==0)conn.p.maze.claim();else conn.p.maze.leave("Đã rời mê cung.");}return; }''', '''        if (idnpc == MazeRun.STONE_MENU) {
            if (conn.p.maze != null) conn.p.maze.useStone(index);
            return;
        }''')
print(args.out.resolve())
