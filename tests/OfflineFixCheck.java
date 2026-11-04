import java.io.*;
import java.util.*;
import client.*;
import core.*;
import io.*;
import template.*;

public class OfflineFixCheck extends UpgradeCheck {
    static class Packets extends Capture {
        final List<byte[]> petPackets = new ArrayList<>();
        @Override public void addmsg(Message message) {
            super.addmsg(message);
            if (message.cmd == 44) petPackets.add(message.getData().clone());
        }
    }
    static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    static Message deposit(int slot) throws IOException {
        Message message = new Message(44);
        message.writer().writeByte(1);
        message.writer().writeShort(slot);
        message.writer().writeByte(3);
        message.writer().writeShort(1);
        return new Message((byte)44, message.getData());
    }
    static Item3 egg(int id) {
        ItemTemplate3 template=ItemTemplate3.item.get(id);
        Item3 item=new Item3();
        item.id=(short)id; item.name=template.getName(); item.type=14;
        item.clazz=4; item.icon=template.getIcon(); item.level=10;
        item.op=new ArrayList<>(); item.islock=true;
        return item;
    }
    public static void main(String[] args) throws Exception {
        UpgradeCheck.main(args);
        int upgrades=0, failures=0;
        Packets connection=new Packets(); Funds player=new Funds(connection);
        for(short material=146;material<=150;material++) {
            Item47 stack=new Item47();stack.id=material;stack.category=7;stack.quantity=30000;
            player.item.bag47.add(stack);
        }
        int[] socketValues={27,406,-1};
        for(int level:new int[]{45,65,95,125}) {
            boolean success=false,failure=false;
            for(int attempt=0;attempt<150 && (!success || !failure);attempt++) {
                player.tinhtu_material=new short[]{146,147,148,149,150};
                Item3 item=offer(4672);item.level=(short)level;
                for(int i=0;i<3;i++) item.op.add(new Option(58+i,socketValues[i]));
                player.item.bag3[0]=item;
                GameSrc.Create_Medal(connection,request(4,0,3));
                for(int i=0;i<3;i++) {
                    final int socketId=58+i;
                    require(item.op.stream().filter(o->Byte.toUnsignedInt(o.id)==socketId).findFirst().orElseThrow().getParam(0)==socketValues[i],
                        "Socket "+socketId+" changed during Tinh Tu upgrade at level "+level);
                }
                boolean upgraded=item.level==level+10;
                success|=upgraded;failure|=!upgraded;
                if(upgraded) upgrades++; else failures++;
            }
            require(success && failure,"Missing success/failure coverage at level "+level);
        }
        int[] eggs={2944,2943,2939,3269,3616,4617,4622,4626,4631,4699,4708,4761,4762,4768};
        for(int type=0;type<eggs.length;type++) {
            int id=eggs[type];
            Pet pet=Pet.get_pet((short)id);
            require(pet!=null,"Unsupported egg "+id);
            require(pet.type==type && Pet.get_id(pet.type)==id,"Pet/egg mapping does not round-trip: "+id);
            player.mypet=new ArrayList<>(); player.item.bag3[0]=egg(id);
            connection.petPackets.clear();
            Service.pet_process(connection,deposit(0));
            require(player.item.bag3[0]==null && player.mypet.size()==1,"Egg not deposited: "+id);
            require(player.mypet.get(0).time_born>System.currentTimeMillis(),"No incubation timer: "+id);
            require(connection.petPackets.size()==1,"Missing incubation response: "+id);
            DataInputStream packet=new DataInputStream(new ByteArrayInputStream(connection.petPackets.get(0)));
            require(packet.readUnsignedByte()==28 && packet.readUnsignedByte()==1 && packet.readUnsignedByte()==3 && packet.readUnsignedByte()==3,"Invalid pet container header");
            packet.readUTF(); packet.readByte(); require(packet.readShort()==id,"Wrong incubation egg");
            packet.readByte();packet.readShort();packet.readByte();packet.readShort();packet.readByte();packet.readByte();packet.readByte();
            require(packet.readUnsignedByte()==0,"Unexpected egg options");
            int minutes=packet.readInt();require(minutes>0 && minutes<=10,"Invalid hatch timer");packet.readByte();
            require(packet.available()==0,"Malformed pet item packet");
            player.item.bag3[0]=egg(id);
            Service.pet_process(connection,deposit(0));
            require(player.item.bag3[0]!=null && player.mypet.size()==1,"A second incubation consumed an egg");
        }
        player.mypet=new ArrayList<>();player.item.bag3[0]=offer(4672);
        Service.pet_process(connection,deposit(0));
        require(player.item.bag3[0]!=null && player.mypet.isEmpty(),"Non-egg consumed");
        Service.pet_process(connection,deposit(-1));Service.pet_process(connection,deposit(999));
        Pet existing=Pet.get_pet((short)2943);existing.is_hatch=false;existing.time_born=System.currentTimeMillis()+100000;
        player.mypet.add(existing);player.item.bag3[0]=egg(4626);
        Service.pet_process(connection,deposit(0));
        require(player.mypet.size()==2 && player.item.bag3[0]==null,"A non-incubating pet incorrectly blocks eggs");
        System.out.println("PASS: "+upgrades+" successful Tinh Tu upgrades / "+failures+" failed attempts preserve three sockets; all 14 egg IDs deposit and round-trip; duplicate, non-egg and malformed requests preserve inventory.");
    }
}
