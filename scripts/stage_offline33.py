"""Stage the confusion effect over a prepared Offline 32 server."""
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


def edit(file, old, new):
    path = java / file
    source = path.read_text(encoding='utf-8')
    if source.count(old) != 1:
        raise ValueError(f'Unexpected source: {file}: {old[:65]}')
    path.write_text(source.replace(old, new), encoding='utf-8')


edit('core/OfflineTools.java', 'VERSION = 32;', 'VERSION = 33;')
edit('core/CombatVisuals.java', '    public static void restoreVisibility(', '''    public static final int CONFUSION_ANIMATION = 14;

    public static void confuse(Player target, int duration) throws IOException {
        target.add_eff(-205, 1, duration);
        if (target.get_eff(-205) != null) {
            send(target, CONFUSION_ANIMATION, 0, duration, target.invisibilityHidden);
        }
    }

    public static void moveConfused(Player target) throws IOException {
        template.EffTemplate confusion = target.get_eff(-205);
        if (confusion == null || target.isdie || target.hp <= 0 || target.map == null) return;

        // Keep both ends of the movement inside the current 24 px collision tile.
        int tileTop = Math.floorDiv(target.y, 24) * 24;
        int y = tileTop + ((++confusion.param & 1) == 0 ? 6 : 18);
        if (y == target.y) return;
        target.y = (short) y;

        Message position = new Message(4);
        position.writer().writeByte(0);
        position.writer().writeShort(0);
        position.writer().writeShort(target.id);
        position.writer().writeShort(target.x);
        position.writer().writeShort(target.y);
        position.writer().writeByte(-1);
        if (target.invisibilityHidden) target.conn.addmsg(position);
        else MapService.send_msg_player_inside(target.map, target, position, true);
        position.cleanup();
    }

    public static void restoreVisibility(''')

edit('map/MapService.java', 'if (map.ld != null && map.ld.isWaiting()) {\n            Message position',
     'if ((map.ld != null && map.ld.isWaiting()) || p.get_eff(-205) != null) {\n            Message position')
edit('map/MapService.java', '''        // lu loan: khong tan cong duoc
        if (dame > 0 && p0.get_eff(-205) != null) {
            dame = 0;
        }
''', '')
edit('map/MapService.java', '''            if (llParam > 0 && TinhTu.rolls(llParam)) {
                int dur = p.body.get_effect_duration(88, 3000);
                p0.add_eff(-205, 1, dur);
                p0.show_eff_p(24, dur);
            }''', '''            if (llParam > 0 && p0.get_eff(-205) == null && TinhTu.rolls(llParam)) {
                core.CombatVisuals.confuse(p0, p.body.get_effect_duration(88, 3000));
            }''')
edit('map/MapService.java', '''            if (llParam > 0 && TinhTu.rolls(llParam)) {
                core.CombatVisuals.mob(p,mob,24,p.body.get_effect_duration(88,3000));
            }''', '''            if (llParam > 0 && mob.confusedUntil <= System.currentTimeMillis() && TinhTu.rolls(llParam)) {
                core.CombatVisuals.mob(p, mob, core.CombatVisuals.CONFUSION_ANIMATION,
                        p.body.get_effect_duration(88, 3000));
            }''')
edit('map/Map.java', '                if (this.ld == null) core.CombatVisuals.restoreVisibility(p);', '''                if (this.ld == null) {
                    core.CombatVisuals.restoreVisibility(p);
                    core.CombatVisuals.moveConfused(p);
                }''')
edit('event_daily/LoiDai.java', '        if (state_ld == 1) moveOpponent(time);', '''        if (state_ld == 1) {
            core.CombatVisuals.moveConfused(p1);
            core.CombatVisuals.moveConfused(p2);
            moveOpponent(time);
        }''')
print(args.out.resolve())
