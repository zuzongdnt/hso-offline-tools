package core;

import client.Player;
import event_daily.LoiDai;
import io.Message;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public final class ArenaRoster {
    private static final List<Player> bots = new ArrayList<>();
    private static final java.util.Map<Integer,Integer> pages = new java.util.concurrent.ConcurrentHashMap<>();
    private static final java.util.Map<Integer,Integer> selected = new java.util.concurrent.ConcurrentHashMap<>();
    private static synchronized void init(Player viewer) throws IOException {
        if (!bots.isEmpty()) return;
        for (int level = 55; level <= 135; level += 10) {
            io.Session session = new io.Session(null);
            Player model = new Player(session, 31900); model.level = (short) level;
            for (int i = 0; i < 5; i++) {
                Player bot = LoiDai.createOpponent(model, 31000 + bots.size(), level + i);
                bot.name = new String[]{"Thiên Vũ", "Hàn Phong", "Bạch Nguyệt", "Lạc Vũ", "Xích Long"}[i] + " " + bot.level + " [Bot]";
                bots.add(bot);
            }
        }
        bots.sort(java.util.Comparator.comparingInt((Player bot) -> bot.level).reversed());
    }
    public static synchronized Player find(String name) {
        return bots.stream().filter(bot -> bot.name.equalsIgnoreCase(name)).findFirst().orElse(null);
    }
    private static void saveSlots(Player p){
        if(p.point_active==null)p.point_active=new int[12];
        else if(p.point_active.length<12)p.point_active=java.util.Arrays.copyOf(p.point_active,12);
    }
    public static int rank(Player p){saveSlots(p);return p.point_active[7]>0?Math.min(46,p.point_active[7]):46;}
    public static void result(Player p,int target,boolean won)throws IOException{
        saveSlots(p);
        if(won){p.point_active[7]=Math.min(rank(p),target);p.point_active[8]=0;p.point_active[9]=0;p.point_active[10]=0;}
        else{p.point_active[8]=1;p.point_active[9]=(int)(System.currentTimeMillis()/1000);p.point_active[10]=target;}
        p.flush();
    }
    public static void ranking(Player p)throws IOException{show(p,0);}
    public static void show(Player p,int page)throws IOException{
        init(p);int mine=rank(p);
        Message packet=new Message(56);packet.writer().writeByte(6);
        packet.writer().writeUTF("Top thi đấu · Hạng của bạn: "+mine);packet.writer().writeByte(99);
        packet.writer().writeInt(mine);packet.writer().writeByte(bots.size()+1);
        int botIndex=0;
        for(int place=1;place<=bots.size()+1;place++){
            Player actor=place==mine?p:bots.get(botIndex++);
            packet.writer().writeUTF(actor.name);packet.writer().writeByte(actor.head);
            packet.writer().writeByte(actor.eye);packet.writer().writeByte(actor.hair);packet.writer().writeShort(actor.level);
            List<template.Item3> gear=new ArrayList<>();
            for(int slot:new int[]{0,1,6,7,10})if(actor.item.wear[slot]!=null)gear.add(actor.item.wear[slot]);
            packet.writer().writeByte(gear.size());
            for(template.Item3 item:gear){packet.writer().writeByte(item.part);packet.writer().writeByte(item.type);}
            packet.writer().writeByte(1);packet.writer().writeUTF("Hạng "+place+(place==mine?" · Bạn":" · Đang online"));
            packet.writer().writeShort(-1);
        }
        p.conn.addmsg(packet);packet.cleanup();

    }
    private static final java.util.Map<Integer,List<Integer>> offers=new java.util.concurrent.ConcurrentHashMap<>();
    public static void select(Player p,int index)throws IOException{
        List<Integer> choices=offers.get(p.id);if(choices==null)return;
        if(index==choices.size()){show(p,0);return;}
        if(index<0||index>=choices.size())return;
        selected.put(p.id,choices.get(index));
        MenuController.send_menu_select(p.conn,12003,new String[]{"Xem thông tin và trang bị","Thách đấu","Danh sách thi đấu"});
    }
    public static void challenge(Player p,String name)throws IOException{
        init(p);for(int i=0;i<bots.size();i++)if(bots.get(i).name.equalsIgnoreCase(name)){
            selected.put(p.id,i);action(p,1);return;
        }
    }
    public static void action(Player p,int index) throws IOException {
        Integer chosen=selected.get(p.id); if(chosen==null)return;
        Player bot=bots.get(chosen);
        if(index==0){
            Message request=new Message(49); request.writer().writeUTF(bot.name);request.writer().writeByte(0);
            Service.send_view_other_player_in4(p.conn,new Message((byte)49,request.getData()));request.cleanup();
        } else if(index==1){
            int target=chosen+1;
            if(p.level<39){Service.send_notice_box(p.conn,"Cần cấp 39 để tham gia Top thi đấu.");return;}
            if(target>=rank(p)){Service.send_notice_box(p.conn,"Hãy chọn đối thủ có hạng cao hơn bạn.");return;}
            if(p.point_active[10]==target&&System.currentTimeMillis()/1000-p.point_active[9]<120){Service.send_notice_box(p.conn,"Chờ 2 phút để thách đấu lại đối thủ vừa thua.");return;}
            if(p.map.ld!=null||p.isdie||p.maze!=null||map.Map.is_map_chien_truong(p.map.map_id))return;
            if(p.point_active[8]!=0&&p.get_ngoc()<1){Service.send_notice_box(p.conn,"Sau trận thua, thách đấu tiếp cần 1 ngọc cho tới khi thắng lại.");return;}
            Player fresh=LoiDai.createOpponent(bot,29999,bot.level);
            fresh.name=bot.name; fresh.level=bot.level;fresh.clazz=bot.clazz;
            fresh.point1=bot.point1;fresh.point2=bot.point2;fresh.point3=bot.point3;fresh.point4=bot.point4;
            fresh.item.wear=bot.item.wear.clone();fresh.fashion=bot.fashion.clone();fresh.skill_point=bot.skill_point.clone();
            fresh.mypet=new ArrayList<>(bot.mypet);fresh.pet_follow=bot.pet_follow;
            fresh.load_skill(); fresh.hp=fresh.body.get_max_hp();fresh.mp=fresh.body.get_max_mp();
            if(p.point_active[8]!=0){p.update_ngoc(-1);p.item.char_inventory(5);}
            LoiDai.startChallenge(p,fresh,target);
        } else if(index==2)show(p,pages.getOrDefault(p.id,0));
    }
}
