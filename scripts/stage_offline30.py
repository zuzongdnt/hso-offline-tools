"""Stage restored-account selection, native ranked challenges and activity entry fixes."""
import argparse
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.out.exists():p.error('Choose an unused output directory.')
shutil.copytree(a.source/'src',a.out/'src');shutil.copy2(a.source/'pom.xml',a.out/'pom.xml')
java=a.out/'src/main/java'
for name in ['OfflineLogin','OfflineTools','ArenaRoster','SocketGems','CombatVisuals','MazeRun','MedalProfiles']:
    text=(root/f'shared/src/core/{name}.java').read_text(encoding='utf-8').replace('VERSION = 26;','VERSION = 30;')
    (java/f'core/{name}.java').write_text(text,encoding='utf-8')
def edit(name,old,new,count=1):
    path=java/name;text=path.read_text(encoding='utf-8')
    if text.count(old)!=count:raise ValueError(f'Unexpected {name}: {old[:80]}')
    path.write_text(text.replace(old,new),encoding='utf-8')

edit('io/Session.java','user_ = core.OfflineLogin.resolve(lookup,user_,pass_);','var restored = core.OfflineLogin.credentials(lookup,user_,pass_); user_ = restored.user(); pass_ = restored.pass();')
edit('io/Session.java','''        if (pass_.equals("1") && user_.equals("1")) {''','''        try(Connection lookup=SQL.gI().getConnection()){
            var restored=core.OfflineLogin.credentials(lookup,user_,pass_);user_=restored.user();pass_=restored.pass();
        }catch(SQLException error){noticelogin("Chưa đọc được tài khoản khôi phục.");return;}
        if (pass_.equals("1") && user_.equals("1")) {''')
edit('core/OfflineMarket.java','''        return item;''','''        core.MedalProfiles.generated(item);
        return item;''',count=2)
edit('template/OfflineSkins.java','''        if (item.type == 16) item.clazz = 4;''','''        if (item.type == 16) item.clazz = 4;
        core.MedalProfiles.refresh(item);''')
edit('client/UseItem.java','''    public static void ProcessItem4(Session conn, Message m2) throws IOException {
        short id = m2.reader().readShort();''','''    public static void ProcessItem4(Session conn, Message m2) throws IOException {
        short id = m2.reader().readShort();
        if(id==332){Service.send_notice_box(conn,"Hổ lửa đã ngừng sử dụng. Vật phẩm vẫn được giữ trong túi.");return;}''')
edit('client/Player.java','    public void change_map(Player p, Vgo vgo) throws IOException {','''    public core.MazeRun maze;
    public void change_map(Player p, Vgo vgo) throws IOException {
        if(p.maze!=null && p.maze.transition(vgo))return;''')
edit('map/Map.java','''return id == 48 ||''','''return (id>=74 && id<=79) || id == 48 ||''')
edit('client/UseItem.java','''        if(id==332){Service.send_notice_box(conn,"Hổ lửa đã ngừng sử dụng. Vật phẩm vẫn được giữ trong túi.");return;}
        if (conn.p.item''','''        if(id==332){Service.send_notice_box(conn,"Hổ lửa đã ngừng sử dụng. Vật phẩm vẫn được giữ trong túi.");return;}
        if(conn.p.map.ld!=null&&conn.p.map.ld.challengeRank>0&&id>=0&&id<ItemTemplate4.item.size()&&ItemTemplate4.item.get(id).getType()==44)return;
        if (conn.p.item''')
edit('template/Item3.java','(socketOption == 80 || socketOption == 82)','(socketOption == 80 || socketOption == 82 || socketOption == 87)')
edit('template/Item3.java','''        int socketOption = Byte.toUnsignedInt(option.id);''','''        int socketOption = Byte.toUnsignedInt(option.id);
        if(socketOption==87 && option.getParam(0)>0)return Math.max(1500,option.getParam(0));''')
edit('map/Map.java','for (Mob_in_map mob : this.mobs) {','for (Mob_in_map mob : this.mobs) { if(mob.confusedUntil>System.currentTimeMillis())continue;')
edit('map/Mob_in_map.java','public int index;','public int index; public long confusedUntil;')
edit('map/MapService.java','p0.show_eff_p(13, 1000);','p0.show_eff_p(24, dur);')
edit('map/MapService.java','p.show_eff_p(13, 1000);','core.CombatVisuals.mob(p,mob,24,p.body.get_effect_duration(88,3000));')

