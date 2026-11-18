"""Stage combat expiry and offline battlefield actors from a prepared offline30 server."""
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
shared = Path(__file__).resolve().parents[1] / 'shared/src'
shutil.copy2(shared / 'ai/BattlefieldWalk.java', java / 'ai/BattlefieldWalk.java')


def edit(file, previous, replacement):
    path = java / file
    source = path.read_text(encoding='utf-8')
    if source.count(previous) != 1:
        raise ValueError(f'Unexpected source: {file}: {previous[:65]}')
    path.write_text(source.replace(previous, replacement), encoding='utf-8')


edit('core/OfflineTools.java', 'VERSION = 30;', 'VERSION = 31;')
edit('core/Manager.java', '            data_part_char_x2[i] =', '''            if (Boolean.getBoolean("hso.assets.x1")) continue;
            data_part_char_x2[i] =''')
edit('io/Session.java', 'if (this.zoomlv < 1 || this.zoomlv > 4)', 'if (this.zoomlv < 1 || this.zoomlv > 4 || Boolean.getBoolean("hso.assets.x1"))')
edit('core/Service.java', '        m.writer().writeShort(p.maxbag); // max bag', '''        // Java v403 reads a signed byte and displays 42 slots per page.
        if (Boolean.getBoolean("hso.client.j2me")) m.writer().writeByte(Math.min(p.maxbag, 126));
        else m.writer().writeShort(p.maxbag);''')
edit('client/Item.java', '        return (p.maxbag - (total_item_by_type(3) + total_item_by_type(4) + total_item_by_type(7)));', '''        int capacity = Boolean.getBoolean("hso.client.j2me") ? Math.min(p.maxbag, 126) : p.maxbag;
        return capacity - (total_item_by_type(3) + total_item_by_type(4) + total_item_by_type(7));''')
edit('client/Player.java', '    public EffTemplate get_eff(int id) {', '''    public boolean invisibilityHidden;

    public EffTemplate get_eff(int id) {''')
edit('client/Player.java', '''        for (int i = 0; i < list_eff.size(); i++) {
            EffTemplate temp = list_eff.get(i);
            if (temp.id == id) {
                return temp;
            }
        }
        return null;''', '''        long now = System.currentTimeMillis();
        synchronized (list_eff) {
            for (EffTemplate effect : list_eff) {
                if (effect.id == id && effect.time > now) return effect;
            }
        }
        return null;''')
edit('client/Player.java', '''            EffTemplate temp_test = get_eff(id);
            while (temp_test != null) {
                list_eff.remove(temp_test);
                temp_test = get_eff(id);
            }''', '''            list_eff.removeIf(effect -> effect.id == id);''')
edit('core/CombatVisuals.java', '''        Message remove=new Message(8);remove.writer().writeShort(player.id);''', '''        player.invisibilityHidden = true;
        Message remove=new Message(8);remove.writer().writeShort(player.id);''')
edit('core/CombatVisuals.java', '''    private static void invisible(''', '''    public static void restoreVisibility(Player player) throws IOException {
        if (!player.invisibilityHidden || player.get_eff(-204) != null || player.map == null) return;
        MapService.update_in4_2_other_inside(player.map, player);
        player.invisibilityHidden = false;
    }

    private static void invisible(''')
edit('map/Map.java', '                if (this.ld != null && p.is_nhanban) continue;', '''                if (this.ld == null) core.CombatVisuals.restoreVisibility(p);
                if (this.ld != null && p.is_nhanban) continue;''')
edit('event_daily/LoiDai.java', '        if(challengeRank>0&&!finished', '''        core.CombatVisuals.restoreVisibility(p1);
        core.CombatVisuals.restoreVisibility(p2);
        if(challengeRank>0&&!finished''')
edit('event_daily/LoiDai.java', '        if (p2.isdie) return;', '        if (p2.isdie || p2.get_eff(-205) != null) return;')
edit('event_daily/LoiDai.java', '        int start = Util.random(SKILLS.length);', '''        if (p1.get_eff(-204) != null || p2.get_eff(-205) != null) return;
        int start = Util.random(SKILLS.length);''')
