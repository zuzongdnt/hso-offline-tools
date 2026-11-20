"""Apply free equipment crafting and the sacred-fire EXP bonus."""
import argparse
import re
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


def edit(file, old, new='', count=1):
    path = java / file
    source = path.read_text(encoding='utf-8')
    if source.count(old) != count:
        raise ValueError(f'Unexpected source: {file}: {old[:90]}')
    path.write_text(source.replace(old, new), encoding='utf-8')


def span(file, start, end, replacement='', count=1):
    path = java / file
    source = path.read_text(encoding='utf-8')
    updated, hits = re.subn(re.escape(start) + r'.*?(?=' + re.escape(end) + r')',
                            lambda _: replacement, source, flags=re.S)
    if hits != count:
        raise ValueError(f'Unexpected source: {file}: {start!r}, {hits} hits')
    path.write_text(updated, encoding='utf-8')


edit('core/OfflineTools.java', 'VERSION = 36;', 'VERSION = 37;')
g = 'core/GameSrc.java'
span(g, '    // Matches the cường hóa prices', '    public static byte[] percent')
edit(g, 'payForRebuild(conn, selected, tem)', 'prepareRebuild(selected, tem)')
span(g, '    private static String payForRebuild(', '    public synchronized static void trade_process(', '''    private static String prepareRebuild(Item3 item, byte currency) {
        if (item == null) return "Chọn trang bị cần cường hóa trong hành trang.";
        if (currency != 0 && currency != 1) return "Lựa chọn cường hóa không hợp lệ.";
        if (!item.islock) {
            item.islock = true;
            item.name = ItemTemplate3.item.get(item.id).getName() + " [Khóa]";
        }
        return null;
    }

''')
span(g, '                        if (conn.p.is_use_mayman\n', '                        conn.p.item.char_inventory(4);')
edit(g, '        if (tem == 7 && (id < 0 || id >= ItemTemplate7.item.size())) return;', '''        if (tem == 7 && (id < 0 || id >= ItemTemplate7.item.size())) return;
        if (type == 4 && (id < 0 || id >= conn.p.item.bag3.length)) return;''')
span(g, '\t\t\t\t\t\tif (conn.p.item.total_item_by_id(7,\n', '\t\t\t\t\t\tint bound1')
span(g, '\t\t\t\t\t\tfor (int i = bound1; i < bound2; i++)', '\t\t\t\t\t\t// change material')
edit(g, '\t\t\t\t\t\tint bound2 = 5 + 5 * conn.p.id_medal_is_created;\n')
span(g, '\t\t\t\t\t\tfor (int i = 0; i < conn.p.tinhtu_material.length; i++) {\n\t\t\t\t\t\t\tif (conn.p.item.total_item_by_id',
     '\t\t\t\t\t\tint index_create')
edit(g, '\t\t\t\tif (conn.p.id_medal_is_created != -1) {', '''                if (conn.p.item.get_bag_able() < 1) {
                    Service.send_notice_box(conn, "Cần ô trống trong hành trang.");
                    return;
                }
                if (conn.p.id_medal_is_created >= 0 && conn.p.id_medal_is_created < 36) {''')
span(g, '\t\t\t\t\tfor (int i = 5 * (it_temp.id - 4587); i < 5 * (it_temp.id - 4587) + 5; i++) {\n\t\t\t\t\t\tshort id_item_upgr', '\t\t\t\t\tboolean suc')
span(g, '\t\t\t\t\tfor (int i = 0; i < conn.p.tinhtu_material.length; i++) {\n\t\t\t\t\t\tshort id_item_upgr', '\t\t\t\t\tint luck')
span(g, '    private static int get_ngoc_medal_upgrade(', '    public static void Create_Medal(')
edit(g, 'm_send.writer().writeShort(get_quant_material_medal_upgrade(it_temp.tier));', 'm_send.writer().writeShort(0);')
edit(g, '''m_send.writer()
\t\t\t\t\t\t\t      .writeShort(get_quant_material_medal_upgrade((byte) Item.get_level_tinh_tu(it_temp.level)));''', 'm_send.writer().writeShort(0);')
span(g, '            int fee = source.tier * 100;', '            target.tier = source.tier;')
edit(g, '''Service.send_box_input_yesno(p.conn,122,"Chuyển hóa cùng loại, không giới hạn cấp độ. Phí "
                    + (p.item.bag3[p.item_replace].tier*100) + " ngọc và 2 đá thạch anh cấp 3. Xác nhận?");''',
     'Service.send_box_input_yesno(p.conn,122,"Chuyển hóa miễn phí giữa hai trang bị cùng loại. Xác nhận?");')