edit('client/UseItem.java','''    private static void use_item4_default(Session conn, short id) throws IOException {''','''    private static void use_item4_default(Session conn, short id) throws IOException {        if(id==332){Service.send_notice_box(conn,"Hổ lửa đã ngừng sử dụng. Vật phẩm vẫn được giữ trong túi.");return;}
        if(id==241||id==243){core.MazeRun.enter(conn.p,id);return;}
        if(id==242){core.MazeRun.openLamp(conn.p);return;}
        if(conn.p.map.ld!=null && conn.p.map.ld.challengeRank>0 && id>=0 && id<template.ItemTemplate4.item.size()){
            int type=template.ItemTemplate4.item.get(id).getType();
            if(type<=5||type==25||type==44){Service.send_notice_box(conn,"Top thi đấu không sử dụng HP, MP hoặc thú cưỡi.");return;}
        }
''' )
edit('core/MenuController.java','''        if (idnpc == 12002)''','''        if (idnpc == 12005) { if(conn.p.maze!=null){if(index==0)conn.p.maze.claim();else conn.p.maze.leave("Đã rời mê cung.");}return; }
        if (idnpc == 12002)''')
edit('map/MapService.java','''        if (chat.equalsIgnoreCase("/velang") || chat.equalsIgnoreCase("/vềlàng")) {''','''        if(chat.equals("/mecung")){core.MazeRun.menu(conn.p);return;}
        if(chat.equals("/velang")&&conn.p.maze!=null){conn.p.maze.leave("Đã rời mê cung.");return;}
        if (chat.equalsIgnoreCase("/velang") || chat.equalsIgnoreCase("/vềlàng")) {''')
edit('client/MessageHandler.java','''            case 49: {''','''            case -101: {
                int action=m.reader().readUnsignedByte();String name=m.reader().readUTF();
                if(action==0)core.ArenaRoster.challenge(conn.p,name);break;
            }
            case 49: {''')
edit('core/Service.java','''        if (type == 0) { // xem thong tin other''','''        if (type == 0 || type == 100) { // native ranked-challenge inspection''')
edit('template/OfflineSkins.java','''        return java.util.Collections.unmodifiableSet(mounts.keySet());''','''        return mounts.keySet().stream().filter(id->id!=332).collect(java.util.stream.Collectors.toUnmodifiableSet());''')
edit('core/Service.java','''    public static void send_char_main_in4(Player p) throws IOException {''','''    public static void send_char_main_in4(Player p) throws IOException {
        if(p.id_horse==220){p.type_use_mount=-1;p.id_horse=-1;}
        template.RankBadge.sync(p);''')

edit('template/RankBadge.java','''    public static void setRank(Player player, int rank) {''','''    public static void sync(Player player) {
        ensureSave(player);int points=player.point_active[2];
        if(player.point_active[3]==3){player.point_active[4]=0;player.point_active[3]=0;}
        int rank=points>=2520?5:points>=1680?4:points>=1260?3:points>=840?2:points>0?1:0;
        player.point_active[4]=Math.max(player.point_active[4],rank);
    }
    public static void setRank(Player player, int rank) {''')
edit('template/RankBadge.java','''    public static int effect(Player player) {''','''    public static int effect(Player player) {
        sync(player);''')
edit('event_daily/LoiDai.java','''    private boolean finished;''','''    private boolean finished;
    public int challengeRank;
    private long challengeDeadline;
    private byte previousMount;
    private short previousHorse;
    private boolean previousPet;
    public static void startChallenge(Player player,Player bot,int target)throws IOException {
        start(player,bot);
        if(player.map.ld==null)return;
        LoiDai match=player.map.ld;match.challengeRank=target;match.challengeDeadline=System.currentTimeMillis()+300000;
        match.previousMount=player.type_use_mount;match.previousHorse=player.id_horse;match.previousPet=player.pet_follow;
        player.type_use_mount=-1;player.id_horse=-1;player.pet_follow=false;
        bot.pet_follow=false;bot.mypet.clear();player.map.send_mount(player);
    }''')
edit('event_daily/LoiDai.java','''        if (player.level < 50 || player.level > 139) {''','''        if (player.level < (selectedBot==null?50:39) || player.level > 139) {''')
edit('event_daily/LoiDai.java','''        int time = secondsLeft();''','''        if(challengeRank>0&&!finished&&System.currentTimeMillis()>=challengeDeadline){losses=2;finish();return;}
        int time = secondsLeft();''')
