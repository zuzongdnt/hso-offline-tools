import java.io.*;
import java.util.*;
import java.lang.reflect.*;
import core.*;
import client.*;
import template.*;
import io.*;

public class UpgradeCheck extends ShopCheck {
    static class Funds extends Buyer {
        int gems=100000;
        Funds(Capture c) { super(c); }
        public synchronized int get_ngoc() { return gems; }
        public synchronized void update_ngoc(long amount) { gems+=(int)amount; }
    }
    static Message request(int type,int id,int category) throws Exception {
        Message out=new Message(0);
        out.writer().writeByte(type);out.writer().writeShort(id);out.writer().writeByte(category);
        return new Message((byte)0,out.getData());
    }
    static Item3 offer(int id) {
        return ItemSellCoin.entry.stream().filter(t->t.id==id).findFirst().orElseThrow().createItem();
    }
    static int stat(Item3 it,int id) {
        return it.op.stream().filter(o->Byte.toUnsignedInt(o.id)==id).mapToInt(o->o.getParam(0)).sum();
    }
    static void materials(Capture c,short[] ids,int quantity) throws Exception {
        DataInputStream p=new DataInputStream(new ByteArrayInputStream(c.packet));
        check(p.readByte()==4);check(p.readByte()==ids.length);
        for(short id:ids) { check(p.readShort()==id);check(p.readShort()==quantity); }
        check(p.available()==0);
    }
    public static void main(String[] args) throws Exception {
        ShopCheck.main(args);
        check(stat(offer(4760),7)==1500 && stat(offer(4760),27)==2000);
        check(stat(offer(4760),185)==500 && stat(offer(4760),186)==500);
        check(stat(offer(4760),37)==0 && stat(offer(4760),128)==0);
        check(stat(offer(4741),7)==1500 && stat(offer(4741),15)==1500);
        check(stat(offer(4634),7)==2500 && stat(offer(4634),122)==10000 && stat(offer(4634),27)==0);
        check(stat(offer(4755),184)==500 && stat(offer(4755),62)==10000);
        check(stat(offer(3602),11)==1000);
        Message wire=new Message(0);offer(4760).writeItemOptions(wire,(byte)0);
        check(new DataInputStream(new ByteArrayInputStream(wire.getData())).readByte()==8);
        Capture c=new Capture();Funds p=new Funds(c);
        p.tinhtu_material=new short[]{146,147,148,149,150};
        p.medal_create_material=new short[20];
        for(int i=0;i<20;i++)p.medal_create_material[i]=(short)(146+i%5);
        for(short id:p.tinhtu_material) {
            Item47 stack=new Item47();stack.id=id;stack.quantity=1000;stack.category=7;
            p.item.bag47.add(stack);
        }
        p.item.bag3[0]=offer(4672);p.item.bag3[0].level=10;
        GameSrc.Create_Medal(c,request(0,0,3));materials(c,p.tinhtu_material,3);
        check(p.item.bag3[0].level==45);
        for(int id=4780;id<=4788;id++) {
            p.item.bag3[1]=offer(id);GameSrc.Create_Medal(c,request(0,1,3));materials(c,p.tinhtu_material,3);
        }
        p.item.bag3[2]=offer(4587);p.item.bag3[2].tier=15;
        GameSrc.Create_Medal(c,request(0,2,3));materials(c,p.tinhtu_material,17);
        Method create=MenuController.class.getDeclaredMethod("Menu_DoTinhTu",Player.class,byte.class);
        create.setAccessible(true);create.invoke(null,p,(byte)0);
        DataInputStream menu=new DataInputStream(new ByteArrayInputStream(c.packet));
        menu.readUTF();check(menu.readByte()==19);check(menu.readShort()==0);check(menu.readByte()==5);
        for(short id:p.tinhtu_material) {check(menu.readShort()==id);check(menu.readShort()==10);}
        check(menu.available()==0);
        boolean success=false,failure=false;
        for(int attempt=0;attempt<100 && (!success || !failure);attempt++) {
            p.item.bag3[0]=offer(4672);int gems=p.gems;
            int before=p.item.total_item_by_id(7,146);
            GameSrc.Create_Medal(c,request(4,0,3));
            check(p.item.bag3[0]!=null);
            check(p.gems==gems-1 && p.item.total_item_by_id(7,146)==before-3);
            if(p.item.bag3[0].level==55)success=true;
            else {check(p.item.bag3[0].level==45);check(stat(p.item.bag3[0],129)==9900);failure=true;}
        }
        check(success && failure);
        p.item.bag3[0].level=135;int gems=p.gems;int count=p.item.total_item_by_id(7,146);
        GameSrc.Create_Medal(c,request(4,0,3));
        check(p.gems==gems && p.item.total_item_by_id(7,146)==count && p.item.bag3[0].level==135);
        GameSrc.Create_Medal(c,request(0,-2,3));GameSrc.Create_Medal(c,request(4,999,3));
        Service.send_item7_template(p,new Message((byte)0,new byte[]{(byte)0xc7,3}));
        check(Item.get_level_tinh_tu(10)==1 && Item.get_level_tinh_tu(45)==1 && Item.get_level_tinh_tu(135)==10);
        check(Item.normalize_tinh_tu_level(20)==55 && Item.normalize_tinh_tu_level(50)==85);
        System.out.println("PASS: official outfit stats, all cosmetic damage lines, native 16-bit material packets, 29 Tinh Tu IDs, upgrade success/failure/durability, max level, malformed IDs and creation menu.");
    }
}