edit('event_daily/LoiDai.java', '            fighter.isdie = false;', '''            synchronized (fighter.list_eff) {
                fighter.list_eff.removeIf(effect -> effect.id <= -200 || core.SocketGems.DEBUFFS.contains(effect.id));
            }
            fighter.isdie = false;
            fighter.is_atk = true;
            core.CombatVisuals.restoreVisibility(fighter);''')
edit('map/MapService.java', '|| p.hieuchien > 320_000', '|| (map.ld == null && p.hieuchien > 320_000)')

# The old guard packet wrote one byte per fashion part. Current clients read shorts.
edit('event_daily/ChienTruong.java', 'if (temp.id == ((short) id)) {', 'if (temp.id == ((short) id) && temp.map == p.map && !temp.isdie && status == 2) {')
edit('event_daily/ChienTruong.java', 'm.writer().writeUTF("Lính canh");', 'm.writer().writeUTF(temp.name);')
edit('event_daily/ChienTruong.java', 'm.writer().writeByte(0); // type\n', 'm.writer().writeByte(temp.flag()); // faction\n')
edit('event_daily/ChienTruong.java', '''for (int i1 = 0; i1 < 7; i1++) {
					m.writer().writeByte(-1);''', '''for (int i1 = 0; i1 < 7; i1++) {
					m.writer().writeShort(-1);''')
edit('event_daily/ChienTruong.java', 'm.writer().writeShort(-1); // body', '''m.writer().writeShort(-1); // name effect
				m.writer().writeShort(-1); // body''')
edit('event_daily/ChienTruong.java', '''			for (Player_Nhan_Ban temp : this.list_ai) {
				temp.isdie = false;
				temp.hp = temp.hp_max;
			}''', '''			Player_Nhan_Ban.beginBattle(this.list_ai);''')
edit('map/Map.java', 'long period = this.ld == null ? 1000L : LoiDai.UPDATE_MILLIS;', '''boolean activeBattle = !players.isEmpty() && Map.is_map_chien_truong(map_id) && ChienTruong.gI().getStatus() == 2;
                    long period = this.ld != null || activeBattle ? LoiDai.UPDATE_MILLIS : 1000L;''')
edit('map/Map.java', 'Player_Nhan_Ban.update(this);', 'if (!players.isEmpty()) Player_Nhan_Ban.update(this);')
edit('map/MapService.java', 'temp.target = p.id;', 'if (temp.flag() != p.typepk) temp.target = p.id;')
edit('ai/Player_Nhan_Ban.java', 'public int id;', '''public int id;
    public String name = "Lính canh";
    public boolean roaming;
    private final java.util.Set<Integer> viewers = new java.util.HashSet<>();
    private java.util.ArrayDeque<Integer> route = new java.util.ArrayDeque<>();
    private long nextRoute;
    private long nextHit;
    private int homeCell = -1;

    public int flag() {
        return switch (village) { case 2 -> 2; case 3 -> 1; case 4 -> 4; default -> 5; };
    }

    public static void beginBattle(List<Player_Nhan_Ban> actors) throws IOException {
        actors.removeIf(actor -> actor.roaming);
        Map center = Map.get_map_by_id(61)[0];
        int id = actors.stream().mapToInt(actor -> actor.id).min().orElse(-2) - 1;
        for (int i = 0; i < 8; i++) {
            add_linh_canh(actors, id--, 61, 0, 2 + i / 2);
            Player_Nhan_Ban fighter = actors.get(actors.size() - 1);
            fighter.roaming = true;
            fighter.name = new String[]{"Phong", "Vũ", "Hỏa", "Dương", "Lôi", "Vân", "Quang", "Nguyệt"}[i] + " [Bot]";
            fighter.hp_max = 160_000;
            fighter.dame = 2200;
            int homeId = new int[]{56, 60, 58, 54}[i / 2];
            var gate = center.vgos.stream().filter(door -> door.id_map_go == homeId).findFirst().orElseThrow();
            fighter.x = (short) (gate.x_old + (i % 2 == 0 ? 48 : -48));
            fighter.y = (short) (gate.y_old + (gate.y_old < 150 ? 96 : -96));
        }
        for (Player_Nhan_Ban actor : actors) {
            actor.isdie = false;
            actor.hp = actor.hp_max;
            actor.target = -1;
            actor.viewers.clear();
            actor.route.clear();
            actor.nextRoute = 0;
            actor.nextHit = 0;
            actor.time_refresh = System.currentTimeMillis() + 60_000;
            BattlefieldWalk ground = BattlefieldWalk.of(actor.map);
            actor.homeCell = ground.nearest(actor.x, actor.y);
            if (actor.homeCell >= 0) {
                actor.x = (short) ground.x(actor.homeCell);
                actor.y = (short) ground.y(actor.homeCell);
            }
        }
    }''')

