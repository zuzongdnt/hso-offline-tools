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
                Player bot = LoiDai.createOpponent(model, 31000 + bots.size());
                bot.name = new String[]{"Thiên Vũ", "Hàn Phong", "Bạch Nguyệt", "Lạc Vũ", "Xích Long"}[i] + " " + level + " [Bot]";
                bots.add(bot);
            }
        }
    }
    public static synchronized Player find(String name) {
        return bots.stream().filter(bot -> bot.name.equalsIgnoreCase(name)).findFirst().orElse(null);
    }
    public static void ranking(Player p) throws IOException {
        init(p);
        Message packet=new Message(56);packet.writer().writeByte(1);
        packet.writer().writeUTF("Top thi đấu · Bot offline");packet.writer().writeByte(99);
        packet.writer().writeInt(0);packet.writer().writeByte(bots.size());
        for(Player bot:bots){
            packet.writer().writeUTF(bot.name);packet.writer().writeByte(bot.head);
            packet.writer().writeByte(bot.eye);packet.writer().writeByte(bot.hair);packet.writer().writeShort(bot.level);
            java.util.List<template.Item3> gear=new ArrayList<>();
            for(int slot:new int[]{0,1,6,7,10})if(bot.item.wear[slot]!=null)gear.add(bot.item.wear[slot]);
            packet.writer().writeByte(gear.size());
            for(template.Item3 item:gear){packet.writer().writeByte(item.part);packet.writer().writeByte(item.type);}
            packet.writer().writeByte(1);packet.writer().writeUTF("Bot online · Chọn Danh sách thi đấu để thách đấu");
            packet.writer().writeShort(-1);
        }
        p.conn.addmsg(packet);packet.cleanup();
    }
    public static void show(Player p, int page) throws IOException {
        init(p); page = Math.max(0, Math.min(page, (bots.size() - 1) / 8)); pages.put(p.id,page);
        List<String> labels = new ArrayList<>();
        for (int i=page*8; i<Math.min(bots.size(),page*8+8);i++) {
            Player bot=bots.get(i); labels.add(bot.name+" · Lv "+bot.level+" · Online");
        }
        labels.add("Trang trước"); labels.add("Trang sau");
        MenuController.send_menu_select(p.conn,12002,labels.toArray(new String[0]));
    }
    public static void select(Player p,int index) throws IOException {
        Integer page=pages.get(p.id); if(page==null)return;
        int count=Math.min(8,bots.size()-page*8);
        if(index==count){show(p,page-1);return;}
        if(index==count+1){show(p,page+1);return;}
        if(index<0 || index>=count)return;
        selected.put(p.id,page*8+index);
        MenuController.send_menu_select(p.conn,12003,new String[]{"Xem thông tin và trang bị","Thách đấu","Danh sách thi đấu"});
    }
    public static void action(Player p,int index) throws IOException {
        Integer chosen=selected.get(p.id); if(chosen==null)return;
        Player bot=bots.get(chosen);
        if(index==0){
            Message request=new Message(49); request.writer().writeUTF(bot.name);request.writer().writeByte(0);
            Service.send_view_other_player_in4(p.conn,new Message((byte)49,request.getData()));request.cleanup();
        } else if(index==1){
            int lower=p.level<55?50:55+(p.level-55)/10*10;
            int upper=p.level<55?64:Math.min(139,lower+9);
            if(bot.level<lower || bot.level>upper){Service.send_notice_box(p.conn,"Hãy chọn bot trong nhóm cấp "+lower+"-"+upper+".");return;}
            Player fresh=LoiDai.createOpponent(bot,29999);
            fresh.name=bot.name; fresh.level=bot.level;fresh.clazz=bot.clazz;
            fresh.point1=bot.point1;fresh.point2=bot.point2;fresh.point3=bot.point3;fresh.point4=bot.point4;
            fresh.item.wear=bot.item.wear.clone();fresh.fashion=bot.fashion.clone();fresh.skill_point=bot.skill_point.clone();
            fresh.load_skill(); fresh.hp=fresh.body.get_max_hp();fresh.mp=fresh.body.get_max_mp();
            LoiDai.start(p,fresh);
        } else if(index==2)show(p,pages.getOrDefault(p.id,0));
    }
}
