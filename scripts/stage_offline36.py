"""Stage the verified combat visuals and arena movement over Offline 35."""
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
patch = Path(__file__).resolve().parents[1] / 'patches/offline36'
shutil.copy2(patch / 'core/CombatMotion.java', java / 'core/CombatMotion.java')


def edit(file, old, new='', count=1):
    path = java / file
    source = path.read_text(encoding='utf-8')
    if source.count(old) != count:
        raise ValueError(f'Unexpected source: {file}: {old[:78]}')
    path.write_text(source.replace(old, new), encoding='utf-8')


edit('core/OfflineTools.java', 'VERSION = 35;', 'VERSION = 36;')
edit('client/Player.java', '    public boolean invisibilityHidden;', '''    public boolean invisibilityHidden;
    public long knockbackUntil;''')

visuals = 'core/CombatVisuals.java'
edit(visuals, '        mob.confusedUntil=System.currentTimeMillis()+time;\n', '')
edit(visuals, '''        if(effect==17 && player.get_eff(-204)!=null){invisible(player,time);return;}
        send(player,effect,0,time,false);''', '''        send(player, effect, 0, time, player.invisibilityHidden);''')
edit(visuals, '    private static void invisible(Player player,int time)throws IOException {',
     '    public static void hide(Player player,int time)throws IOException {')
source = (java / visuals).read_text(encoding='utf-8')
start = source.index('    public static void moveConfused(')
end = source.index('    public static void restoreVisibility(', start)
edit(visuals, source[start:end], '''    public static void lockCountdown(Player player, int millis) throws IOException {
        // Native lock flag with the stock empty skill effect.
        send(player, 16, 1, millis, true);
    }

''')
edit('map/Map.java', '''                if (this.ld == null) {
                    core.CombatVisuals.restoreVisibility(p);
                    core.CombatVisuals.moveConfused(p);
                }''', '                if (this.ld == null) core.CombatVisuals.restoreVisibility(p);')

gems = 'core/SocketGems.java'
edit(gems, 'p.add_eff(-210,200,3000);CombatVisuals.show(p,20,3000);',
     'p.add_eff(-210,200,3000);CombatVisuals.show(p,18,3000);')
edit(gems, 'CombatVisuals.show(p,45,3000);', 'CombatVisuals.show(p,22,3000);')
edit(gems, 'visual(p,30,3000);', 'visual(p,20,3000);')
edit(gems, 'p.add_eff(-212,values[5],duration);visual(p,27,duration);', 'p.add_eff(-212,values[5],duration);')
edit(gems, 'p.add_eff(-215,20,3000);visual(p,32,3000);', 'p.add_eff(-215,20,3000);')
edit(gems, 'if(TinhTu.rolls(values[8])){damage*=2;visual(p,18,800);}', 'if(TinhTu.rolls(values[8])) damage*=2;')

combat = 'map/MapService.java'
source = (java / combat).read_text(encoding='utf-8')
start = source.index('        if ((map.ld != null && map.ld.isWaiting())')
end = source.index('        \n\t\tSession conn', start)
edit(combat, source[start:end], '''        if ((map.ld != null && map.ld.isWaiting()) || p.get_eff(-122) != null) {
            core.CombatMotion.position(p, true, false);
            return;
        }
        if (p.knockbackUntil > System.currentTimeMillis()) return;
        if (p.get_eff(-205) != null) {
            core.CombatMotion.reverse(p, x_new, y_new);
            return;
        }
''')
edit(combat, '                p0.conn.addmsg(m);\n                if (p.other_player_inside.get(p0.id)) {', '''                if (!p.invisibilityHidden) p0.conn.addmsg(m);
                if (p0.invisibilityHidden) continue;
                if (p.other_player_inside.get(p0.id)) {''')
edit(combat, 'Map.is_map__load_board_player(map.map_id)', '(map.ld != null || Map.is_map__load_board_player(map.map_id))', count=4)
edit(combat, 'p.show_eff_p(17, dur);', 'core.CombatVisuals.hide(p, dur);', count=2)
edit(combat, '        if (!conn.p.is_atk || map.ld != null && map.ld.isWaiting()) {',
     '        if (!conn.p.is_atk || conn.p.get_eff(-205) != null || conn.p.get_eff(-122) != null\n                || map.ld != null && map.ld.isWaiting()) {')
