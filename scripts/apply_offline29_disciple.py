"""Activate the existing disciple system with a timed, announced child event."""
from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];java=a.source/'src/main/java'
shutil.copy2(root/'shared/src/core/ChildEvent.java',java/'core/ChildEvent.java')
def edit(name,old,new):
    path=java/name;s=path.read_text(encoding='utf-8')
    if s.count(old)!=1:raise ValueError(f'Unexpected source {name}: {old[:80]}')
    path.write_text(s.replace(old,new),encoding='utf-8')
edit('core/ServerManager.java','''        OfflineTools.start();''','''        OfflineTools.start();
        core.ChildEvent.start();''')
path=java/'client/UseItem.java';s=path.read_text(encoding='utf-8')
begin=s.index('            case 220: { // Keo Ho Lo');end=s.index('            case 227:',begin)
s=s[:begin]+'''            case 220: {
                core.ChildEvent.menu(conn.p);break;
            }
'''+s[end:];path.write_text(s,encoding='utf-8')
path=java/'core/MenuController.java';s=path.read_text(encoding='utf-8')
s=s.replace('new String[]{"Nhận Đệ Tử", "Hủy Đệ Tử", "Thông Tin"}','new String[]{"Nhận Đệ Tử", "Hủy Đệ Tử", "Thông Tin", "Tìm Đứa Bé", "Nhận ngay gần Đứa Bé · 50 ngọc"}')
begin=s.index('            case 0: { // Nhan De Tu',s.index('private static void Menu_Mr_Master'))
end=s.index('            case 1:',begin)
s=s[:begin]+'''            case 0: { core.ChildEvent.adopt(conn.p,false);break; }
            case 3: { core.ChildEvent.info(conn.p);break; }
            case 4: { core.ChildEvent.adopt(conn.p,true);break; }
'''+s[end:]
s=s.replace('''        byte idnpc = m.reader().readByte();''','''        byte idnpc = m.reader().readByte();
        if (conn.p.id_dua_be != -1 && (idnpc == -33 || idnpc == -55 || idnpc == -10 || idnpc == -1)) {
            Service.send_notice_box(conn,"Không thể dùng cột dịch chuyển khi đang dẫn Đứa Bé.");return;
        }''',1)
s=s.replace('''        if (conn.p.dungeon != null || Map.is_map_chien_truong(conn.p.map.map_id)) {''','''        if (conn.p.id_dua_be != -1) { Service.send_notice_box(conn,"Không thể về làng nhanh khi đang dẫn Đứa Bé.");return; }
        if (conn.p.dungeon != null || Map.is_map_chien_truong(conn.p.map.map_id)) {''')
path.write_text(s,encoding='utf-8')
edit('core/MenuController.java','''        if (idnpc == 12001) { core.ArenaShop.select(conn.p, Byte.toUnsignedInt(index)); return; }''','''        if (idnpc == 12004) {
            if (index == 0) core.ChildEvent.info(conn.p);
            else if (index == 1) core.ChildEvent.follow(conn.p);
            else if (index == 2) core.ChildEvent.adopt(conn.p,true);
            return;
        }
        if (idnpc == 12001) { core.ArenaShop.select(conn.p, Byte.toUnsignedInt(index)); return; }''')
path=java/'map/MapService.java';s=path.read_text(encoding='utf-8')
s=s.replace('''        String chat = m2.reader().readUTF();''','''        String chat = m2.reader().readUTF();
        if (chat.equalsIgnoreCase("/detu")) { core.ChildEvent.menu(conn.p);return; }''',1)
s=s.replace('''        if (p_target != null && p_target.get_eff(-204) != null) return;''','''        if (mob.template.mob_id == 175) return;
        if (p_target != null && p_target.get_eff(-204) != null) return;''')
anchor='''    private static void fire_mob(Map map, Mob_in_map mob, Player p, byte index_skill, long dame_atk) throws IOException {'''
assert s.count(anchor)==1;s=s.replace(anchor,anchor+'''
        if (mob.template.mob_id == 175) return;''')
s=s.replace('''        if (chat.equalsIgnoreCase("/velang") || chat.equalsIgnoreCase("/vềlàng")) {''','''        if (chat.equalsIgnoreCase("/velang") || chat.equalsIgnoreCase("/vềlàng")) {
            if (conn.p.id_dua_be != -1) { Service.send_notice_box(conn,"Không thể về làng nhanh khi đang dẫn Đứa Bé.");return; }''')
path.write_text(s,encoding='utf-8')
print(a.source.resolve())
