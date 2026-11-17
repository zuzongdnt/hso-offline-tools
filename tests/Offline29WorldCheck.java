package offline;

import client.Item;
import client.Player;
import core.*;
import io.Message;
import io.Session;
import java.io.*;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import template.*;

public final class Offline29WorldCheck {
    static class Capture extends Session {
        byte[] shop;
        byte[] effect;
        Capture(){super(null);}
        @Override public void addmsg(Message message){if(message.cmd==23)shop=message.getData().clone();if(message.cmd==-49)effect=message.getData().clone();}
    }
    static class Buyer extends Player {
        int gems=100;
        Buyer(Capture capture){super(capture,123);capture.p=this;level=100;maxbag=20;point_active=new int[8];
            item=new Item(this){@Override public void char_inventory(int type){}};
            item.bag3=new Item3[20];item.wear=new Item3[24];item.bag47=new ArrayList<>();}
        @Override public void flush(){}
        @Override public synchronized int get_ngoc(){return gems;}
        @Override public synchronized void update_ngoc(long delta){gems+=(int)delta;}
    }
    static void check(boolean value,String text){if(!value)throw new AssertionError(text);}
    public static void main(String[] args)throws Exception {
        int exit=0;
        try {
            System.setProperty("hso.root",Path.of(args[0]).toAbsolutePath().toString());
            Manager.gI().init();
            Thread.sleep(200);
            check(offline.MapScheduler.workerCount()<=4 && Thread.activeCount()<100,"Bounded map workers");
            Capture capture=new Capture();Buyer buyer=new Buyer(capture);
            for(int level:new int[]{55,64,65,74,75,84,85,89,90,139}){
                Player bot=event_daily.LoiDai.createOpponent(buyer,32000+level,level);
                check(bot.level==level,"Exact bot level");
                Item3 medal=bot.item.wear[12];
                check(medal.tier==15 && medal.clazz==4,"Bot lottery medal +15 for all classes");
                check(medal.getParamByOptionId(77)==5000,"Bot burn duration");
                check(bot.mypet.size()==1 && bot.pet_follow && bot.mypet.get(0).is_follow,"Bot pet");
                int tier=ArenaBotEquipment.wingTier(level);
                check(tier<0?bot.item.wear[10]==null && bot.item.wear[14]==null:bot.item.wear[10].tier==tier,"Wing level progression");
            }
            ArenaRoster.show(buyer,0);
            var field=ArenaRoster.class.getDeclaredField("bots");field.setAccessible(true);
            @SuppressWarnings("unchecked") List<Player> bots=(List<Player>)field.get(null);
            check(bots.size()==45 && bots.get(0).level==139 && bots.get(44).level==55,"Roster endpoints");
            for(int i=1;i<bots.size();i++)check(bots.get(i-1).level>=bots.get(i).level,"Descending ranking");
            check(ArenaShop.stock().size()==10,"Ten arena skins");
            check(ItemSellCoin.goldStock().stream().anyMatch(row->row.id==4793),"Other skins remain in the gold shop");
            ArenaShop.show(buyer,0);
            DataInputStream packet=new DataInputStream(new ByteArrayInputStream(capture.shop));
            check(packet.readUTF().contains("300 điểm"),"Point price title");
            check(packet.readByte()==1 && packet.readShort()==10,"Image shop protocol");
            short reward=ArenaShop.stock().get(0).id;
            buyer.point_active[2]=299;ArenaShop.buy(buyer,reward,1);
            check(buyer.item.bag3[0]==null && buyer.point_active[2]==299,"Reject insufficient points");
            buyer.point_active[2]=300;ArenaShop.buy(buyer,reward,1);
            check(buyer.item.bag3[0]!=null && buyer.point_active[2]==0,"Exact point exchange");
            ArenaShop.buy(buyer,reward,Integer.MAX_VALUE);
            check(buyer.item.bag3[1]==null,"Reject overflowing bulk price");
            for(ItemTemplate7 material:ItemTemplate7.item)if(material.getType()==54)
                check(material.getPrice()==1 && material.getPricetype()==0,"All medal-material tiers cost one gold");
            Item3 weapon=new Item3();weapon.type=8;weapon.op=new ArrayList<>(List.of(new Option(58,386),new Option(59,391),new Option(100,48),new Option(101,42)));
            check(weapon.optionValue(new Option(100,48))==5 && weapon.optionValue(new Option(101,42))==5,"Correct legacy 48/42 socket rows to five hits");
            int[][] expected={{25,20,15,10,5},{25,20,15,10,5},{50,100,150,250,350},{50,100,150,250,350},{200,250,300,350,450},{300,500,700,900,1400},{100,300,500,700,900}};
            for(int kind=0;kind<7;kind++)for(int rank=0;rank<5;rank++){
                weapon.op=new ArrayList<>(List.of(new Option(58,kind==6?412+rank:352+kind*5+rank)));
                int option=kind<4?100+kind:kind==4?106:kind==5?107:108;
                check(SocketGems.value(weapon,option)==expected[kind][rank],"Socket stat table kind="+kind+" rank="+rank);
            }
            Player effects=event_daily.LoiDai.createOpponent(buyer,1234,90);effects.conn=capture;capture.p=effects;
            effects.map=map.Map.get_map_by_id(82)[0];effects.map.players.add(effects);
            Arrays.fill(effects.item.wear,null);effects.mypet.clear();effects.item.wear[0]=weapon;
            weapon.op=new ArrayList<>(List.of(new Option(58,356)));effects.hp=effects.body.get_max_hp();long full=effects.hp;
            for(int hit=0;hit<5;hit++)SocketGems.hon(effects);
            check(effects.get_eff(-210)!=null && effects.hp==Math.max(1,full-full/2),"Normal Hon Nguyen activates at five hits and deducts HP once");
            effectPacket(capture.effect,20,1234,0,3000);
            effects.list_eff.clear();effects.hit_count_ngoc_hon_nguyen=0;weapon.op.set(0,new Option(58,386));effects.hp=full;
            for(int hit=0;hit<5;hit++)SocketGems.hon(effects);
            check(effects.get_eff(-210)!=null && effects.hp==full,"Refined Hon Nguyen does not deduct HP");
            effects.list_eff.clear();weapon.op.set(0,new Option(58,391));effects.add_eff(-201,1,3000);
            for(int hit=0;hit<5;hit++)SocketGems.khai(effects);
            effects.add_eff(-205,1,3000);
            check(effects.get_eff(-211)!=null && effects.get_eff(-201)==null && effects.get_eff(-205)==null,"Khai Hoan clears and resists debuffs");
            effects.add_eff(-204,1,5000);CombatVisuals.show(effects,17,5000);
            effectPacket(capture.effect,54,1234,17,5000);
            effects.map.players.remove(effects);
            String incoming=Files.readString(Path.of(args[1]));
            var tables=SaveTransfer.validate(incoming);
            var account=(org.json.simple.JSONArray)((org.json.simple.JSONArray)tables.get("account")).get(0);
            String user=(String)account.get(1),pass=(String)account.get(2);
            SQL.gI().importSave(incoming);
            try(Connection c=SQL.gI().getConnection();PreparedStatement q=c.prepareStatement("UPDATE account SET pass=? WHERE user=?")){
                q.setString(1,"fixture-old-password");q.setString(2,user);check(q.executeUpdate()==1,"Existing local account collision");
            }
            SQL.gI().importSave(incoming);
            check(tables.equals(SaveTransfer.validate(SQL.gI().exportSave())),"Complete imported save including source password");
            try(Connection c=SQL.gI().getConnection()){
                String cached="knightauto_hsod_999999999999999999";
                String resolved=OfflineLogin.resolve(c,cached,"hsr_132");
                check(!resolved.equals(cached),"Imported automatic account reconnects");
                check(OfflineLogin.resolve(c,cached,"wrong").equals(cached),"Wrong automatic password is not mapped");
                check(OfflineLogin.resolve(c,user,"wrong").equals(user),"Manual credentials are not rewritten");
                try(PreparedStatement q=c.prepareStatement("SELECT pass FROM account WHERE user=?")){
                    q.setString(1,user);try(ResultSet rs=q.executeQuery()){check(rs.next() && pass.equals(rs.getString(1)),"PC password restored");}
                }
            }
            ChildEvent.start();long now=System.currentTimeMillis();ChildEvent.tick(now);
            map.Mob_in_map child=null;map.Map childMap=null,masterMap=null;
            for(map.Map[] zones:map.Map.entrys)for(map.Map zone:zones){
                if(ChildEvent.masterMap(zone))masterMap=zone;
                for(map.Mob_in_map mob:zone.mobs)if(mob.template.mob_id==175){child=mob;childMap=zone;}
            }
            check(child!=null && masterMap!=null,"Announced child spawns and Mr Master maps exist");
            buyer.name="ChildFixture";buyer.map=childMap;buyer.x=child.x;buyer.y=child.y;
            Item47 candy=new Item47();candy.category=4;candy.id=220;candy.quantity=1;buyer.item.bag47.add(candy);
            ChildEvent.follow(buyer);
            check(buyer.id_dua_be==child.index && buyer.item.total_item_by_id(4,220)==0,"Child escort consumes exactly one candy");
            buyer.map=masterMap;ChildEvent.adopt(buyer,false);
            check(buyer.detu!=null && buyer.detu.level==10 && buyer.id_dua_be==-1,"Escort adoption starts disciple at level ten");
            client.Disciple restored=client.Disciple.fromJson(buyer,buyer.detu.toJson());
            check(restored!=null && restored.level==10 && restored.wear[0]!=null,"Disciple inventory survives serialization");
            ChildEvent.tick(now+1000);
            check(countChildren()==0,"Successful adoption waits ninety minutes");
            ChildEvent.tick(now+ChildEvent.RESPAWN+5000);check(countChildren()==1,"Child respawns after ninety minutes");
            ChildEvent.tick(now+ChildEvent.RESPAWN+ChildEvent.LIFETIME+6000);check(countChildren()==1,"Expired child immediately respawns elsewhere");
            check(Arrays.stream(toBoxed(Manager.gI().itempoitionsell)).anyMatch(id->id==220),"Lisa sells child candy");
            System.out.println("OFFLINE29_PASS bounded map workers, arena rewards/bots, socket formulas/native packets, provided save/authentication, child spawn/escort/adoption/expiry and disciple persistence");
        }catch(Throwable error){error.printStackTrace();exit=1;}
        finally {if(SQL.is_connected)SQL.gI().close();}
        System.exit(exit);
    }
    private static int countChildren(){int n=0;for(map.Map[] zones:map.Map.entrys)for(map.Map zone:zones)for(map.Mob_in_map mob:zone.mobs)if(mob.template.mob_id==175)n++;return n;}
    private static Short[] toBoxed(short[] values){Short[] out=new Short[values.length];for(int i=0;i<values.length;i++)out[i]=values[i];return out;}
    private static void effectPacket(byte[] bytes,int animation,int actor,int movement,int duration)throws Exception{
        DataInputStream data=new DataInputStream(new ByteArrayInputStream(bytes));
        check(data.readByte()==2,"Native effect subtype");int size=data.readUnsignedShort();check(size>0,"Embedded native effect metadata");data.skipNBytes(size);
        data.readByte();data.readByte();check(data.readUnsignedByte()==animation,"Animation ID");
        check(data.readShort()==actor,"Full actor ID must not be truncated to a byte");
        check(data.readByte()==0 && data.readByte()==movement && data.readInt()==duration && data.available()==0,"Native effect fields");
    }
}
