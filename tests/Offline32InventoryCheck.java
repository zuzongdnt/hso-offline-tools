package offline;

import client.Player;
import core.GameSrc;
import core.Manager;
import core.SQL;
import core.Service;
import event_daily.LoiDai;
import io.Message;
import io.Session;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.nio.file.Path;
import java.util.ArrayList;
import template.Item3;
import template.ItemSellCoin;

public final class Offline32InventoryCheck {
    private static final class Capture extends Session {
        byte[] inventory;

        Capture() { super(null); zoomlv = 1; connected = true; }

        @Override public void addmsg(Message message) {
            byte[] bytes = message.getData();
            if (message.cmd == 16 && bytes.length > 2 && bytes[0] == 0 && bytes[1] == 3) {
                inventory = bytes.clone();
            }
        }
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void checkFirstItem(Capture client, boolean midlet, String name) throws Exception {
        try (var data = new DataInputStream(new ByteArrayInputStream(client.inventory))) {
            check(data.readUnsignedByte() == 0 && data.readUnsignedByte() == 3, "bulk item packet");
            data.readLong();
            data.readInt();
            check(data.readUnsignedByte() == 3, "equipment category");
            int count = midlet ? data.readUnsignedByte() : data.readUnsignedShort();
            check(count == 1 && data.readUTF().equals(name), "one equipment record decodes after count");
        }
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        Manager.gI().init();
        Capture client = new Capture();
        Player player = LoiDai.createOpponent(new Player(client, 200), 201, 55);
        player.conn = client;
        client.p = player;
        client.shopType = 37;
        player.maxbag = 256;
        player.item.bag3 = new Item3[player.maxbag];
        player.item.bag47 = new ArrayList<>();
        player.update_vang(1_000_000_000);
        ItemSellCoin offer = ItemSellCoin.goldStock().stream()
                .filter(candidate -> ItemSellCoin.cosmetic(candidate.createItem().type))
                .findFirst().orElseThrow();
        long initialGold = player.get_vang();
        Message buy = new Message(0);
        buy.writer().writeByte(1);
        buy.writer().writeShort(offer.id);
        buy.writer().writeShort(1);
        System.setProperty("hso.client.j2me", "true");
        Service.buy_item(player, new Message((byte) 0, buy.getData()));
        var bought = player.item.bag3[0];
        check(bought != null && bought.id == offer.id && player.get_vang() == initialGold - offer.price, "shop purchase committed once");
        checkFirstItem(client, true, bought.name);
        System.clearProperty("hso.client.j2me");
        player.item.char_inventory(3);
        checkFirstItem(client, false, bought.name);

        bought.tier = 0;
        var canRebuild = GameSrc.class.getDeclaredMethod("rebuildableItem", Player.class, int.class);
        canRebuild.setAccessible(true);
        check(canRebuild.invoke(null, player, 0) == null, "skin cannot enter enhancement");
        long goldAfterPurchase = player.get_vang();
        Message socket = new Message(0);
        socket.writer().writeByte(2);
        socket.writer().writeShort(0);
        socket.writer().writeShort(33);
        GameSrc.Hop_Ngoc_Kham(player, new Message((byte) 0, socket.getData()));
        check(player.get_vang() == goldAfterPurchase && player.item.check_kham_ngoc(bought)[0] == -2, "skin cannot be socketed");
        System.out.println("OFFLINE32_PASS real purchase, byte/short inventory counts, fixed cosmetic rules");
        SQL.gI().close();
        System.exit(0);
    }
}
