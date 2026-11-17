"""Correct socket statistics, native effect packets and all three medal-material tiers."""
import argparse
from pathlib import Path
import re
import shutil

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
java=a.source/'src/main/java'
for name in ['SocketGems','CombatVisuals']:
    shutil.copy2(root/f'shared/src/core/{name}.java',java/f'core/{name}.java')
def edit(name,old,new):
    path=java/name;text=path.read_text(encoding='utf-8')
    if text.count(old)!=1:raise ValueError(f'Unexpected source {name}: {old[:90]}')
    path.write_text(text.replace(old,new),encoding='utf-8')

edit('template/Item3.java','''    public int optionValue(Option option) {''','''    public int optionValue(Option option) {
        int socketOption = Byte.toUnsignedInt(option.id);
        if (socketOption >= 100 && socketOption <= 108) return core.SocketGems.value(this,socketOption);
        if (type == 16 && (socketOption == 80 || socketOption == 82) && option.getParam(0) > 0)
            return Math.max(1500,option.getParam(0));''')
edit('template/Item3.java','''\tpublic void writeItemOptions(Message m, byte playerClazz, boolean activeSet) throws IOException {''','''\tpublic void writeItemOptions(Message m, byte playerClazz, boolean activeSet) throws IOException {
        core.SocketGems.rebuild(this);''')
edit('template/OfflineSkins.java','''        if (item.type == 16) item.clazz = 4;''','''        if (item.type == 16) item.clazz = 4;
        core.SocketGems.rebuild(item);''')
edit('template/ItemSellCoin.java','''        for (short id : LEVEL5_GEMS) {''','''        for (ItemTemplate7 material : ItemTemplate7.item) {
            if (material.getType() != 54) continue;
            material.setPrice(1); material.setPricetype((byte)0);
            material.setContent("Nguyên liệu dùng chế tạo mề đay");
            materials.add(material.getId());
        }
        for (short id : LEVEL5_GEMS) {''')
path=java/'core/GameSrc.java';text=path.read_text(encoding='utf-8')
start=text.index('                        int param = Util.random(1, 10);',text.index('int index_ngoc_kham_vao'))
finish=text.index('                            case 23:',start)
text=text[:start]+'''                        switch (id_g1) {
'''+text[finish:]
anchor='''                        m.writer().writeByte(3);
                        m.writer().writeUTF("Thành công, chúc mừng");'''
success=text.index(anchor,start)
text=text[:success]+'''                        core.SocketGems.rebuild(it3);
'''+text[success:]
path.write_text(text,encoding='utf-8')

path=java/'client/Player.java';text=path.read_text(encoding='utf-8')
begin=text.index('    public int gemHitThreshold(int firstId) {')
end=text.index('    public synchronized static void update_coin',begin)
text=text[:begin]+'''    public int gemHitThreshold(int firstId) { return core.SocketGems.threshold(this,firstId); }
    public void process_hon_nguyen_hit() throws IOException { core.SocketGems.hon(this); }
    public void process_khai_hoan_hit() throws IOException { core.SocketGems.khai(this); }
    public void process_luc_bao_hit() { core.SocketGems.absorb(this); }
    public void process_eff_ngoc_kham(Item3 item,int index) throws IOException { }
    public void show_eff_p(int effect,int time) throws IOException { core.CombatVisuals.show(this,effect,time); }

'''+text[end:]
anchor='''    public void add_eff(int id, int param, int time) {
'''
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''        if (core.SocketGems.DEBUFFS.contains(id) && get_eff(-211) != null) return;
        if (id == 2 && get_eff(-216) != null) return;
