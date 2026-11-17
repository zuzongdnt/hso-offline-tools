"""Stage the shared gameplay and portable data tools for offline 23."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'build/server-offline23/src/main/java'


def edit(path, old, new):
    text = path.read_text(encoding='utf-8-sig')
    if new in text:
        return
    if text.count(old) != 1:
        raise ValueError(f'Expected one anchor in {path}: {old[:70]}')
    path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')


def main():
    if not SERVER.exists():
        shutil.copytree(ROOT / 'build/server-offline22/src', ROOT / 'build/server-offline23/src')
        shutil.copy2(ROOT / 'build/server-offline22/pom.xml', ROOT / 'build/server-offline23/pom.xml')
    assets = ROOT / 'build/offline23-assets/data'
    if not assets.exists():
        shutil.copytree(ROOT / 'build/offline22-assets', ROOT / 'build/offline23-assets')
    for source in (ROOT / 'shared/src').rglob('*.java'):
        target = SERVER / source.relative_to(ROOT / 'shared/src')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copy2(ROOT / 'shared/offline-tools.html', assets / 'offline-tools.html')
    edit(SERVER / 'core/Manager.java', '        // load item3\n',
         '        try { OfflineTools.restorePending(); } catch (Exception error) {\n'
         '            throw new IOException("Không khôi phục được dữ liệu", error);\n        }\n        // load item3\n')
    edit(SERVER / 'core/SQL.java', '    public void close() {', '''    public String exportSave() throws Exception {
        try (Connection connection = getConnection()) {
            connection.setAutoCommit(false);
            try {
                String text = SaveTransfer.capture(connection);
                connection.commit();
                return text;
            } catch (Exception error) {
                connection.rollback();
                throw error;
            }
        }
    }

    public void importSave(String text) throws Exception {
        SaveTransfer.validate(text);
        try (Connection connection = getConnection()) {
            connection.setAutoCommit(false);
            try {
                SaveTransfer.replace(connection, text);
                connection.commit();
            } catch (Exception error) {
                connection.rollback();
                throw error;
            }
        }
    }

    public void close() {''')
    edit(SERVER / 'core/ServerManager.java', '        Manager.gI().init();\n        Mob_in_map.create_boss();',
         '        Manager.gI().init();\n        OfflineMarket.populate();\n        OfflineTools.start();\n        Mob_in_map.create_boss();')
    edit(SERVER / 'core/SaveData.java', '                        Player p0 = map0.players.get(i1);',
         '                        Player p0 = map0.players.get(i1);\n                        if (p0.is_nhanban) continue;')
    edit(SERVER / 'map/Map.java', '                Player p = players.get(i1);',
         '                Player p = players.get(i1);\n                if (core.OfflineMarket.isMerchant(p)) continue;')
    edit(SERVER / 'map/Map.java', '        this.ismaplang = ismaplang;',
         '        this.ismaplang = ismaplang || id == 82;')
    edit(SERVER / 'core/Service.java', '    public static short get_id_phiphong(Player p) {',
         '    public static short get_id_phiphong(Player p) {\n        if (template.OfflineSkins.dreamOutfit(p)) return -1;')
    edit(SERVER / 'core/Service.java', '    public static short get_id_mat_na(Player p) {',
         '    public static short get_id_mat_na(Player p) {\n        if (template.OfflineSkins.dreamOutfit(p)) return -1;')
    edit(SERVER / 'template/OfflineSkins.java', '    public static short bodyEffect(Player player) {',
         '    public static boolean dreamOutfit(Player player) {\n'
         '        Item3 outfit = player.item.wear[11];\n'
         '        return outfit != null && (outfit.id == 4807 || outfit.id == 4808);\n    }\n\n'
         '    public static short bodyEffect(Player player) {')
    edit(SERVER / 'template/OfflineSkins.java', '    public static Mount mount(short id) {', '''    public static int mountParam(Player player, int id) {
        if (player.type_use_mount < 0 || player.id_horse < 0 || equippedMount(player) != null) return 0;
        if (id >= 23 && id <= 26) return 4;
        return id == 27 ? 500 : 0;
    }

    public static Mount mount(short id) {''')
    edit(SERVER / 'client/Body.java', '    public int total_item_param(int id) {\n        int param = 0;',
         '    public int total_item_param(int id) {\n        int param = template.OfflineSkins.mountParam(p, id);')
    edit(SERVER / 'template/OfflineSkins.java', '            mount.setContent("Thú cưỡi vĩnh viễn.");',
         '            mount.setContent("Thú cưỡi vĩnh viễn. Khi cưỡi: +4 sức mạnh, khéo léo, thể lực, tinh thần; +5% máu.");')
    edit(SERVER / 'template/OfflineSkins.java', '        if (!has(item.id)) return;\n        ItemTemplate3 template',
         '        if (ItemSellCoin.cosmetic(item.type) && item.op.stream().noneMatch(op -> op.id < 58 || op.id > 60)) {\n'
         '            for (Option option : ItemSellCoin.cosmeticOptions(ItemTemplate3.item.get(item.id)))\n'
         '                item.op.add(new Option(option.id, option.getParam(0)));\n        }\n'
         '        if (!has(item.id)) return;\n        ItemTemplate3 template')
    arena = SERVER / 'event_daily/LoiDai.java'
    edit(arena, '    private static Player createOpponent(Player player) throws IOException {',
         '    public static Player createOpponent(Player player) throws IOException {\n'
         '        return createOpponent(player, player.id == 30000 ? 29999 : 30000);\n    }\n\n'
         '    public static Player createOpponent(Player player, int id) throws IOException {')
    edit(arena, '        Player bot = new Player(session, player.id == 30000 ? 29999 : 30000);',
         '        Player bot = new Player(session, id);')
    edit(arena, '        bot.load_skill();',
         '        bot.point3 += 500;\n        bot.point4 += 500;\n        bot.load_skill();')
    edit(arena, '        template.RankBadge.setRank(bot, 2 + clazz);',
         '        bot.item.wear[13].op.add(new Option(36, 2000));\n'
         '        bot.item.wear[13].op.add(new Option(33, 2000));\n'
         '        bot.item.wear[13].op.add(new Option(34, 4000));\n'
         '        bot.item.wear[13].op.add(new Option(35, 4000));\n'
         '        template.RankBadge.setRank(bot, 2 + clazz);')
    edit(SERVER / 'template/ItemSellCoin.java',
         '    private static boolean cosmetic(int type) {', '    static boolean cosmetic(int type) {')
    edit(SERVER / 'template/ItemSellCoin.java',
         '        for (short id = 46; id <= 145; id++) materials.add(id);',
         '        for (short id = 46; id <= 145; id++) {\n'
         '            materials.add(id);\n            ItemTemplate7.item.get(id).setPricetype((byte) 0);\n'
         '            ItemTemplate7.item.get(id).setPrice(1);\n        }')
    edit(SERVER / 'template/ItemSellCoin.java', '        return result;\n    }\n}', '''        if (result.isEmpty() && cosmetic(template.getType())) {
            switch (template.getType()) {
                case 23: case 25: result.add(new Option(29, 100)); break;
                case 21: case 30:
                    for (int id = 23; id <= 26; id++) result.add(new Option(id, 4));
                    break;
                default:
                    for (int id = 7; id <= 11; id++) result.add(new Option(id, 500));
                    result.add(new Option(27, 100));
                    break;
            }
        }
        return result;
    }
}''')
    # Merchants use the existing player-shop packets and never spend an item from a real account.
    game = SERVER / 'core/GameSrc.java'
    edit(game, '\t\t\t\tPlayer p0 = Map.get_player_by_id(id_p);\n\t\t\t\tif (p0 != null && !p0.my_store_name.isEmpty()) {',
         '\t\t\t\tPlayer p0 = Map.get_player_by_id(id_p);\n'
         '\t\t\t\tif (core.OfflineMarket.view(conn, p0)) return;\n'
         '\t\t\t\tif (p0 != null && p0.map == conn.p.map && p0 != conn.p && !p0.my_store_name.isEmpty()) {')
    moly = SERVER / 'event_daily/MoLy.java'
    edit(moly, 'new short[]{2939, 4640, 4639, 4641, 4638, 14}',
         'new short[]{2939, 4640, 4639, 4641, 4638, 14, 4587, 4589, 4588, 4590}')
    edit(moly, 'new byte[]{3, 3, 3, 3, 3, 7}', 'new byte[]{3, 3, 3, 3, 3, 7, 3, 3, 3, 3}')
    edit(moly, 'new byte[]{15, 5, 5, 5, 5, 10}', 'new byte[]{15, 5, 5, 5, 5, 10, 5, 5, 5, 5}')
    edit(moly, '                    ItemTemplate3 temp = ItemTemplate3.item.get(item_mo_ly[i]);', '''                    if (i >= 6) {
                        template.Item3 prize = core.OfflineMarket.lotteryMedal(i - 6);
                        m.writer().writeUTF(prize.name + " +15 • Bỏng lửa");
                        m.writer().writeByte(prize.clazz);
                        m.writer().writeShort(prize.id);
                        m.writer().writeByte(prize.type);
                        m.writer().writeShort(prize.icon);
                        m.writer().writeByte(prize.tier);
                        m.writer().writeShort(prize.level);
                        m.writer().writeByte(prize.color);
                        m.writer().writeByte(prize.op.size());
                        for (template.Option option : prize.op) {
                            m.writer().writeByte(option.id);
                            m.writer().writeInt(option.getParam(prize.tier));
                        }
                        break;
                    }
                    ItemTemplate3 temp = ItemTemplate3.item.get(item_mo_ly[i]);''')
    edit(moly, '        switch (step) {', '''        if (idSelectedItem < 0 || idSelectedItem >= item_mo_ly.length) return;
        if (p.item.get_bag_able() < 1) {
            Service.send_notice_box(p.conn, "Hành trang đầy.");
            return;
        }
        switch (step) {''')
    edit(moly, '                if (p.id_select_mo_ly != -1) {',
         '                if (p.id_select_mo_ly != -1 && p.id_select_mo_ly == idSelectedItem\n'
         '                        && p.item.total_item_by_id(4, 52) > 0) {')
    edit(moly, '                        Service.open_box_notice_item(p, "Xin chúc mừng",', '''                        if (p.id_select_mo_ly >= 6) {
                            p.item.add_item_bag3(core.OfflineMarket.lotteryMedal(p.id_select_mo_ly - 6));
                            p.item.char_inventory(3);
                            p.item.char_inventory(4);
                            Service.send_notice_box(p.conn, "Nhận được mề đay +15 có Bỏng lửa!");
                        } else Service.open_box_notice_item(p, "Xin chúc mừng",''')
    combat = SERVER / 'map/MapService.java'
    text = combat.read_text(encoding='utf-8')
    old = 'if (blParam > 0 && (blParam >= 100 || blParam > Util.random(10000))) {'
    new = 'if (blParam > 0 && TinhTu.rolls(blParam)) {'
    assert text.count(old) == 2 or text.count(new) == 2
    combat.write_text(text.replace(old, new), encoding='utf-8')
    edit(combat, 'if (map.zone_id == map.maxzone || (map.zone_id == 1 && Map.has_monster(map.map_id))) {',
         'if (map.map_id == 82 || map.zone_id == map.maxzone || (map.zone_id == 1 && Map.has_monster(map.map_id))) {')
    edit(combat, '    public static void change_flag(Map map, Player p_target, int type) throws IOException {',
         '    public static void change_flag(Map map, Player p_target, int type) throws IOException {\n'
         '        if (map.map_id == 82 && type != -1) return;')
    edit(combat, 'if (p0 == null || p0.id == p.id || p.map.ismaplang || p.level < 11 || p0.level < 11',
         'if (p0 == null || p0.id == p.id || p.map.map_id == 82 || p.map.ismaplang || p.level < 11 || p0.level < 11')
    edit(combat, '            if (p0.pet_follow) {\n                for (Pet temp : p0.mypet) {',
         '            if (p != p0 && p0.pet_follow && p0.mypet.stream().anyMatch(pet -> pet.is_follow)) {\n'
         '                for (Pet temp : p0.mypet) {')
    edit(SERVER / 'core/Service.java', '        if (p.pet_follow) {\n            for (Pet temp : p.mypet) {',
         '        if (p.pet_follow && p.mypet.stream().anyMatch(pet -> pet.is_follow)) {\n            for (Pet temp : p.mypet) {')
    edit(game, 'm.writer().writeInt(GameSrc.wing_upgrade_material_time[it.tier] * 60);',
         'm.writer().writeInt(0); // Offline wing upgrades finish immediately.')
    edit(game, '                    it.time_use = System.currentTimeMillis()\n'
               '                            + (((long) GameSrc.wing_upgrade_material_time[it.tier - 1]) * 3_600_000L);',
         '                    it.time_use = 0; // Clear the upgrade timer before sending the bag.')
    edit(game, '                    conn.p.item.remove(7, 8, GameSrc.wing_upgrade_material_long_khuc_xuong[it.tier]);',
         '                    conn.p.update_vang(-GameSrc.wing_upgrade_material_gold[it.tier]);\n'
         '                    conn.p.item.remove(7, 8, GameSrc.wing_upgrade_material_long_khuc_xuong[it.tier]);')
    edit(game, '        if (type == 1) { // create\n            if (wing < 2880',
         '        if ((type == 2 || type == 3) && (id < 0 || id >= conn.p.item.bag3.length)) return;\n'
         '        if (type == 2 || type == 3) {\n'
         '            Item3 target = conn.p.item.bag3[id];\n'
         '            if (target == null || target.id < 2880 || target.id > 2929 || (target.id - 2880) % 7 != 0\n'
         '                    || target.tier < 0 || target.tier >= GameSrc.wing_upgrade_material_gold.length) return;\n'
         '            target.time_use = 0; // Release wings left waiting by older offline versions.\n'
         '        }\n        if (type == 1) { // create\n            if (wing < 2880')
    edit(game, '\t\t\t\tPlayer p0 = Map.get_player_by_id(idChar);\n\t\t\t\tif (p0 != null && !p0.my_store_name.isEmpty()) {',
         '\t\t\t\tPlayer p0 = Map.get_player_by_id(idChar);\n'
         '\t\t\t\tif (core.OfflineMarket.buy(conn, p0, iditem, idType)) return;\n'
         '\t\t\t\tif (p0 != null && p0.map == conn.p.map && p0 != conn.p && !p0.my_store_name.isEmpty()) {')
    edit(game, 'public static void player_store(Session conn, Message m2)', 'public static synchronized void player_store(Session conn, Message m2)')
    edit(game, 'if (conn.p.map.map_id != 82) {', 'if (conn.p.map.map_id != 82 || conn.p.isdie) {')
    edit(game, 'if (p0.my_store.get(i).it_type == 3 && p0.item.bag3[p0.my_store.get(i).it_id] != null',
         'if (idType == 3 && p0.my_store.get(i).it_type == 3 && p0.item.bag3[p0.my_store.get(i).it_id] != null')
    edit(game, '\t\t\t\t\t\t\tconn.p.update_vang(-vang_trade);\n\t\t\t\t\t\t\tvang_trade = (vang_trade / 100) * 95;\n\t\t\t\t\t\t\tp0.update_vang(vang_trade);\n\t\t\t\t\t\t\tconn.p.item.add_item_bag3(p0.item.bag3[p0.my_store.get(i).it_id]);',
         '\t\t\t\t\t\t\tif (conn.p.item.get_bag_able() < 1 || !conn.p.item.add_item_bag3(p0.item.bag3[p0.my_store.get(i).it_id])) {\n'
         '\t\t\t\t\t\t\t\tService.send_notice_box(conn, "Hành trang đầy.");\n\t\t\t\t\t\t\t\treturn;\n\t\t\t\t\t\t\t}\n'
         '\t\t\t\t\t\t\tconn.p.update_vang(-vang_trade);\n\t\t\t\t\t\t\tvang_trade = (int)(vang_trade * 95L / 100);\n\t\t\t\t\t\t\tp0.update_vang(vang_trade);')
    # A fallback is applied only to empty cosmetic option lists. Existing reference stats stay authoritative.
    skins = assets / 'offline-skins.json'
    rows = json.loads(skins.read_text(encoding='utf-8'))
    fallback = {15: [[7,1000],[8,1000],[9,1000],[10,1000],[11,1000],[15,1000]],
                21: [[23,4],[24,4],[25,4],[26,4]],
                22: [[7,500],[8,500],[9,500],[10,500],[11,500],[15,1500],[27,100]],
                23: [[29,100]], 25: [[29,100]], 24: [[7,2500],[8,2500],[9,2500],[10,2500],[11,2500]],
                30: [[23,4],[24,4],[25,4],[26,4],[27,500]],
                31: [[7,1000],[8,1000],[9,1000],[10,1000],[11,1000]],
                32: [[7,1000],[8,1000],[9,1000],[10,1000],[11,1000]]}
    for row in rows:
        if not row['options'] and row['type'] in fallback:
            row['options'] = fallback[row['type']]
            row['refreshOptions'] = True
    skins.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
