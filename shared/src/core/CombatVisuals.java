package core;

import client.Player;
import io.Message;
import java.io.IOException;
import java.nio.ByteBuffer;
import map.MapService;

/** Native -49/2 effect packets: animation ID is separate from the full actor ID. */
public final class CombatVisuals {
    private CombatVisuals() {}
    public static void mob(Player attacker,map.Mob_in_map mob,int effect,int time)throws IOException {
        if(mob.hp<=0)return;
        mob.confusedUntil=System.currentTimeMillis()+time;
        int zoom=Math.max(1,Math.min(4,attacker.conn.zoomlv));
        byte[] raw=Util.loadfile("data/part_char/imgver/x"+zoom+"/112_"+effect);
        int start=4+ByteBuffer.wrap(raw).getInt(),size=raw.length-start;
        if(start<4||size<=0||size>32767)throw new IOException("Invalid monster effect");
        Message packet=new Message(-49);packet.writer().writeByte(2);packet.writer().writeShort(size);packet.writer().write(raw,start,size);
        packet.writer().writeByte(0);packet.writer().writeByte(0);packet.writer().writeByte(effect);
        packet.writer().writeShort(mob.index);packet.writer().writeByte(1);packet.writer().writeByte(0);packet.writer().writeInt(time);
        MapService.send_msg_player_inside(attacker.map,attacker,packet,true);packet.cleanup();
    }
    public static void show(Player player,int effect,int time)throws IOException {
        if(effect==17 && player.get_eff(-204)!=null){invisible(player,time);return;}
        send(player,effect,0,time,false);
    }
    public static void send(Player player,int effect,int movement,int time,boolean ownerOnly)throws IOException {
        int zoom=Math.max(1,Math.min(4,player.conn.zoomlv));
        byte[] raw=Util.loadfile("data/part_char/imgver/x"+zoom+"/112_"+effect);
        int start=4+ByteBuffer.wrap(raw).getInt(),size=raw.length-start;
        if(start<4 || size<=0 || size>32767)throw new IOException("Invalid combat effect "+effect);
        Message packet=new Message(-49);packet.writer().writeByte(2);
        packet.writer().writeShort(size);packet.writer().write(raw,start,size);
        packet.writer().writeByte(0);packet.writer().writeByte(0);
        packet.writer().writeByte(effect);packet.writer().writeShort(player.id);
        packet.writer().writeByte(0);packet.writer().writeByte(movement);packet.writer().writeInt(time);
        if(ownerOnly || player.map==null)player.conn.addmsg(packet);
        else MapService.send_msg_player_inside(player.map,player,packet,true);
        packet.cleanup();
    }
    private static void invisible(Player player,int time)throws IOException {
        send(player,54,17,time,true);
        if(player.map==null)return;
        Message remove=new Message(8);remove.writer().writeShort(player.id);
        MapService.send_msg_player_inside(player.map,player,remove,false);remove.cleanup();
    }
}
