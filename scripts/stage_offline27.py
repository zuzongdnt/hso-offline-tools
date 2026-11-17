"""Stage the next offline server without touching the installed game or saves."""
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/server-offline23"
TARGET = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "build/server-offline27e"


def replace(name, old, new):
    path = TARGET / "src/main/java" / name
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        raise ValueError(f"Expected one anchor in {name}: {old[:75]}")
    path.write_text(source.replace(old, new), encoding="utf-8", newline="\n")


def replace_between(name, start, end, new=""):
    path = TARGET / "src/main/java" / name
    source = path.read_text(encoding="utf-8")
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError(f"Expected one block in {name}: {start[:60]}")
    first = source.index(start)
    last = source.index(end, first)
    path.write_text(source[:first] + new + source[last:], encoding="utf-8", newline="\n")


def main():
    if TARGET.exists():
        raise SystemExit(f"Output exists: {TARGET}")
    shutil.copytree(SOURCE / "src", TARGET / "src")
    shutil.copy2(SOURCE / "pom.xml", TARGET / "pom.xml")

    arena = "event_daily/LoiDai.java"
    replace(arena, "    private static final int ROUND_SECONDS = 60;", "    private static final int ROUND_SECONDS = 60;\n    private static final int WAIT_SECONDS = 3;")
    replace(arena, "        if (player.level < 50) {", "        if (player.level < 50 || player.level > 139) {")
    replace(arena, '"Lôi đài offline mở từ cấp 50."', '"Lôi đài offline dành cho cấp 50 đến 139."')
    replace(arena, "bot.level = (short) (player.level / 10 * 10 + Util.random(10));",
            "int lower = player.level < 55 ? 50 : 55 + (player.level - 55) / 10 * 10;\n"
            "        int upper = Math.min(139, player.level < 55 ? 64 : lower + 9);\n"
            "        bot.level = (short) (lower + Util.random(upper - lower + 1));")
    replace(arena, "            setTimer(1);\n            ready = true;", "            setTimer(WAIT_SECONDS);\n            ready = true;")
    replace(arena, "        moveOpponent(time);", "        if (state_ld == 1) moveOpponent(time);")
    replace(arena, "                    setTimer(1);", "                    setTimer(WAIT_SECONDS);")
    replace(arena, "    private synchronized int secondsLeft() {", "    public boolean isWaiting() { return state_ld == 0; }\n\n    private synchronized int secondsLeft() {")
    replace(arena, "            fighter.mp = fighter.body.get_max_mp();", "            fighter.mp = fighter.body.get_max_mp();\n            fighter.x = fighter == p1 ? (short) 288 : (short) 408;\n            fighter.y = 228;")
    replace(arena, "        MapService.send_in4_other_char(map, p1, p2);\n    }",
            "        MapService.send_in4_other_char(map, p1, p2);\n"
            "        for (Player fighter : new Player[]{p1, p2}) {\n"
            "            Message position = new Message(4);\n"
            "            position.writer().writeByte(0); position.writer().writeShort(0);\n"
            "            position.writer().writeShort(fighter.id);\n"
            "            position.writer().writeShort(fighter.x); position.writer().writeShort(fighter.y);\n"
            "            position.writer().writeByte(-1); p1.conn.addmsg(position);\n"
            "        }\n    }")
    replace(arena, "    public static void claimTestReward(Player player) throws IOException {", "    private static void claimTestReward(Player player) throws IOException {")

    service = "map/MapService.java"
    replace(service, "        p_target.type_use_mount = -1;\n    }", "    }")
    replace(service, "        if (p.type_use_mount != 10 && template.OfflineSkins.equippedMount(p) == null) {\n        p.type_use_mount = -1;\n        }}", "        }")
    replace(service, "        if (!conn.p.is_atk) {", "        if (!conn.p.is_atk || map.ld != null && map.ld.isWaiting()) {")
    replace(service, "        short x_new = m2.reader().readShort();\n        short y_new = m2.reader().readShort();",
            "        short x_new = m2.reader().readShort();\n        short y_new = m2.reader().readShort();\n"
            "        if (map.ld != null && map.ld.isWaiting()) {\n"
            "            Message position = new Message(4);\n"
            "            position.writer().writeByte(0); position.writer().writeShort(0);\n"
            "            position.writer().writeShort(p.id);\n"
            "            position.writer().writeShort(p.x); position.writer().writeShort(p.y);\n"
            "            position.writer().writeByte(-1); p.conn.addmsg(position);\n"
            "            return;\n        }")
    revive = TARGET / "src/main/java/client/Process_Yes_no_box.java"
    source = revive.read_text(encoding="utf-8")
    old = "                            Service.send_char_main_in4(conn.p);\n                            // chest in4"
    if source.count(old) != 2:
        raise ValueError("Expected two on-site revival branches")
    revive.write_text(source.replace(old, "                            Service.send_char_main_in4(conn.p);\n                            if (conn.p.type_use_mount >= 0) conn.p.map.send_mount(conn.p);\n                            // chest in4"), encoding="utf-8", newline="\n")

    menu = "core/MenuController.java"
    replace(menu, '"Nhận quà thử", "TikTok: thinhdzuong", "Đổi quà theo điểm"',
            '"TikTok: thinhdzuong", "Đổi quà theo điểm"')
    replace(menu, "            case 3:\n                LoiDai.claimTestReward(conn.p);\n                break;\n            case 4:", "            case 3:")
    replace(menu, "            case 5:\n                LoiDai.claimRankReward(conn.p);", "            case 4:\n                LoiDai.claimRankReward(conn.p);")
    replace(menu, "            case 6: {\n                conn.p.list_thao_kham_ngoc.clear();", "            case 5: {\n                conn.p.list_thao_kham_ngoc.clear();")
    replace(menu, "            case 7: {\n\n                if (Manager.gI().bossTG.p.isdie)", "            case 6: {\n\n                if (Manager.gI().bossTG.p.isdie)")
    replace(menu, "            case 8: {\n                if (Manager.gI().bossTG.top_dame.size()", "            case 7: {\n                if (Manager.gI().bossTG.top_dame.size()")
    replace(menu, "            case 9: {\n                if (!Manager.gI().bossTG.p.isdie)", "            case 8: {\n                if (!Manager.gI().bossTG.p.isdie)")
    replace(menu, '"Từ cấp 50. Ghép bot ngẫu nhiên cùng nhóm cấp, như 5x hoặc 6x. "',
            '"Cấp 50-139. Nhóm 55-64, 65-74...; cấp 50-54 ghép nhóm đầu. "')

    replace("client/UseItem.java", "            if (temp3.clazz != 4 && temp3.clazz != conn.p.clazz) {",
            "            if (temp3.type != 16 && temp3.clazz != 4 && temp3.clazz != conn.p.clazz) {")
    replace("core/OfflineMarket.java", "                            seller.x = (short) (150 + position * 65);\n                            seller.y = 200;",
            "                            seller.x = (short) new int[]{150, 310, 225, 390, 475}[position];\n                            seller.y = (short) new int[]{200, 240, 290, 190, 275}[position];")
    replace("gamble/TaiXiu.java", '''\t\t\t\t\tManager.gI().chatKTGprocess(
\t\t\t\t\t      "@Server : Tài xỉu mở tại npc Cướp biển ở cánh đồng sói, hãy đến tham gia và bắt đầu trở nên giàu có");
''', "")
    replace("core/ServerManager.java", '"Gặp Zulu để điểm danh offline. Gặp NPC Top BXH để xem xếp hạng."',
            '"Gặp Mrs Oda vào Lôi đài; Mr Ballard vào Chiến trường; khu mua bán có mề đay."')
    replace("core/OfflineTools.java", "public static final int VERSION = 26;",
            "public static final int VERSION = 27;")

    # The original server counted Khải Hoàn without a gem and counted each Hỗn Nguyên socket as a hit.
    player = "client/Player.java"
    replace_between(player, "                // ngoc hon nguyen: 382-386\n", "                // ngoc phong ma: 397-401\n")
    replace_between(player, "                // ngoc khai hoan: 402-406", "                // ngoc luc bao: 407-411")
    replace(player, "    public void process_eff_ngoc_kham(Item3 it, int index) throws IOException {", '''    public int gemHitThreshold(int firstId) {
        int total = 0;
        int count = 0;
        for (Item3 item : this.item.wear) {
            if (item == null) continue;
            for (Option socket : item.op) {
                int socketId = Byte.toUnsignedInt(socket.id);
                int gemId = socket.getParam(0);
                if (socketId >= 58 && socketId <= 60 && gemId >= firstId && gemId < firstId + 5) {
                    total += 25 - (gemId - firstId) * 5;
                    count++;
                }
            }
        }
        return count == 0 ? 0 : total / count;
    }

    public void process_hon_nguyen_hit() throws IOException {
        int required = gemHitThreshold(382);
        if (required == 0 || ++hit_count_ngoc_hon_nguyen < required) return;
        hit_count_ngoc_hon_nguyen = 0;
        if (get_eff(-210) == null) {
            hp = Math.max(1, hp - body.get_max_hp() / 2);
            add_eff(-210, 200, 3000);
        }
    }

    public void process_khai_hoan_hit() throws IOException {
        int required = gemHitThreshold(402);
        if (required == 0 || ++hit_count_ngoc_khai_hoan < required) return;
        hit_count_ngoc_khai_hoan = 0;
        if (get_eff(-211) == null) add_eff(-211, 20, 3000);
    }

    public void process_eff_ngoc_kham(Item3 it, int index) throws IOException {''')
    replace_between(player, "                // ngoc luc bao: 407-411", "            }\n        }\n    }\n\n    public void show_eff_p")
    replace(player, "    public void process_eff_ngoc_kham(Item3 it, int index) throws IOException {", '''    public void process_luc_bao_hit() {
        if (get_eff(-213) != null) return;
        for (Item3 item : this.item.wear) {
            if (item == null) continue;
            for (Option socket : item.op) {
                int socketId = Byte.toUnsignedInt(socket.id);
                int gemId = socket.getParam(0);
                if (socketId >= 58 && socketId <= 60 && gemId >= 407 && gemId <= 411
                        && 100 + (gemId - 406) * 100 > Util.random(1000)) {
                    add_eff(-213, gemId - 406, 3000);
                    return;
                }
            }
        }
    }

    public void process_eff_ngoc_kham(Item3 it, int index) throws IOException {''')
    replace(service, "                // tac dung ngoc kham\n", "                conn.p.process_hon_nguyen_hit();\n                // tac dung ngoc kham\n")
    replace(service, '''                p_target.hit_count_ngoc_khai_hoan++;
                if (p_target.hit_count_ngoc_khai_hoan >= 25) {
                    p_target.hit_count_ngoc_khai_hoan = 0;
                    p_target.add_eff(-211, 20, 3000);
                }''', "                p_target.process_khai_hoan_hit();")
    replace(service, '''            p0.hit_count_ngoc_khai_hoan++;
            if (p0.hit_count_ngoc_khai_hoan >= 25) {
                p0.hit_count_ngoc_khai_hoan = 0;
                p0.add_eff(-211, 20, 3000);
            }''', "            p0.process_khai_hoan_hit();")
    replace(service, "                EffTemplate efLucBao = p_target.get_eff(-213);",
            "                p_target.process_luc_bao_hit();\n                EffTemplate efLucBao = p_target.get_eff(-213);")
    replace(service, "            EffTemplate efLucBao = p0.get_eff(-213);",
            "            p0.process_luc_bao_hit();\n            EffTemplate efLucBao = p0.get_eff(-213);")

    replace("template/OfflineSkins.java", '''        if (OptionItem.entrys.size() == 193) {
            addOption("Xuyên Kháng", 4, 1);
            addOption("Quáng Tuyết", 8, 1);
        }''', '''        if (OptionItem.entrys.size() == 193) {
            addOption("Xuyên Kháng", 4, 1);
            addOption("Quáng Tuyết", 8, 1);
        }
        if (OptionItem.entrys.size() == 195) addOption("Chính xác (chưa kích hoạt)", 8, 0);''')
    replace("template/TinhTu.java", "        id = activeOption(id);\n        if (!active) return id;",
            "        id = activeOption(id);\n        if (!active) return id == 170 ? 195 : id;")
    print(TARGET)


if __name__ == "__main__":
    main()
