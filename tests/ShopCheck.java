import java.io.*;
import java.nio.file.*;
import java.util.*;
import org.json.simple.*;
import org.json.simple.parser.JSONParser;
import client.Player;
import client.Item;
import core.Manager;
import core.Service;
import io.Message;
import io.Session;
import template.*;

public class ShopCheck {
    static class Capture extends Session {
        byte[] packet;
        Capture() { super(null); }
        public void addmsg(Message m) { packet = m.getData().clone(); }
    }
    static class Buyer extends Player {
        long gold;
        Buyer(Capture conn) {
            super(conn,123);
            conn.p=this;
            gold=100000000;
            maxbag=98;
            item=new Item(this);
            item.bag3=new Item3[98];
            item.box3=new Item3[98];
            item.wear=new Item3[24];
            item.bag47=new ArrayList<>();
        }
        public synchronized long get_vang() { return gold; }
        public synchronized void update_vang(long value) { gold+=value; }
        public synchronized boolean update_coin(int value) { throw new AssertionError("Coin was charged"); }
    }
    static int n(JSONObject o,String key) { return ((Number)o.get(key)).intValue(); }
    static void check(boolean b) { if(!b) throw new AssertionError(); }
    static Message buy(int category,int id,int quantity) throws Exception {
        Message out=new Message(0);
        out.writer().writeByte(category);
        out.writer().writeShort(id);
        out.writer().writeShort(quantity);
        return new Message((byte)0,out.getData());
    }
    public static void main(String[] args) throws Exception {
        JSONObject data=(JSONObject)new JSONParser().parse(Files.readString(Path.of(args[0])));
        for(Object row:(JSONArray)data.get("item3")) {
            JSONObject o=(JSONObject)row;
            ItemTemplate3 t=new ItemTemplate3();
            t.setId((short)n(o,"id"));t.setName((String)o.get("name"));
            t.setType((byte)n(o,"type"));t.setClazz((byte)n(o,"clazz"));
            t.setIcon((short)n(o,"icon"));t.setPart((byte)n(o,"part"));
            JSONArray pairs=(JSONArray)new JSONParser().parse((String)o.get("data"));
            ArrayList<Option> ops=new ArrayList<>();
            for(Object pair:pairs) {JSONArray a=(JSONArray)pair;ops.add(new Option(((Number)a.get(0)).intValue(),((Number)a.get(1)).intValue()));}
            t.setOp(ops);
            ItemTemplate3.item.add(t);
        }
        for(Object row:(JSONArray)data.get("item4")) {
            JSONObject o=(JSONObject)row;
            ItemTemplate4 t=new ItemTemplate4();
            t.setId((short)n(o,"id"));t.setType((byte)n(o,"type"));
            t.setPrice(n(o,"price"));t.setPricetype((byte)n(o,"moneytype"));
            ItemTemplate4.item.add(t);
        }
        for(Object row:(JSONArray)data.get("item7")) {
            JSONObject o=(JSONObject)row;
            ItemTemplate7 t=new ItemTemplate7();
            t.setId((short)n(o,"id"));t.setType((byte)n(o,"type"));
            t.setPrice(n(o,"price"));t.setPricetype((byte)n(o,"moneytype"));
            ItemTemplate7.item.add(t);
        }
        Manager manager=Manager.gI();
        manager.itemsellTB=new ArrayList<>();
        manager.item7sell=ItemSellCoin.configure(new short[]{1,14,27});
        int size=ItemSellCoin.entry.size();
        ItemSellCoin.configure(manager.item7sell);
        check(size==ItemSellCoin.entry.size());
        check(new HashSet<>(ItemSellCoin.entry.stream().map(o->o.id).toList()).size()==size);
        for(short gem:ItemSellCoin.LEVEL5_GEMS) {
            check(ItemTemplate7.item.get(gem).getPricetype()==0);
            boolean found=false;
            for(short id:manager.item7sell) if(id==gem) found=true;
            check(found);
        }
        long skins=ItemTemplate3.item.stream().filter(t->t.getType()==15 || t.getType()>=21&&t.getType()<=27).count();
        check(ItemSellCoin.entry.stream().filter(o->{int t=ItemTemplate3.item.get(o.id).getType();return t==15 || t>=21&&t<=27;}).count()==skins);
        Capture conn=new Capture();Buyer buyer=new Buyer(conn);
        Service.send_box_UI(conn,37);
        DataInputStream packet=new DataInputStream(new ByteArrayInputStream(conn.packet));
        check(packet.readUTF().contains("Vàng"));check(packet.readByte()==1);
        check(packet.readUnsignedShort()==size);
        for(ItemSellCoin offer:ItemSellCoin.entry) {
            check(packet.readShort()==offer.id);packet.readUTF();packet.readByte();packet.readByte();packet.readShort();
            check(packet.readLong()==offer.price);check(packet.readShort()==offer.createItem().level);check(packet.readByte()==offer.color);
            Message expected=new Message(0);offer.createItem().writeItemOptions(expected,buyer.clazz);
            byte[] bytes=expected.getData();check(Arrays.equals(bytes,packet.readNBytes(bytes.length)));
            check(packet.readByte()==0);
        }
        check(packet.available()==0);
        ItemSell3 overlapping = new ItemSell3();
        overlapping.id = 4593;
        overlapping.price = 1;
        manager.itemsellTB.add(new ItemSell3[]{overlapping});
        long overlapGold = buyer.gold;
        Service.buy_item(buyer,buy(1,4593,1));
        check(buyer.gold==overlapGold-400000 && buyer.item.bag3[0].id==4593);
        buyer.item.bag3[0]=null;
        long before=buyer.gold;
        Service.buy_item(buyer,buy(1,4672,2));
        check(buyer.gold==before-500000);
        check(buyer.item.bag3[0].id==4672 && buyer.item.bag3[1].id==4672);
        check(buyer.item.bag3[0].color==4 && buyer.item.bag3[0].level==45);
        check(buyer.item.bag3[0].op.stream().anyMatch(o->Byte.toUnsignedInt(o.id)==155));
        check(buyer.item.bag3[0].op!=buyer.item.bag3[1].op);
        buyer.gold=0;
        Service.buy_item(buyer,buy(1,4755,1));
        check(buyer.item.bag3[2]==null && buyer.gold==0);
        buyer.gold=100000000;before=buyer.gold;
        Service.buy_item(buyer,buy(1,4778,1));check(buyer.gold==before && buyer.item.bag3[2]==null);
        Service.buy_item(buyer,buy(4,411,2));
        check(buyer.gold==before-200000 && buyer.item.total_item_by_id(7,411)==2);
        before=buyer.gold;
        Service.buy_item(buyer,buy(0,313,1));
        check(buyer.gold==before-1000000 && buyer.item.total_item_by_id(4,313)==1);
        before=buyer.gold;
        Service.buy_item(buyer,buy(4,411,32000));check(buyer.gold==before);
        Service.buy_item(buyer,buy(0,313,32000));check(buyer.gold==before);
        Service.buy_item(buyer,buy(1,4672,0));check(buyer.gold==before);
        Service.send_box_UI(conn,38);
        packet=new DataInputStream(new ByteArrayInputStream(conn.packet));
        check(packet.readUTF().contains("Vàng"));check(packet.readByte()==0);
        check(packet.readShort()==ItemSellCoin.MOUNTS.length);
        for(short mount:ItemSellCoin.MOUNTS) {check(packet.readShort()==mount);check(ItemTemplate4.item.get(mount).getPricetype()==0);}
        System.out.println("PASS: "+size+" offers, "+skins+" skins, "+ItemSellCoin.MOUNTS.length+" mount variants, 17 gems; preview matches purchased items, gold payment, quantity and failed purchases verified.");
    }
}