span(g, '            if (conn.p.item.total_item_by_id(7, 8) < 80) {', '            ItemTemplate3 temp = ItemTemplate3.item.get(wing);')
edit(g, 'target.tier >= GameSrc.wing_upgrade_material_gold.length', 'target.tier > 29')
edit(g, 'm.writer().writeInt(GameSrc.wing_upgrade_material_gold[it.tier]);', 'm.writer().writeInt(0);')
span(g, '                    m.writer().writeByte(6);\n                    m.writer().writeShort(8);', '                    conn.addmsg(m);', '                    m.writer().writeByte(0); // No ingredients.\n')
span(g, '                    // check material\n                    if (conn.p.item.total_item_by_id(7, 8)', '                    it.tier++;')
span(g, '\t\t\t\t\tint quant = conn.p.item.total_item_by_id(7, id);', '\t\t\t\t} else if (tem == 3)', '''                    Message m = new Message(-105);
                    m.writer().writeByte(0);
                    m.writer().writeByte(0);
                    m.writer().writeShort(id);
                    conn.addmsg(m);
                    m.cleanup();
''')
edit(g, '\t\t\t\tString name = ItemTemplate7.item.get(id).getName();\n\t\t\t\tService.send_box_input_text(conn, 7, name, new String[] {"Số lượng (5000 vàng/1)"});', '''                if (id < 46 || id >= 246 || id + 100 >= ItemTemplate7.item.size()
                        || ItemTemplate7.item.get(id).getType() != 54) return;
                String name = ItemTemplate7.item.get(id).getName();
                conn.p.fusion_material_medal_id = id;
                Service.send_box_input_text(conn, 7, name, new String[]{"Số lượng (miễn phí)"});''')
edit(g, '''\t\t\t\tif (conn.p.fusion_material_medal_id == -1) {
\t\t\t\t\tconn.p.fusion_material_medal_id = id;
\t\t\t\t}
''')
edit(g, '                    int vang_total = (GameSrc.get_vang_hopngoc(id_g1) / 50_000) * 1_000_000;\n')
edit(g, '                    p.update_vang(-vang_total);\n                    p.item.remove(7, id_g1, 1);\n')
span(g, '                    if (p.get_vang() < ((index_ngoc_kham_vao + 1) * 1_000_000)) {',
     '                    boolean suc = false;', '''                    if (p.item.total_item_by_id(7, id_g1) < 1) {
                        Service.send_notice_box(p.conn, "Chọn loại đục có trong hành trang. Đục lỗ không tiêu hao vật phẩm.");
                        return;
                    }
''')

s = 'core/Service.java'
edit(s, 'm.writer().writeUTF("Cường hóa trang bị");', 'm.writer().writeUTF("Cường hóa miễn phí");')
span(s, '                m.writer().writeByte(5);\n                //\n                m.writer().writeShort(conn.p.medal_create_material[0 + 5 * (type - 25)]);',
     '                break;', '                m.writer().writeByte(0); // No ingredients.\n')
edit(s, 'm2.writer().writeInt(200_000);\n                m2.writer().writeShort(60);', 'm2.writer().writeInt(0);\n                m2.writer().writeShort(60);')
span(s, '                m2.writer().writeByte(6);\n                m2.writer().writeShort(8);', '                p.conn.addmsg(m2);',
     '                m2.writer().writeByte(0); // No ingredients.\n')
span('core/MenuController.java', '                m.writer().writeByte(p.tinhtu_material.length);', '                p.conn.addmsg(m);',
     '                m.writer().writeByte(0); // No ingredients.\n')

hero = 'template/HeroArmor.java'
edit(hero, '    private static final int MATERIAL_COUNT = 500;\n    private static final int GOLD = 2_000_000;\n')
span(hero, '        int owned = player.item.total_item_by_id(7, FIRST_MATERIAL + color);', '    }', '''        Service.send_box_input_yesno(player.conn, 198, "Chế tạo miễn phí giáp siêu nhân " + COLORS[color] + "?");
''')
span(hero, '        short ingredient = (short) (FIRST_MATERIAL + color);', '        if (player.item.get_bag_able()')
edit(hero, '        player.item.remove(7, ingredient, MATERIAL_COUNT);\n        player.update_vang(-GOLD);\n')

