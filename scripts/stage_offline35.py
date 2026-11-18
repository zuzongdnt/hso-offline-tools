"""Restore movement through maze doors and remove the event's teleport stones."""
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


def edit(file, old, new=''):
    path = java / file
    source = path.read_text(encoding='utf-8')
    if source.count(old) != 1:
        raise ValueError(f'Unexpected source: {file}: {old[:65]}')
    path.write_text(source.replace(old, new), encoding='utf-8')


edit('core/OfflineTools.java', 'VERSION = 34;', 'VERSION = 35;')
edit('map/Map.java', '        if (p.maze != null) p.maze.sendStone();\n')
edit('core/MenuController.java', '''        if (idnpc == MazeRun.STONE_NPC && conn.p.maze != null) {
            conn.p.maze.openStone();
            return;
        }
''')
edit('core/MenuController.java', '''        if (idnpc == MazeRun.STONE_MENU) {
            if (conn.p.maze != null) conn.p.maze.useStone(index);
            return;
        }''', '''        if (idnpc == MazeRun.TREASURE_MENU) {
            MazeRun run = conn.p.maze;
            if (run != null && index == 0) run.claim();
            if (run != null && index == 1) run.leave("Đã rời mê cung.");
            return;
        }''')

maze = 'core/MazeRun.java'
edit(maze, 'import template.NpcTemplate;\n')
edit(maze, '''    public static final byte STONE_NPC = -55;
    public static final short STONE_MENU = 12005;''', '    public static final short TREASURE_MENU = 12005;')
edit(maze, '''        player.x=entry.x_new;player.y=entry.y_new;player.is_changemap=false;
        MapService.enter(player.map,player);player.map.start_map();timer();''', '''        player.x_old = player.x = entry.x_new;
        player.y_old = player.y = entry.y_new;
        player.is_changemap = false;
        MapService.enter(player.map,player);player.map.start_map();timer();
        if (room == TREASURE_ROOM) menu(player);''')
source = (java / maze).read_text(encoding='utf-8')
start = source.index('    public void sendStone()')
end = source.index('    public synchronized void claim()', start)
edit(maze, source[start:end], '''    public static void menu(Player p) throws IOException {
        MazeRun run = p.maze;
        if (run == null) {
            Service.send_notice_box(p.conn, "Dùng Vé vào mê cung trong hành trang để tham gia.");
        } else if (run.room == TREASURE_ROOM) {
            MenuController.send_menu_select(p.conn, TREASURE_MENU, new String[]{"Nhặt Đèn Thần", "Rời mê cung"});
        } else {
            Service.send_notice_box(p.conn, "Đi qua lối ở mép phòng để tìm Đèn Thần.");
        }
    }
''')
print(args.out.resolve())