edit(combat, '    public static void buff_skill(Map map, Session conn, Message m2) throws IOException {', '''    public static void buff_skill(Map map, Session conn, Message m2) throws IOException {
        if (conn.p.get_eff(-205) != null || conn.p.get_eff(-122) != null || map.ld != null && map.ld.isWaiting()) return;''')
edit(combat, '            if (mob.is_boss && (percent_stun > Util.random(0, 100))) {',
     '            if (!p_target.isdie && mob.is_boss && percent_stun > Util.random(0, 100)) {')
edit(combat, '                    MapService.add_eff_stun(map, p_target, null, time_stun, list[Util.random(0, list.length)], mob.index);', '''                    int type = map.map_id == 7 && mob.template.mob_id == 103 ? 5 : list[Util.random(0, list.length)];
                    MapService.add_eff_stun(map, p_target, null, time_stun, type, mob.index);''')
edit(combat, '                p0.show_eff_p(1, 1000);', '                p0.show_eff_p(13, dur);')
edit(combat, '                p0.show_eff_p(2, 1000);', '                p0.show_eff_p(12, dur);')
edit(combat, '                p.show_eff_p(1, 1000);', '                core.CombatVisuals.mob(p, mob, 13, p.body.get_effect_duration(77, 5000));')
edit(combat, '                p.show_eff_p(2, 1000);', '                core.CombatVisuals.mob(p, mob, 12, p.body.get_effect_duration(79, 5000));')
edit(combat, '                core.CombatVisuals.mob(p, mob, core.CombatVisuals.CONFUSION_ANIMATION,\n                        p.body.get_effect_duration(88, 3000));', '''                int duration = p.body.get_effect_duration(88, 3000);
                mob.confusedUntil = System.currentTimeMillis() + duration;
                core.CombatVisuals.mob(p, mob, core.CombatVisuals.CONFUSION_ANIMATION, duration);''')
edit(combat, '                    p0.show_eff_p(6, 1000);', '                    p0.show_eff_p(15, dur);')
edit(combat, '                    p0.show_eff_p(7, 1000);', '                    p0.show_eff_p(19, 5000);')
for old, count in [('p0.show_eff_p(18, 1000);', 2), ('p0.show_eff_p(14, 1000);', 2),
                   ('p_target.show_eff_p(14, 1000);', 2), ('p_target.show_eff_p(15, 1000);', 1),
                   ('p0.show_eff_p(15, 1000);', 1), ('p0.show_eff_p(19, 1000);', 1),
                   ('p0.show_eff_p(20, 1000);', 1), ('p0.show_eff_p(22, 1000);', 1), ('p.show_eff_p(27, 1000);', 2)]:
    path = java / combat
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    matches = sum(line.strip() == old for line in lines)
    if matches != count:
        raise ValueError(f'Expected {count} lines for {old}, found {matches}')
    path.write_text(''.join(line for line in lines if line.strip() != old), encoding='utf-8')
edit(combat, '''            // mu mat: 140 / -116
            int mmParam = get_combat_effect_param(p, -233, -116);
            if (mmParam > 0 && TinhTu.rolls(mmParam)) {
                // visual effect on attacker/target
                p.show_eff_p(18, 1000);
            }
''')
edit(combat, '''        // affect_special_skill
        if (affect_special_skill) {''', '''        if (dame > 0 && !p0.isdie) {
            if (TinhTu.rolls(p.body.get_equipment_effect(160))) p0.show_eff_p(42, 1000);
            if (map.ld != null && indexskill == 17 && p.clazz == 0) core.CombatMotion.push(p, p0);
        }
        // affect_special_skill
        if (affect_special_skill && dame > 0 && !p0.isdie) {''')
edit('map/Map.java', '                                        p2.hp -= burn_dame;', '''                                        p2.hp -= burn_dame;
                                        p2.show_eff_p(17, 3000);''')
edit('map/Eff_special_skill.java', 'm.writer().writeByte(9);', 'm.writer().writeByte(23);')

arena = 'event_daily/LoiDai.java'
edit(arena, '        start(player,bot);\n        if(player.map.ld==null)return;',
     '        if (!startMatch(player, bot, 36, target)) return;')
edit(arena, '        LoiDai match=player.map.ld;match.challengeRank=target;match.challengeDeadline=System.currentTimeMillis()+300000;',
     '        LoiDai match = player.map.ld;')
edit(arena, '''    public static void start(Player player, Player selectedBot) throws IOException {
        if (player.map.ld != null || player.isdie) {''', '''    public static void start(Player player, Player selectedBot) throws IOException {
        startMatch(player, selectedBot, 102, 0);
    }

    private static boolean startMatch(Player player, Player selectedBot, int mapId, int rank) throws IOException {
        if (player.map.ld != null || player.isdie) {''')