text = 'client/TextFromClient.java'
span(text, '                int quant_inbag = conn.p.item.total_item_by_id(7, conn.p.fusion_material_medal_id);',
     '                conn.p.fusion_material_medal_id = -1;', '''                short output = (short) (conn.p.fusion_material_medal_id + 100);
                if (!addFreeCraftMaterials(conn.p, output, quant)) return;
                Message result = new Message(-105);
                result.writer().writeByte(2);
                result.writer().writeByte(3);
                result.writer().writeUTF("Đã hợp miễn phí " + quant + " " + ItemTemplate7.item.get(output).getName());
                result.writer().writeShort(output);
                result.writer().writeByte(7);
                conn.addmsg(result);
                result.cleanup();
''')
span(text, '\t\t\t\tint quant_ngoc_can_create = conn.p.item.total_item_by_id(7, conn.p.id_ngoc_tinh_luyen);',
     '\t\t\t\tbreak;', '''                int source = conn.p.id_ngoc_tinh_luyen;
                if (source < 352 || source > 381) return;
                short output = (short) (source + 30);
                if (!addFreeCraftMaterials(conn.p, output, quant)) return;
                conn.p.id_ngoc_tinh_luyen = -1;
                Service.send_notice_box(conn, "Đã tinh luyện miễn phí " + quant + " " + ItemTemplate7.item.get(output).getName());
''')
span(text, '\t\t\t\tint quant_ngoc_can_create = conn.p.item.total_item_by_id(7, conn.p.id_hop_ngoc)',
     '\t\t\t\tMessage m = new Message(-100);', '''                if (!GameSrc.canFuseGem(conn.p.id_hop_ngoc)) return;
                short output = (short) (conn.p.id_hop_ngoc + 1);
                if (!addFreeCraftMaterials(conn.p, output, quant)) return;
                conn.p.id_hop_ngoc = -1;
''')
path = java / text
body = path.read_text(encoding='utf-8')
start = body.index('if (!GameSrc.canFuseGem(')
end = body.index('break;', start)
body = body[:start] + body[start:end].replace('itbag.id', 'output') + body[end:]
offset = body.rfind('}')
body = body[:offset] + '''    private static boolean addFreeCraftMaterials(Player player, short material, int amount) throws IOException {
        int owned = player.item.total_item_by_id(7, material);
        if (amount <= 0 || amount > 32_000 - owned || (owned == 0 && player.item.get_bag_able() < 1)) {
            Service.send_notice_box(player.conn, "Số lượng không hợp lệ hoặc hành trang đã đầy.");
            return false;
        }
        Item47 item = new Item47();
        item.id = material;
        item.category = 7;
        item.quantity = (short) amount;
        player.item.add_item_bag47(7, item);
        player.item.char_inventory(7);
        return true;
    }
''' + body[offset:]
path.write_text(body, encoding='utf-8')
edit(g, '''                if (id_item == 27 || id_item == 32 || id_item == 356 || id_item == 361 || id_item == 366 || id_item == 371 || id_item == 376 || id_item == 381) {''',
     '''                if (!canFuseGem(id_item)) {''')
edit(g, '                } else if (GameSrc.get_vang_hopngoc(id_item) <= 200_000) {', '                } else {')
edit(g, '''                } else {
                    Service.send_notice_box(p.conn, "Đã hợp tối đa!");
                }
                break;''', '''                }
                break;''')
edit(g, '    public static int get_vang_hopngoc(int id) {', '''    public static boolean canFuseGem(int id) {
        if (id >= 23 && id <= 32) return id != 27 && id != 32;
        return id >= 352 && id < 417 && (id - 352) % 5 != 4;
    }

    public static int get_vang_hopngoc(int id) {''')

edit('map/Map.java', '    private static final int CAMPFIRE_EXP_PERCENT = 2000;', '    private static final long CAMPFIRE_EXP = 2_000_000_000L;')
edit('map/Map.java', 'public synchronized int campfireExpPercent(Player player)', 'public synchronized long campfireExpBonus(Player player)')
edit('map/Map.java', '? CAMPFIRE_EXP_PERCENT + campfire.oil() * 5 : 0;', '? CAMPFIRE_EXP : 0;')
edit('client/Player.java', 'dame_exp += dame_exp * map.campfireExpPercent(this) / 100;', 'dame_exp += map.campfireExpBonus(this);')
edit('core/Manager.java', '"Cộng thêm 2000% EXP khi đứng gần. Thời gian sử dụng 1 tiếng."',
     '"Cộng thêm 2 tỷ EXP mỗi lần nhận EXP đánh quái khi đứng gần. Hiệu lực 1 giờ."')
edit('core/Manager.java', 'this.msg_61 = Util.loadfile("data/msg/msg_61");',
     'this.msg_61 = GameSrc.freeRebuildPrices(Util.loadfile("data/msg/msg_61"));')
edit(g, '    public static void rebuild_item(', '''    public static byte[] freeRebuildPrices(byte[] original) throws IOException {
        byte[] packet = original.clone();
        try (var reader = new java.io.DataInputStream(new java.io.ByteArrayInputStream(packet))) {
            for (int list = 0; list < 2; list++) {
                int length = reader.readUnsignedByte();
                for (int i = 0; i < length; i++) reader.readUTF();
            }
            int materials = reader.readUnsignedByte();
            for (int i = 0; i < materials; i++) reader.readShort();
            int tiers = reader.readUnsignedByte();
            for (int i = 0; i < tiers; i++) {
                reader.readByte(); // Tier, followed by gold, gems and four ingredients.
                int start = packet.length - reader.available();
                reader.readInt();
                reader.readShort();
                reader.readInt();
                java.util.Arrays.fill(packet, start, start + 10, (byte) 0);
                // Older clients hide the action when both currency fields are zero.
                packet[start] = packet[start + 1] = packet[start + 2] = packet[start + 3] = (byte) -1;
            }
        }
        return packet;
    }

    public static void rebuild_item(''')
print(args.out.resolve())
