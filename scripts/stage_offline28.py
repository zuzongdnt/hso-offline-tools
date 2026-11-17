"""Create the 28 source tree without changing installed games or saves."""
from pathlib import Path
import argparse
import shutil

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=root / 'build/server-offline27-release')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    parser.error('Choose a new output directory.')
shutil.copytree(args.source / 'src', args.out / 'src')
shutil.copy2(args.source / 'pom.xml', args.out / 'pom.xml')
java = args.out / 'src/main/java'

def edit(name, old, new):
    path = java / name
    source = path.read_text(encoding='utf-8')
    if source.count(old) != 1:
        raise ValueError('Unexpected source: ' + name + ': ' + old[:65])
    path.write_text(source.replace(old, new), encoding='utf-8')

edit('core/OfflineTools.java', 'VERSION = 27;', 'VERSION = 28;')
edit('template/ItemSellCoin.java', '    public static List<Option> cosmeticOptions(ItemTemplate3 template) {', '''    public static List<Option> cosmeticOptions(ItemTemplate3 template) {
        if (template.getId() >= 4870 && template.getId() <= 4872) return new ArrayList<>();''')
edit('template/ItemSellCoin.java', '''        switch (template.getId()) {
            case 4634:''', '''        switch (template.getId()) {
            case 4737:
                data = "[[15,500],[27,1000],[122,10000]]"; break;
            case 4688:
                data = "[[7,1000],[8,1000],[9,1000],[10,1000],[11,1000],[27,1000],[28,1000]]"; break;
            case 4634:''')
edit('template/OfflineSkins.java', 'Set.of(4633, 4634, 4707, 4755)', 'Set.of(4633, 4634, 4707, 4755, 4737, 4688)')
edit('template/OfflineSkins.java', '''        return costume == null ? -1 : bodyEffects.getOrDefault(costume.id, (short) -1);''', '''        short effect = costume == null ? -1 : bodyEffects.getOrDefault(costume.id, (short) -1);
        return (short) (player.type_use_mount >= 0 && (effect == 253 || effect == 254) ? effect + 2 : effect);''')
edit('ai/Player_Nhan_Ban.java', '\t\t\t\tp0.type_use_mount = -1;', '')
edit('map/MapService.java', '''            } else {
                Service.send_char_main_in4(p);
            }
            Service.send_combo''', '''            } else {
                Service.send_char_main_in4(p);
                if (p.type_use_mount >= 0) map.send_mount(p);
            }
            Service.send_combo''')
edit('event_daily/MoLy.java', '''        if (idSelectedItem < 0 || idSelectedItem >= item_mo_ly.length) return;''', '''        if (step == 2) idSelectedItem = p.id_select_mo_ly;
        if (idSelectedItem < 0 || idSelectedItem >= item_mo_ly.length) return;''')
edit('event_daily/MoLy.java', 'p.item.get_bag_able() < 1', 'p.item.get_bag_able() < 3')
edit('event_daily/MoLy.java', 'if (p.id_select_mo_ly == -1) {', 'if (p.id_select_mo_ly != idSelectedItem) {')
edit('event_daily/MoLy.java', '''                            Service.send_notice_box(p.conn, "Nhận được mề đay +15 có Bỏng lửa!");''', '''                            template.Item3 reward = core.OfflineMarket.lotteryMedal(p.id_select_mo_ly - 6);
                            Message notice = new Message(78);
                            notice.writer().writeUTF("Xin chúc mừng"); notice.writer().writeByte(1);
                            notice.writer().writeUTF(reward.name); notice.writer().writeShort(reward.icon);
                            notice.writer().writeInt(1); notice.writer().writeByte(3);
                            notice.writer().writeByte(15); notice.writer().writeByte(reward.color);
                            notice.writer().writeUTF(""); notice.writer().writeByte(1); notice.writer().writeByte(1);
                            p.conn.addmsg(notice); notice.cleanup();''')
edit('core/OfflineMarket.java', 'new Option(81, 5)', 'new Option(81, 5000)')
edit('core/OfflineMarket.java', 'new Option(88, 3)', 'new Option(88, 3000)')
edit('core/OfflineMarket.java', 'new Option(77, 5)', 'new Option(77, 5000)')
path = java / 'core/OfflineMarket.java'
source = path.read_text(encoding='utf-8')
source = source.replace('new Option(33, 1000)', 'new Option(new int[]{33, 34, 35, 36}[clazz], 1000)')
source = source.replace('new Option(33, 500)', 'new Option(new int[]{33, 34, 35, 36}[clazz], 500)')
path.write_text(source, encoding='utf-8')
edit('template/Item3.java', 'public int optionValue(Option option) {', '''public int optionValue(Option option) {
        int effectId = Byte.toUnsignedInt(option.id);
        if (type == 16 && (effectId == 77 || effectId == 79 || effectId == 81 || effectId == 86 || effectId == 88)) {
            int duration = option.getParam(tier);
            return duration > 0 && duration <= 60 ? duration * 1000 : duration;
        }''')
path = java / 'template/Item3.java'
text = path.read_text(encoding='utf-8')
text = text.replace('(type == 15 || (type >= 21', '(type == 15 || type == 16 || (type >= 21')
path.write_text(text, encoding='utf-8')
edit('event_daily/LoiDai.java', '        player.is_changemap = false;\n        if (player.conn.connected)', '''        player.is_changemap = false;
        player.is_atk = true;
        Service.send_char_main_in4(player);
        if (player.conn.connected)''')