source = (java / arena).read_text(encoding='utf-8')
start = source.index('    private static boolean startMatch(')
end = source.index('    public static Player createOpponent', start)
match = source[start:end]
edit(arena, match, match.replace('return;', 'return false;').replace('Map.get_map_by_id(102)', 'Map.get_map_by_id(mapId)')
     .replace('new Map(102, 0, template.npc_name_data', 'new Map(mapId, 0, new String[0]')
     .replace('        arena.mobs', '''        match.challengeRank = rank;
        if (rank > 0) match.challengeDeadline = System.currentTimeMillis() + 300_000;
        match.placeFighter(bot);
        arena.mobs''')
     .replace('        player.x = 288;\n        player.y = 228;', '        match.placeFighter(player);')
     .replace('        arena.start_map();', '        arena.start_map();\n        return true;'))
edit(arena, '    public synchronized void ready() {', '''    private void placeFighter(Player player) {
        player.x = (short) ((map.map_id == 36 ? 456 : 288) + (player == p1 ? 0 : 120));
        player.y = (short) (map.map_id == 36 ? 360 : 228);
        player.knockbackUntil = 0;
    }

    public synchronized void ready() throws IOException {''')
edit(arena, '            ready = true;', '            ready = true;\n            core.CombatVisuals.lockCountdown(p1, WAIT_SECONDS * 1000);')
edit(arena, '((deadline - System.nanoTime()) * speed + 999_999_999)', '((deadline - System.nanoTime()) * (state_ld == 0 ? 1 : speed) + 999_999_999)')
edit(arena, '        deadline = now + Math.max(0, deadline - now) * speed / p1.offlineSpeed;', '        if (state_ld != 0) deadline = now + Math.max(0, deadline - now) * speed / p1.offlineSpeed;')
edit(arena, 'seconds * 1_000_000_000L / speed', 'seconds * 1_000_000_000L / (state_ld == 0 ? 1 : speed)')
edit(arena, '''        if (state_ld == 1) {
            core.CombatVisuals.moveConfused(p1);
            core.CombatVisuals.moveConfused(p2);
            moveOpponent(time);
        }''', '        if (state_ld == 1) moveOpponent(time);')
edit(arena, '            if (state_ld == 0) MapService.send_in4_other_char(map, p1, p2);', '''            if (state_ld == 0) {
                MapService.send_in4_other_char(map, p1, p2);
                core.CombatVisuals.lockCountdown(p1, Math.max(1, (int) ((deadline - System.nanoTime()) / 1_000_000)));
            }''')
edit(arena, '''        if (p2.isdie || p2.get_eff(-205) != null) return;
        int targetX = Math.max(216, Math.min(450, p1.x + (time % 8 < 4 ? 48 : -48)));
        int targetY = Math.max(180, Math.min(300, p1.y + (time % 6 < 3 ? 24 : -24)));
        p2.x += Math.max(-18, Math.min(18, targetX-p2.x));
        p2.y += Math.max(-12, Math.min(12, targetY-p2.y));
        Message position = new Message(4);
        position.writer().writeByte(0); position.writer().writeShort(0);
        position.writer().writeShort(p2.id); position.writer().writeShort(p2.x); position.writer().writeShort(p2.y);
        position.writer().writeByte(-1); p1.conn.addmsg(position);''', '''        if (p2.isdie || p2.get_eff(-205) != null || p2.get_eff(-122) != null
                || p2.knockbackUntil > System.currentTimeMillis() || p1.invisibilityHidden) return;
        int targetX = p1.x + (time % 8 < 4 ? 48 : -48);
        int targetY = p1.y + (time % 6 < 3 ? 24 : -24);
        int x = p2.x + Math.max(-18, Math.min(18, targetX - p2.x));
        int y = p2.y + Math.max(-12, Math.min(12, targetY - p2.y));
        if (core.CombatMotion.walkable(map, x, p2.y)) p2.x = (short) x;
        if (core.CombatMotion.walkable(map, p2.x, y)) p2.y = (short) y;
        core.CombatMotion.position(p2, false, false);''')
edit(arena, '''            fighter.x = fighter == p1 ? (short) 288 : (short) 408;
            fighter.y = 228;''', '            placeFighter(fighter);')
print(args.out.resolve())