edit('event_daily/LoiDai.java','''        int delta = wins > losses ? 30''','''        if(challengeRank>0){
            core.ArenaRoster.result(p1,challengeRank,wins>losses);finished=true;state_ld=2;setTimer(5);
            Service.send_notice_box(p1.conn,(wins>losses?"Thắng thách đấu. Hạng của bạn: "+core.ArenaRoster.rank(p1):"Thua thách đấu. Thứ hạng được giữ nguyên.")+" Không tính điểm Lôi đài.");return;
        }
        int delta = wins > losses ? 30''')
edit('event_daily/LoiDai.java','''        p1.point_active[2] += delta;''','''        p1.point_active[2] += delta;
        template.RankBadge.sync(p1);template.RankBadge.send(p1,p1);p1.flush();''')
edit('event_daily/LoiDai.java','''        player.typepk = -1;''','''        if(challengeRank>0){player.type_use_mount=previousMount;player.id_horse=previousHorse;player.pet_follow=previousPet;}
        player.typepk = -1;''')
edit('event_daily/LoiDai.java','''message.writer().writeUTF((finished ? "Kết thúc Lôi đài" : "Lôi đài · Hiệp " + round)''','''message.writer().writeUTF((finished ? "Kết thúc trận" : (challengeRank>0?"Thách đấu · Hiệp ":"Lôi đài · Hiệp ") + round)''')

# Keep the existing four-faction maps, houses, guards and score processing.
edit('core/MenuController.java','''ChienTruong.gI().getStatus() == 1''','''ChienTruong.gI().getStatus() >= 0''',count=2)
path=java/'core/MenuController.java';text=path.read_text(encoding='utf-8');a0=text.index('            case 998: {');a1=text.index('            case -53:',a0)
chunk=text[a0:a1].replace('case 998: {','case 998: {\n                if(conn.p.level<40){Service.send_notice_box(conn,\"Cần cấp 40 để đăng ký.\");return;}').replace('1_000_000','500_000').replace('1.000.000','500.000').replace('500 ngọc','2 ngọc').replace('get_ngoc() < 500','get_ngoc() < 2').replace('update_ngoc(-500)','update_ngoc(-2)')
text=text[:a0]+chunk+text[a1:];text=text.replace('"Đăng ký bằng 1.000.000 vàng", "Đăng ký bằng 500 ngọc"','"Đăng ký bằng 500.000 vàng", "Đăng ký bằng 2 ngọc"')
start=text.index('    private static void Menu_Mr_Ballard');idx=text.index('                if (ChienTruong.gI().getStatus() == 2)',start)
text=text[:idx]+'''                if(conn.p.level<40){Service.send_notice_box(conn,"Cần cấp 40 để tham gia chiến trường.");return;}
                if(ChienTruong.gI().getStatus()==1&&ChienTruong.gI().get_infor_register(conn.p.name)!=null){ChienTruong.gI().close_and_start();return;}
'''+text[idx:];path.write_text(text,encoding='utf-8')
path=java/'event_daily/ChienTruong.java';text=path.read_text(encoding='utf-8');start=text.index('\t\t\tif (list.size() < 4) {');end=text.index('\n\t\t\t// for (int mem',start);text=text[:start]+text[end:]
text=text.replace('''\tpublic synchronized void register(Player p, int type) throws IOException {''','''\tpublic synchronized void register(Player p, int type) throws IOException {
        if(p.level<40){Service.send_notice_box(p.conn,"Cần cấp 40 để đăng ký.");return;}
        if(status==0)open_register();''')
text=text.replace('temp.village = 0;','''temp.village = 0;
            if(status==2){int[] counts=new int[4];for(Member_ChienTruong member:list.values())if(member.village>=2&&member.village<=5)counts[member.village-2]++;
                int smallest=0;for(int i=1;i<4;i++)if(counts[i]<counts[smallest])smallest=i;temp.village=smallest+2;}''')
text=text.replace('this.vang += 800000','this.vang += 500000').replace('this.ngoc += 450','this.ngoc += 2');path.write_text(text,encoding='utf-8')
edit('map/Npc.java','Chiến trường bắt đầu vào 21h30 phút hàng ngày','Chiến trường offline mở bất cứ lúc nào tại Mr Ballard')
print(a.out.resolve())
