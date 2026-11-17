package core;

import client.Disciple;
import client.Player;
import io.Message;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.Set;
import map.Map;
import map.MapService;
import map.Mob_in_map;
import template.Mob;

/** The offline child event reuses the existing disciple, escort and training systems. */
public final class ChildEvent {
    public static final long LIFETIME=20*60*1000L,RESPAWN=90*60*1000L;
    public static final int INSTANT_COST=50;
    private static final Set<String> MASTER_MAPS=Set.of("bờ biển","nghĩa địa cát","rừng hoa đỏ","đèo băng giá");
    private static Map map;
    private static Mob_in_map child;
    private static Player owner;
    private static long expires,nextSpawn,stealAfter;
    private static boolean started;
    private ChildEvent(){}
    public static synchronized void start(){
        if(started)return;started=true;
        LinkedHashSet<Short> offers=new LinkedHashSet<>();
        for(short id:Manager.gI().itempoitionsell)offers.add(id);
        offers.add(Disciple.ITEM_BUA_GOI_DETU);offers.add(Disciple.ITEM_KEO_HO_LO);offers.add(Disciple.ITEM_VE_LUYEN_DETU);
        Manager.gI().itempoitionsell=new short[offers.size()];int i=0;
        for(short id:offers)Manager.gI().itempoitionsell[i++]=id;
        offline.MapScheduler.schedule(ChildEvent::run,1000);
    }
    private static void run(){
        try{tick(System.currentTimeMillis());}catch(Exception error){System.err.println("Child event: "+error.getMessage());}
        finally{offline.MapScheduler.schedule(ChildEvent::run,1000);}
    }
    public static boolean masterMap(Map value){return value!=null&&MASTER_MAPS.contains(value.name.toLowerCase(java.util.Locale.ROOT));}
    private static void removeWild(){
        if(map==null||child==null)return;
        synchronized(map){map.mobs=Arrays.stream(map.mobs).filter(mob->mob!=child).toArray(Mob_in_map[]::new);}
    }
    private static void addWild(){
        synchronized(map){Mob_in_map[] mobs=Arrays.copyOf(map.mobs,map.mobs.length+1);mobs[mobs.length-1]=child;map.mobs=mobs;}
    }
    private static void removeVisual(Map place)throws IOException{
        if(place==null||child==null)return;Message message=new Message(8);message.writer().writeShort(child.index);
        synchronized(place){for(Player viewer:place.players)viewer.conn.addmsg(message);}
        message.cleanup();
    }
    private static void spawnVisual(Map place,short x,short y)throws IOException{
        Message message=new Message(4);message.writer().writeByte(1);message.writer().writeShort(175);
        message.writer().writeShort(child.index);message.writer().writeShort(x);message.writer().writeShort(y);message.writer().writeByte(-1);
        synchronized(place){for(Player viewer:place.players)viewer.conn.addmsg(message);}
        message.cleanup();
    }
    public static synchronized void tick(long now)throws IOException{
        if(child!=null&&now>=expires){
            Map place=owner==null?map:owner.map;removeVisual(place);removeWild();
            if(owner!=null)owner.id_dua_be=-1;owner=null;child=null;nextSpawn=now;
        }
        if(child!=null&&owner!=null&&(owner.isdie||!owner.conn.connected)){
            Map place=owner.map;removeVisual(place);owner.id_dua_be=-1;
            if(masterMap(place)){owner=null;child=null;nextSpawn=now;}
            else if(place!=null){map=place;child.x=owner.x;child.y=owner.y;owner=null;addWild();spawnVisual(map,child.x,child.y);}
        }
        if(child!=null||now<nextSpawn)return;
        ArrayList<Map> candidates=new ArrayList<>();
        for(Map[] zones:Map.entrys){if(zones.length<1)continue;Map zone=zones[0];
            if(zone.mobs.length>0&&!zone.ismaplang&&zone.ld==null&&zone.d==null&&Map.has_monster(zone.map_id)
                    &&!Map.is_map_cant_save_site(zone.map_id)&&!Map.is_map_chien_truong(zone.map_id))candidates.add(zone);
        }
        if(candidates.isEmpty())return;
        map=candidates.get(Util.random(candidates.size()));Mob_in_map anchor=map.mobs[Util.random(map.mobs.length)];
        child=new Mob_in_map();child.template=Mob.entrys.get(175);child.index=Manager.gI().get_index_mob_new();
        child.x=anchor.x;child.y=anchor.y;child.map_id=map.map_id;child.zone_id=map.zone_id;
        child.level=child.template.level;child.hpmax=child.hp=Math.max(1,child.template.hpmax);child.list_fight=new ArrayList<>();
        child.time_back=Long.MAX_VALUE;expires=now+LIFETIME;stealAfter=0;addWild();spawnVisual(map,child.x,child.y);
        Manager.gI().chatKTGprocess("Đứa Bé đã xuất hiện tại "+map.name+" · Khu "+(map.zone_id+1)+" · ("+child.x+", "+child.y+"). Bé sẽ ở lại 20 phút!");
    }
    private static boolean near(Player player){
        if(child==null)return false;Map place=owner==null?map:owner.map;
        int x=owner==null?child.x:owner.x,y=owner==null?child.y:owner.y;
        return player.map==place&&Math.abs(player.x-x)<150&&Math.abs(player.y-y)<150;
    }
    public static synchronized void info(Player player)throws IOException{
        if(child==null){Service.send_notice_box(player.conn,"Đứa Bé chưa xuất hiện. Sau khi có người nhận, bé khác sẽ xuất hiện sau 90 phút.");return;}
        Map place=owner==null?map:owner.map;
        Service.send_notice_box(player.conn,"Đứa Bé: "+place.name+" · Khu "+(place.zone_id+1)+"\nCòn "+Math.max(0,(expires-System.currentTimeMillis())/60000)+" phút.\nMua kẹo hồ lô tại Lisa, dẫn về Mr Master; hoặc nhận ngay gần bé với 50 ngọc.");
    }
    public static void menu(Player player)throws IOException{
        MenuController.send_menu_select(player.conn,12004,new String[]{"Tìm Đứa Bé","Dắt về Mr Master · 1 kẹo hồ lô","Nhận ngay gần Đứa Bé · 50 ngọc"});
    }
    public static synchronized void follow(Player player)throws IOException{
        long now=System.currentTimeMillis();
        if(player.detu!=null||player.id_dua_be!=-1){Service.send_notice_box(player.conn,"Bạn đã có đệ tử hoặc đang dẫn Đứa Bé.");return;}
        if(!near(player)||now>=expires){Service.send_notice_box(player.conn,"Hãy đến gần Đứa Bé còn đang xuất hiện.");return;}
        if(player.pet_di_buon!=null||player.typepk>=11&&player.typepk<=13){Service.send_notice_box(player.conn,"Hãy kết thúc đi buôn trước khi dẫn Đứa Bé.");return;}
        if(owner!=null){
            if(masterMap(player.map)){Service.send_notice_box(player.conn,"Không thể dụ Đứa Bé ở bản đồ có Mr Master.");return;}
            if(now<stealAfter){Service.send_notice_box(player.conn,"Chờ đủ 10 giây giữa hai lần dụ Đứa Bé.");return;}
            if(player.get_ngoc()<1){Service.send_notice_box(player.conn,"Cần 1 ngọc để dụ Đứa Bé.");return;}
            owner.id_dua_be=-1;player.update_ngoc(-1);
        }else{
            if(player.item.total_item_by_id(4,Disciple.ITEM_KEO_HO_LO)<1){Service.send_notice_box(player.conn,"Cần 1 kẹo hồ lô mua ở Lisa.");return;}
            player.item.remove(4,Disciple.ITEM_KEO_HO_LO,1);removeWild();
        }
        owner=player;player.id_dua_be=(short)child.index;stealAfter=now+10000;spawnVisual(player.map,player.x,player.y);
        player.item.char_inventory(4);Service.send_notice_box(player.conn,"Đứa Bé đi theo bạn. Còn "+Math.max(0,(expires-now)/60000)+" phút để dẫn về Mr Master.");
    }
    public static synchronized void adopt(Player player,boolean immediate)throws IOException{
        if(player.detu!=null){Service.send_notice_box(player.conn,"Bạn đã có Đệ Tử.");return;}
        if(child==null||System.currentTimeMillis()>=expires){Service.send_notice_box(player.conn,"Đứa Bé đã rời đi. Hãy tìm bé mới.");return;}
        if(immediate){
            if(!near(player)||owner!=null&&owner!=player){Service.send_notice_box(player.conn,"Hãy đến gần Đứa Bé chưa có chủ, hoặc bé đang đi theo bạn.");return;}
            if(player.get_ngoc()<INSTANT_COST){Service.send_notice_box(player.conn,"Cần 50 ngọc để nhận Đứa Bé ngay.");return;}
            player.update_ngoc(-INSTANT_COST);
        }else if(owner!=player||!masterMap(player.map)){Service.send_notice_box(player.conn,"Dẫn Đứa Bé về Mr Master ở Bờ Biển, Nghĩa Địa Cát, Rừng Hoa Đỏ hoặc Đèo Băng Giá.");return;}
        removeVisual(owner==null?map:owner.map);removeWild();player.id_dua_be=-1;
        player.detu=Disciple.createNew(player,(byte)Util.random(4));player.flush();
        child=null;owner=null;nextSpawn=System.currentTimeMillis()+RESPAWN;
        Manager.gI().chatKTGprocess(player.name+" đã thu nhận Đệ Tử!");
        Service.send_notice_box(player.conn,"Đã nhận Đệ Tử cấp 10. Gặp Oda để luyện; mua bùa gọi đệ tử tại Lisa.");
    }
}