''')
path.write_text(text,encoding='utf-8')

path=java/'client/Body.java';text=path.read_text(encoding='utf-8')
text=text.replace('if (matches && op.getParam(temp.tier) > maxParam)', 'if (matches && temp.optionValue(op) > maxParam)')
text=text.replace('maxParam = op.getParam(temp.tier);','maxParam = temp.optionValue(op);')
for method,variable in [('get_pierce','pie'),('get_react_dame','param'),('get_miss','param'),('get_crit','crit')]:
    start=text.index(f'    public int {method}() {{');end=text.index('\n    }',start)
    block=text[start:end];old=f'return {variable};';assert block.count(old)==1
    block=block.replace(old,f'return core.SocketGems.resistancePenalty(p,{variable});')
    text=text[:start]+block+text[end:]
path.write_text(text,encoding='utf-8')

path=java/'map/MapService.java';text=path.read_text(encoding='utf-8')
start=text.index('                conn.p.process_hon_nguyen_hit();')
end=text.index('                int upgrade =',start)
text=text[:start]+text[end:]
text=text.replace('''        if (dame > 0 && p0.hp > 0) {
            p0.process_luc_bao_hit();''','''        if (dame > 0 && p0.hp > 0) {
            core.SocketGems.defend(p0);''')
text=text.replace('''                p_target.process_luc_bao_hit();''','''                core.SocketGems.defend(p_target);''')
text=text.replace('''                p0.hp += heal;''','''                p0.hp = Math.min(p0.body.get_max_hp(),p0.hp+heal);''')
text=text.replace('''                    p_target.hp += heal;''','''                    p_target.hp = Math.min(p_target.body.get_max_hp(),p_target.hp+heal);''')
text=text.replace('p0.hp = Math.min(p0.body.get_max_hp(),p0.hp+heal);','dame = Math.max(0,dame-heal);')
text=text.replace('p_target.hp = Math.min(p_target.body.get_max_hp(),p_target.hp+heal);','dmob = (int)Math.max(0,dmob-heal);')
text=text.replace('''            p0.process_khai_hoan_hit();''','''            // Counted once by SocketGems.defend.''')
text=text.replace('''                p_target.process_khai_hoan_hit();''','''                // Counted once by SocketGems.defend.''')
anchor='''        // === EFFECT CHECKS ==='''
assert text.count(anchor)==1
text=text.replace(anchor,'''        dame = core.SocketGems.attackDamage(p,dame,true,false);
'''+anchor)
anchor='''        mob.hp -= dame;'''
assert text.count(anchor)==1
text=text.replace(anchor,'''        dame = core.SocketGems.attackDamage(p,dame,mob.is_boss,true);
'''+anchor)
text=re.sub(r'\((\w+) >= 100 \|\| \1 > Util\.random\(10000\)\)',r'TinhTu.rolls(\1)',text)
text=text.replace('show_eff_p(17, 1000)','show_eff_p(17, dur)')
anchor='''        if (mob.template.mob_id >= 89 && mob.template.mob_id <= 92) {'''
assert text.count(anchor)>=1
text=text.replace(anchor,'''        if (p_target != null && p_target.get_eff(-204) != null) return;
'''+anchor,1)
anchor='''        if (p0 == null || p0.id == p.id || p.map.map_id == 82'''
assert text.count(anchor)==1
text=text.replace(anchor,'''        if (p0 != null && p0.get_eff(-204) != null) return;
'''+anchor)
anchor='''    public static void send_in4_other_char(Map map, Player p, Player p0) throws IOException {'''
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''
        if (p.id != p0.id && p0.get_eff(-204) != null) return;''')
text=text.replace('''        if (crit) {
            dame *= 2;
        }''','''        if (crit) {
            dame = dame * (20000L + p.body.total_item_param(107)) / 10000;
        }''')
path.write_text(text,encoding='utf-8')

edit('core/Service.java','''    public static void usepotion(Player p, int type, long param) throws IOException {''','''    public static void usepotion(Player p, int type, long param) throws IOException {
        if (type == 0 && param > 0 && p.get_eff(-216) != null) return;''')

edit('core/MenuController.java','''send_menu_select(conn, 130, new String[]{"Thông Tin Tài Khoản", "Thông Tin Bản Thân"});''','''send_menu_select(conn, 130, new String[]{"Thông Tin Tài Khoản", "Thông Tin Bản Thân", "Về làng nhanh"});''')
edit('core/MenuController.java',''' private static void Menu_Thongtincanhan(Session conn, byte index) throws IOException {
''',''' private static void Menu_Thongtincanhan(Session conn, byte index) throws IOException {
    if (index == 2) {
        if (conn.p.map.ld != null) { conn.p.map.ld.leave(conn.p); return; }
        if (conn.p.dungeon != null || Map.is_map_chien_truong(conn.p.map.map_id)) {
            Service.send_notice_box(conn,"Hãy rời trận hoặc phó bản trước khi về làng.");return;
        }
        Vgo home = new Vgo(); home.id_map_go=1;home.x_new=528;home.y_new=480;
        conn.p.change_map(conn.p,home);return;
    }
''')

path=java/'map/Map.java';text=path.read_text(encoding='utf-8')
text=text.replace('''if (temp.id == 2) {
                                p.hp += p.hp_restore;''','''if (temp.id == 2 && p.get_eff(-216) == null) {
                                p.hp += p.hp_restore;''')
text=text.replace('''|| temp.id == -211 || temp.id == -212 || temp.id == -213''','''|| temp.id == -211 || temp.id == -212 || temp.id == -213 || temp.id == -214 || temp.id == -215 || temp.id == -216''')
path.write_text(text,encoding='utf-8')
print(a.source.resolve())