ai = java / 'ai/Player_Nhan_Ban.java'
source = ai.read_text(encoding='utf-8')
start = source.index('	public static void update(Map map)')
end = source.index('	private static void atk(Map map', start)
source = source[:start] + '''    public static void update(Map map) throws IOException {
        long now = System.currentTimeMillis();
        var battle = ChienTruong.gI();
        var players = new ArrayList<>(map.players);
        for (Player_Nhan_Ban actor : battle.list_ai) {
            if (actor.map != map) continue;
            if (actor.isdie) {
                actor.viewers.clear();
                if (now < actor.time_refresh) continue;
                actor.isdie = false;
                actor.hp = actor.hp_max;
            }
            for (Player player : players) {
                if (distance(actor.x, actor.y, player.x, player.y) <= 340) {
                    if (actor.viewers.add(player.id)) battle.get_ai(player, actor.id);
                } else if (actor.viewers.remove(player.id)) {
                    Message remove = new Message(8);
                    remove.writer().writeShort(actor.id);
                    player.conn.addmsg(remove);
                    remove.cleanup();
                }
            }
            Player enemy = null;
            for (Player player : players) {
                if (!player.isdie && player.typepk > 0 && player.typepk != actor.flag()
                        && player.get_eff(-204) == null && distance(actor.x, actor.y, player.x, player.y) < 240
                        && (enemy == null || distance(actor.x, actor.y, enemy.x, enemy.y)
                        > distance(actor.x, actor.y, player.x, player.y))) enemy = player;
            }
            Player_Nhan_Ban rival = null;
            if (actor.roaming && enemy == null) {
                for (Player_Nhan_Ban other : battle.list_ai) {
                    if (other.map == map && other.roaming && !other.isdie && other.village != actor.village
                            && (rival == null || distance(actor.x, actor.y, other.x, other.y)
                            < distance(actor.x, actor.y, rival.x, rival.y))) rival = other;
                }
            }
            if (enemy != null && distance(actor.x, actor.y, enemy.x, enemy.y) <= 58) {
                if (now >= actor.nextHit) {
                    actor.nextHit = now + Util.random(1200, 2100);
                    atk(map, actor, enemy);
                }
                continue;
            }
            if (rival != null && distance(actor.x, actor.y, rival.x, rival.y) <= 58) {
                if (now >= actor.nextHit) {
                    actor.nextHit = now + Util.random(1200, 2100);
                    spar(map, actor, rival, now);
                }
                continue;
            }
            BattlefieldWalk ground = BattlefieldWalk.of(map);
            if (now >= actor.nextRoute && actor.homeCell >= 0) {
                actor.nextRoute = now + Util.random(1800, 2900);
                int x = ground.x(actor.homeCell) + Util.random(-110, 111);
                int y = ground.y(actor.homeCell) + Util.random(-110, 111);
                if (enemy != null) { x = enemy.x; y = enemy.y; }
                else if (rival != null) { x = rival.x; y = rival.y; }
                actor.route = ground.route(ground.nearest(actor.x, actor.y), ground.nearest(x, y));
            }
            if (actor.route.isEmpty()) continue;
            int cell = actor.route.peekFirst();
            actor.x += step(ground.x(cell) - actor.x);
            actor.y += step(ground.y(cell) - actor.y);
            if (actor.x == ground.x(cell) && actor.y == ground.y(cell)) actor.route.removeFirst();
            move(map, actor);
        }
    }

    private static int step(int distance) { return Math.max(-9, Math.min(9, distance)); }

    private static int distance(int x, int y, int otherX, int otherY) {
        return Math.abs(x - otherX) + Math.abs(y - otherY);
    }

    private static void spar(Map map, Player_Nhan_Ban actor, Player_Nhan_Ban target, long now) throws IOException {
        int damage = Math.min(target.hp, actor.dame);
        target.hp -= damage;
        Message attack = new Message(6);
        attack.writer().writeShort(actor.id);
        attack.writer().writeByte(0);
        attack.writer().writeByte(1);
        attack.writer().writeShort(target.id);
        attack.writer().writeInt(damage);
        attack.writer().writeInt(target.hp);
        attack.writer().writeByte(0);
        attack.writer().writeInt(actor.hp);
        attack.writer().writeInt(0);
        attack.writer().writeByte(11);
        attack.writer().writeInt(0);
        for (Player player : map.players) {
            if (actor.viewers.contains(player.id) || target.viewers.contains(player.id)) player.conn.addmsg(attack);
        }
        attack.cleanup();
        if (target.hp == 0) {
            target.isdie = true;
            target.time_refresh = now + 15_000;
            Message remove = new Message(8);
            remove.writer().writeShort(target.id);
            for (Player player : map.players) player.conn.addmsg(remove);
            remove.cleanup();
        }
    }

''' + source[end:]
start = source.index('                            switch (map.map_id)')
end = source.index('Message m = new Message(6);', start)
source = source[:start] + '''                if (temp.map != map || temp.isdie || p.typepk <= 0 || p.typepk == temp.flag()
                        || distance(temp.x, temp.y, p.x, p.y) > 300) return;
                ''' + source[end:]
