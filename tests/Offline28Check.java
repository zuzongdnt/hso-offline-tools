import java.io.*;
import java.util.*;
import template.*;
import core.OfflineMarket;

public class Offline28Check {
    static class Capture extends io.Session {
        boolean reward;
        Capture(){super(null);} public void addmsg(io.Message m){if(m.cmd==78)reward=true;}
    }
    static class Buyer extends client.Player {
        Buyer(Capture c){super(c,123);c.p=this;point_active=new int[10];item=new client.Item(this){public void char_inventory(int type){}};
            maxbag=4;item.bag47=new ArrayList<>();item.bag3=new Item3[4];item.box3=new Item3[4];item.wear=new Item3[24];}
        public void flush(){}
    }
    static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args) throws Exception {
        ItemSellCoin.entry.clear();
        for(int i=0;i<=4590;i++){
            ItemTemplate3 t=new ItemTemplate3();t.setId((short)i);t.setName("Fixture "+i);
            t.setType((byte)16);t.setOp(new ArrayList<>());ItemTemplate3.item.add(t);
        }
        for(int id:new int[]{4587,4589,4588,4590}){
            ItemSellCoin offer=new ItemSellCoin();offer.id=(short)id;offer.op=new ArrayList<>();offer.color=5;
            ItemSellCoin.entry.add(offer);
        }
        for(int clazz=0;clazz<4;clazz++){
            Item3 medal=OfflineMarket.lotteryMedal(clazz);
            check(medal.tier==15,"Lottery medal tier");
            check(medal.getParamByOptionId(new int[]{33,34,35,36}[clazz])>0,"Class effect missing");
            check(medal.getParamByOptionId(77)==5000,"Burn duration must be milliseconds");
            check(medal.getParamByOptionId(81)==5000,"Invisibility duration must be milliseconds");
            check(medal.getParamByOptionId(88)==3000,"Confusion duration must be milliseconds");
            MessageCheck(medal);
        }
        Item3 legacy=new Item3();legacy.type=16;legacy.tier=15;
        check(legacy.optionValue(new Option(77,5))==5000,"Old saved medal duration display");
        ItemTemplate3 costume=ItemTemplate3.item.get(4100);costume.setType((byte)15);
        ItemSellCoin offer=new ItemSellCoin();offer.id=4100;offer.color=5;offer.op=new ArrayList<>();ItemSellCoin.entry.add(offer);
        Buyer buyer=new Buyer(new Capture());buyer.point_active[2]=299;
        core.ArenaShop.show(buyer,0);core.ArenaShop.select(buyer,1);
        check(buyer.item.bag3[0]==null && buyer.point_active[2]==299,"Insufficient points consumed or awarded an item");
        buyer.point_active[2]=300;core.ArenaShop.select(buyer,1);
        check(buyer.item.bag3[0]!=null && buyer.item.bag3[0].id==4100 && buyer.point_active[2]==0,"Point purchase did not exchange exactly once");
        core.ArenaShop.select(buyer,1);
        check(buyer.item.bag3[1]==null && buyer.point_active[2]==0,"Repeated purchase granted a free item");
        for(int id=0;id<=52;id++){
            ItemTemplate4 t=new ItemTemplate4();t.setId((short)id);t.setName("Reward "+id);ItemTemplate4.item.add(t);
        }
        Capture lotteryPackets=new Capture();Buyer lottery=new Buyer(lotteryPackets);
        lottery.maxbag=20;lottery.quest_daily=new int[6];lottery.nv_tinh_tu=new short[3];
        Item47 ticket=new Item47();ticket.category=4;ticket.id=52;ticket.quantity=1;lottery.item.bag47.add(ticket);
        lottery.id_select_mo_ly=0;event_daily.MoLy.item_mo_ly_percent[0]=0;
        io.Message play=new io.Message(-91);play.writer().writeByte(2);play.writer().writeByte(-1);
        event_daily.MoLy.Lottery_process(lottery,new io.Message((byte)-91,play.getData()));
        check(lottery.id_select_mo_ly==-1 && lottery.item.total_item_by_id(4,52)==0,"Play again did not finish the pending ticket");
        check(lotteryPackets.reward,"Lottery did not show its consolation rewards");
        System.out.println("Offline28Check OK: class bonuses, effect durations and cross-class display");
    }
    static void MessageCheck(Item3 medal)throws Exception{
        for(byte viewer=0;viewer<4;viewer++){
            io.Message m=new io.Message(0);medal.writeItemOptions(m,viewer);
            DataInputStream input=new DataInputStream(new ByteArrayInputStream(m.getData()));
            check(input.readUnsignedByte()==medal.op.size(),"Medal options hidden by viewer class");
            for(Option op:medal.op){check(input.readByte()==op.id,"Option order");check(input.readInt()==medal.optionValue(op),"Option value");}
            check(input.available()==0,"Trailing bytes");
        }
    }
}