# Main-character position corrections lock the client until its path finishes.
# Reloading the arena clears the route instead of queueing a path on a dead actor.
path = java / 'event_daily/LoiDai.java'
text = path.read_text(encoding='utf-8')
first = text.index('        for (Player fighter : new Player[]{p1, p2}) {', text.index('MapService.send_in4_other_char(map, p1, p2);', text.index('private void resetFighters')))
last = text.index('\n    }', first)
text = text[:first] + '        map.send_map_data(p1);\n        if (p1.type_use_mount >= 0) map.send_mount(p1);' + text[last:]
path.write_text(text, encoding='utf-8')
edit('core/MenuController.java', '"TikTok: thinhdzuong", "Đổi quà theo điểm",', '"TikTok: thinhdzuong", "Shop skin Lôi đài",')
edit('core/MenuController.java', '                LoiDai.claimRankReward(conn.p);', '                core.ArenaShop.show(conn.p, 0);')
edit('core/MenuController.java', '        switch (idnpc) {\n            case -1:', '''        if (idnpc == 12001) { core.ArenaShop.select(conn.p, Byte.toUnsignedInt(index)); return; }
        switch (idnpc) {
            case -1:''')
edit('template/ItemSellCoin.java', '!REMOVED_GOLD_STOCK.contains((int)offer.id) && offer.available()', '!REMOVED_GOLD_STOCK.contains((int)offer.id) && !core.ArenaShop.contains(offer.id) && offer.available()')
shutil.copy2(root / 'shared/src/core/ArenaShop.java', java / 'core/ArenaShop.java')
shutil.copy2(root / 'shared/src/core/ArenaRoster.java', java / 'core/ArenaRoster.java')
edit('event_daily/LoiDai.java', '    public static void start(Player player) throws IOException {', '''    public static void start(Player player) throws IOException { start(player, null); }
    public static void start(Player player, Player selectedBot) throws IOException {''')
edit('event_daily/LoiDai.java', '        Player bot = createOpponent(player);', '        Player bot = selectedBot == null ? createOpponent(player) : selectedBot;')
edit('event_daily/LoiDai.java', '        bot.hp = bot.body.get_max_hp();', '''        java.util.List<ItemSellCoin> costumes = ItemSellCoin.entry.stream()
                .filter(row -> row.available() && template.ItemTemplate3.item.get(row.id).getType() == 15).collect(java.util.stream.Collectors.toList());
        if (!costumes.isEmpty()) {
            Item3 costume = costumes.get(Math.floorMod(id, costumes.size())).createItem();
            bot.item.wear[11] = costume; bot.fashion = template.Part_fashion.get_part(bot);
        }
        bot.hp = bot.body.get_max_hp();''')
edit('core/Service.java', '            if (p0 == null) p0 = Map.get_player_by_name(name);', '''            if (p0 == null) p0 = Map.get_player_by_name(name);
            if (p0 == null) p0 = core.ArenaRoster.find(name);''')
edit('core/MenuController.java', '        if (idnpc == 12001)', '''        if (idnpc == 12002) { core.ArenaRoster.select(conn.p, Byte.toUnsignedInt(index)); return; }
        if (idnpc == 12003) { core.ArenaRoster.action(conn.p, Byte.toUnsignedInt(index)); return; }
        if (idnpc == 12001)''')
edit('core/MenuController.java', '"BXH Chiến Trường", "BXH Bang Hội"', '"BXH Chiến Trường", "BXH Bang Hội", "Danh sách thi đấu", "Top thi đấu", "Về làng"')
edit('core/MenuController.java', '''    private static void Menu_BXH(Session conn, byte index) throws IOException {
''', '''    private static void Menu_BXH(Session conn, byte index) throws IOException {
        if (index == 5) { core.ArenaRoster.show(conn.p, 0); return; }
        if (index == 6) { core.ArenaRoster.ranking(conn.p); return; }
        if (index == 7) {
            if (conn.p.map.ld != null) { conn.p.map.ld.leave(conn.p); return; }
            if (conn.p.dungeon != null || Map.is_map_chien_truong(conn.p.map.map_id)) {
                Service.send_notice_box(conn, "Hãy rời trận hoặc phó bản trước khi về làng."); return;
            }
            Vgo home = new Vgo(); home.id_map_go = 1; home.x_new = 528; home.y_new = 480;
            conn.p.change_map(conn.p, home); return;
        }
''')
edit('map/MapService.java', '        if (chat.equals("/offline-speed-1")', '''        if (chat.equalsIgnoreCase("/velang") || chat.equalsIgnoreCase("/vềlàng")) {
            if (map.ld != null) { map.ld.leave(conn.p); return; }
            if (conn.p.dungeon != null || Map.is_map_chien_truong(map.map_id)) {
                Service.send_notice_box(conn, "Hãy rời trận hoặc phó bản trước khi về làng."); return;
            }
            Vgo home = new Vgo(); home.id_map_go = 1; home.x_new = 528; home.y_new = 480;
            conn.p.change_map(conn.p, home); return;
        }
        if (chat.equals("/offline-speed-1")''')
print(args.out.resolve())