ai.write_text(source, encoding='utf-8')
edit('ai/Player_Nhan_Ban.java', '		p0.hp -= dame;', '''        dame = (int) Math.min(dame, Math.max(1, p0.body.get_max_hp() / (temp.roaming ? 18 : 12)));
		p0.hp -= dame;''')
edit('ai/Player_Nhan_Ban.java', 'pp.conn.addmsg(m);\n\t\t\t\t}\n\t\t\t\tm3.cleanup();', 'pp.conn.addmsg(m3);\n\t\t\t\t}\n\t\t\t\tm3.cleanup();')
edit('ai/Player_Nhan_Ban.java', 'p0.conn.addmsg(m22);', 'if (temp.viewers.contains(p0.id)) p0.conn.addmsg(m22);')
edit('map/MapService.java', '        p.other_player_inside.clear();', '''        if (Map.is_map_chien_truong(map.map_id)) {
            for (Player_Nhan_Ban actor : ChienTruong.gI().list_ai) actor.forget(p.id);
        }
        p.other_player_inside.clear();''')
edit('ai/Player_Nhan_Ban.java', '    public int flag() {', '''    public void forget(int id) { viewers.remove(id); }

    public int flag() {''')
edit('ai/Player_Nhan_Ban.java', 'new java.util.HashSet<>();', 'java.util.concurrent.ConcurrentHashMap.newKeySet();')
edit('event_daily/ChienTruong.java', 'list_ai = Player_Nhan_Ban.init();', 'list_ai = new java.util.concurrent.CopyOnWriteArrayList<>(Player_Nhan_Ban.init());')
edit('template/ItemSellCoin.java', '''        return item;
    }

    public static final short[] WING_MATERIALS''', '''        if (id == 4635 || id == 4864) {
            item.tier = 15;
            item.level = 1;
        }
        return item;
    }

    public static final short[] WING_MATERIALS''')
edit('template/ItemSellCoin.java', '''        switch (template.getId()) {''', '''        switch (template.getId()) {
            case 4635:
                data = "[[7,4000],[8,4000],[9,4000],[10,4000],[11,4000],[37,3]]"; break;
            case 4864:
                data = "[[23,39],[24,39],[25,39],[26,39],[37,3],[62,10000]]"; break;''')
print(args.out.resolve())
