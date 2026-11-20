package offline;

import client.Item;
import client.Player;
import client.TextFromClient;
import core.GameSrc;
import core.Manager;
import core.SQL;
import event_daily.LoiDai;
import io.Message;
import io.Session;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import map.Map;
import template.Item3;
import template.Item47;
import template.ItemSellCoin;

public final class Offline37CraftCheck {
    private static void check(boolean condition, String description) {
        if (!condition) throw new AssertionError(description);
    }

    private static Message craft(int action, int slot, int category) throws Exception {
        var packet = new Message(-105);
        packet.writer().writeByte(action);
        packet.writer().writeShort(slot);
        packet.writer().writeByte(category);
        return new Message((byte) -105, packet.getData());
    }

    private static Message wing(int action, int id, int slot) throws Exception {
        var packet = new Message(77);
        packet.writer().writeByte(action);
        packet.writer().writeInt(id);
        packet.writer().writeShort(slot);
        return new Message((byte) 77, packet.getData());
    }

    private static void submitQuantity(Session session, int recipe, String amount) throws Exception {
        var packet = new Message(0);
        packet.writer().writeShort(recipe);
        packet.writer().writeShort(0);
        packet.writer().writeByte(1);
        packet.writer().writeUTF(amount);
        TextFromClient.process(session, new Message((byte) 0, packet.getData()));
    }

    private static int slot(Player player, int item) {
        for (int i = 0; i < player.item.bag3.length; i++) {
            if (player.item.bag3[i] != null && player.item.bag3[i].id == item) return i;
        }
        throw new AssertionError("Missing crafted item " + item);
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        try {
            Manager.gI().init();
            var session = new Session(null) {
                @Override public void addmsg(Message message) {}
            };
            Player player = LoiDai.createOpponent(new Player(session, 120), 121, 59);
            player.conn = session;
            session.p = player;
            player.item.bag3 = new Item3[42];
            player.item.bag47 = new ArrayList<>();
            player.item.wear = new Item3[24];
            player.maxbag = 42;
            check(player.get_vang() == 0 && player.get_ngoc() == 0, "empty wallet fixture");
            player.medal_create_material = new short[20];
            player.tinhtu_material = new short[5];

            player.id_medal_is_created = 0;
            GameSrc.Create_Medal(session, craft(3, -1, -1));
            int medal = slot(player, 4587);
            GameSrc.Create_Medal(session, craft(4, medal, 3));
            check(player.item.bag3[medal].tier == 1, "medal is made and upgraded with empty inventory");

            player.id_medal_is_created = 4;
            GameSrc.Create_Medal(session, craft(3, -1, -1));
            int astral = slot(player, 4664);
            Item3 item = player.item.bag3[astral];
            item.color = 3;
            for (int i = 0; i < 40 && item.level == 45; i++) GameSrc.Create_Medal(session, craft(4, astral, 3));
            check(item.level == 55, "Tinh Tú upgrades without materials or gems");

            GameSrc.Wings_Process(session, wing(1, 2880, -1));
            int wing = slot(player, 2880);
            GameSrc.Wings_Process(session, wing(3, 2880, wing));
            check(player.item.bag3[wing].tier == 1, "wings are made and upgraded for free");

            var boost = new Message(67);
            boost.writer().writeByte(2);
            boost.writer().writeShort(0);
            boost.writer().writeByte(0);
            player.id_item_rebuild = (short) medal;
            GameSrc.rebuild_item(session, new Message((byte) 67, boost.getData()));
            check(player.item.bag3[medal].tier == 2, "ordinary enhancement accepts zero currency and materials");
            check(player.get_vang() == 0 && player.get_ngoc() == 0 && player.item.bag47.isEmpty(), "no resources debited");

            player.fusion_material_medal_id = 146;
            submitQuantity(session, 7, "2");
            check(player.item.total_item_by_id(7, 246) == 2 && player.item.total_item_by_id(7, 146) == 0,
                    "medal materials can be combined for free");
            player.id_hop_ngoc = 352;
            submitQuantity(session, 15, "2");
            check(player.item.total_item_by_id(7, 353) == 2 && player.item.total_item_by_id(7, 352) == 0,
                    "gems can be combined for free");
            player.id_ngoc_tinh_luyen = 352;
            submitQuantity(session, 16, "2");
            check(player.item.total_item_by_id(7, 382) == 2, "gems can be refined for free");

            byte[] metadata = Manager.gI().msg_61;
            try (var input = new DataInputStream(new ByteArrayInputStream(metadata))) {
                for (int list = 0; list < 2; list++) for (int n = input.readUnsignedByte(); n > 0; n--) input.readUTF();
                for (int n = input.readUnsignedByte(); n > 0; n--) input.readShort();
                for (int n = input.readUnsignedByte(); n > 0; n--) {
                    input.readByte();
                    check(input.readInt() == -1 && input.readShort() == 0 && input.readInt() == 0,
                            "rebuild button remains available without requirements");
                }
            }

            player.map = Map.get_map_by_id(7)[0];
            player.x = 400;
            player.y = 400;
            Item47 fire = new Item47();
            fire.id = 67;
            fire.category = 4;
            fire.quantity = 1;
            player.item.add_item_bag47(4, fire);
            player.map.useCampfire(player, fire.id);
            check(player.map.campfireExpBonus(player) == 2_000_000_000L, "near a sacred fire grants two billion EXP");
            player.x += 300;
            check(player.map.campfireExpBonus(player) == 0, "outside the radius grants no bonus");
            System.out.println("OFFLINE37_PASS free crafting and upgrades, client metadata, campfire radius and EXP");
        } catch (Throwable failure) {
            failure.printStackTrace();
            System.exit(1);
        } finally {
            if (SQL.is_connected) SQL.gI().close();
        }
        System.exit(0);
    }
}
