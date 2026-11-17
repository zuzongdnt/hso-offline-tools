package core;

import client.Player;
import io.Message;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import map.Map;
import map.MapService;
import map.Mob_in_map;
import map.Vgo;
import template.Item47;

/** Private five-minute route through the native maze rooms. */
public final class MazeRun {
    public static final long LIMIT=300_000L;
    public final Player player;
    public final Map[] rooms=new Map[6];
    public long deadline;
    private final Map home;
    private final short homeX,homeY;
    private int room;
    private boolean ended;
    private MazeRun(Player p)throws IOException{
        player=p;home=p.map;homeX=p.x;homeY=p.y;deadline=System.currentTimeMillis()+LIMIT;
        List<Integer> ids=new ArrayList<>(List.of(74,75,76,77,78,79));Collections.shuffle(ids);
        for(int i=0;i<rooms.length;i++){
            Map base=Map.get_map_by_id(ids.get(i))[0];
            List<Vgo> doors=new ArrayList<>();
            for(Vgo old:base.vgos){Vgo door=new Vgo();door.x_old=old.x_old;door.y_old=old.y_old;
                door.x_new=old.x_new;door.y_new=old.y_new;door.name_map_go="Lối đi mê cung";doors.add(door);}
            Map copy=new Map(base.map_id,0,base.npc_name_data,"Vượt mê cung",base.typemap,false,base.showhs,15,1,doors);
            copy.mobs=new Mob_in_map[base.mobs.length];
            for(int j=0;j<copy.mobs.length;j++){
                Mob_in_map src=base.mobs[j],mob=new Mob_in_map();mob.template=src.template;
                mob.index=Manager.gI().get_index_mob_new();mob.x=src.x;mob.y=src.y;mob.level=src.level;
                mob.hp=mob.hpmax=src.hpmax;mob.map_id=copy.map_id;mob.zone_id=0;mob.list_fight=new ArrayList<>();
                mob.time_back=Long.MAX_VALUE;copy.mobs[j]=mob;
            }
            rooms[i]=copy;
        }
        for(int i=0;i<rooms.length;i++)for(int d=0;d<rooms[i].vgos.size();d++){
            int next=d==0?Math.max(0,i-1):Math.min(5,i+1);
            Vgo door=rooms[i].vgos.get(d);door.id_map_go=rooms[next].map_id;
            door.x_new=rooms[next].vgos.get(0).x_old;door.y_new=(short)(rooms[next].vgos.get(0).y_old+30);
        }
    }
    public static void enter(Player p,short ticket)throws IOException{
        synchronized(p){
            if(ticket==243){
                if(p.item.total_item_by_id(4,243)<1)return;
                int count=p.item.total_item_by_id(4,241);
                if(count>31990||(count==0&&p.item.get_bag_able()<1)){Service.send_notice_box(p.conn,"Cần chỗ trống để mở gói 10 vé.");return;}
                Item47 pack=new Item47();pack.category=4;pack.id=241;pack.quantity=10;
                p.item.remove(4,ticket,1);p.item.add_item_bag47(4,pack);p.item.char_inventory(4);p.flush();
                Service.send_notice_box(p.conn,"Đã mở gói thành 10 Vé vào mê cung. Dùng từng vé để tham gia.");return;
            }
            if(p.level<20){Service.send_notice_box(p.conn,"Cần cấp 20 để vượt mê cung.");return;}
            if(p.maze!=null||p.isdie||p.dungeon!=null||p.map.ld!=null||Map.is_map_chien_truong(p.map.map_id)
                    ||p.id_dua_be!=-1||p.pet_di_buon!=null){Service.send_notice_box(p.conn,"Hãy kết thúc hoạt động hiện tại trước khi vượt mê cung.");return;}
            if(p.item.total_item_by_id(4,ticket)<1)return;
            MazeRun run=new MazeRun(p);p.maze=run;
            p.item.remove(4,ticket,1);
            try{run.move(0,run.rooms[0].vgos.get(0));}
            catch(Exception error){run.leave("Không mở được mê cung. Vé đã được hoàn lại.");Item47 refund=new Item47();refund.id=ticket;refund.quantity=1;p.item.add_item_bag47(4,refund);p.item.char_inventory(4);return;}
            offline.MapScheduler.schedule(run::tick,1000);
        }
    }
    private void move(int destination,Vgo entry)throws IOException{
        MapService.leave(player.map,player);room=destination;player.map=rooms[room];
        player.x=entry.x_new;player.y=entry.y_new;player.is_changemap=false;
        MapService.enter(player.map,player);player.map.start_map();timer();
        if(room==5)menu(player);
    }
    public synchronized boolean transition(Vgo door)throws IOException{
        if(ended)return false;
        for(Mob_in_map mob:player.map.mobs)if(!mob.isdie&&mob.hp>0&&(mob.template.mob_id==149||mob.template.mob_id==155)){
            Service.send_notice_box(player.conn,"Tiêu diệt thần canh cửa trước khi qua cửa.");return true;
        }
        for(int i=0;i<rooms.length;i++)if(rooms[i].map_id==door.id_map_go){move(i,door);return true;}
        leave("Đã rời mê cung.");return true;
    }
    public static void menu(Player p)throws IOException{
        if(p.maze==null){Service.send_notice_box(p.conn,"Dùng Vé vào mê cung trong hành trang để tham gia.");return;}
        MenuController.send_menu_select(p.conn,12005,new String[]{"Nhặt Đèn Thần","Rời mê cung"});
    }
    public synchronized void claim()throws IOException{
        if(ended||room!=5||System.currentTimeMillis()>=deadline){Service.send_notice_box(player.conn,"Hãy tìm phòng kho báu trước khi hết 5 phút.");return;}
        if(player.item.get_bag_able()<1){Service.send_notice_box(player.conn,"Cần một ô trống để nhận Đèn Thần.");return;}
        Item47 lamp=new Item47();lamp.id=242;lamp.quantity=1;lamp.category=4;
        player.item.add_item_bag47(4,lamp);player.item.char_inventory(4);player.flush();leave("Đã tìm được Đèn Thần! Dùng đèn trong hành trang để nhận quà.");
    }
    public synchronized void leave(String notice)throws IOException{
        if(ended)return;ended=true;
        for(Map map:rooms)map.stop_map();MapService.leave(player.map,player);player.maze=null;
        player.map=home;player.x=homeX;player.y=homeY;player.is_changemap=false;
        if(player.conn.connected){MapService.enter(home,player);Service.send_notice_box(player.conn,notice);}
        player.flush();
    }
    private void tick(){
        try{
            if(ended)return;
            if(!player.conn.connected||player.isdie||System.currentTimeMillis()>=deadline){leave("Lượt vượt mê cung kết thúc.");return;}
            for(Map map:rooms)for(Mob_in_map mob:map.mobs)if(mob.isdie)mob.time_back=Long.MAX_VALUE;
            timer();offline.MapScheduler.schedule(this::tick,1000);
        }catch(Exception error){System.err.println("Maze: "+error.getMessage());try{leave("Mê cung đã đóng, vé được hoàn lại.");Item47 ticket=new Item47();ticket.id=241;ticket.quantity=1;player.item.add_item_bag47(4,ticket);}catch(Exception ignored){}}
    }
    private void timer()throws IOException{
        Message m=new Message(-104);m.writer().writeByte(1);m.writer().writeByte(1);
        m.writer().writeShort(Math.max(0,(int)((deadline-System.currentTimeMillis())/1000)));
        m.writer().writeUTF("Vượt mê cung · "+(room==5?"Kho báu":"Tìm Đèn Thần"));player.conn.addmsg(m);m.cleanup();
    }
    public static void openLamp(Player p)throws IOException{
        synchronized(p){
            if(p.item.total_item_by_id(4,242)<1)return;
            if(p.item.get_bag_able()<1){Service.send_notice_box(p.conn,"Cần một ô trống để mở Đèn Thần.");return;}
            short[] ids={18,142,222};short id=ids[Util.random(ids.length)];int amount=3+Util.random(3);
            if(p.item.total_item_by_id(4,id)+amount>32000){Service.send_notice_box(p.conn,"Vật phẩm thưởng đã đầy số lượng, hãy cất bớt trước khi mở đèn.");return;}
            Item47 gift=new Item47();gift.category=4;gift.id=id;gift.quantity=(short)amount;
            p.item.remove(4,(short)242,1);p.item.add_item_bag47(4,gift);p.update_Exp(p.level*1000L,false);
            p.item.char_inventory(4);p.flush();Service.send_notice_box(p.conn,"Đèn Thần: "+amount+" "+template.ItemTemplate4.item.get(id).getName()+" và kinh nghiệm.");
        }
    }
}
