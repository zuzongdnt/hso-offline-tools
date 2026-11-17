package offline;

import client.Item;
import client.Player;
import core.OfflineMarket;
import core.SQL;
import core.Service;
import event_daily.MoLy;
import io.Message;
import io.Session;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import template.Item3;
import template.ItemSellCoin;
import template.ItemTemplate7;
import template.OfflineSkins;

public final class World23Check {
    static class Capture extends Session {
        byte[] packet;
        Capture() { super(null); }
        @Override public void addmsg(Message message) { packet = message.getData().clone(); }
    }
    static class Buyer extends Player {
        long gold = 100000;
        Buyer(Capture connection) {
            super(connection, 123);
            connection.p = this;
            level = 100;
            maxbag = 10;
            item = new Item(this);
            item.bag3 = new Item3[10];
            item.wear = new Item3[24];
            item.bag47 = new ArrayList<>();
            tutien = new int[2];
        }
        @Override public synchronized long get_vang() { return gold; }
        @Override public synchronized void update_vang(long delta) { gold += delta; }
    }
    private static void require(boolean condition, String text) {
        if (!condition) throw new AssertionError(text);
    }
    private static Item3 offer(int id) {
        return ItemSellCoin.entry.stream().filter(row -> row.id == id).findFirst().orElseThrow().createItem();
    }
    public static void main(String[] args) throws Exception {
        try {
            IosWorld.start(Path.of(args[0]), Path.of(args[1]));
            map.Map market = map.Map.get_map_by_id(82)[0];
            require(market.players.stream().filter(OfflineMarket::isMerchant).count() == 5, "Five merchants in map 82");
            Capture capture = new Capture();
            Buyer buyer = new Buyer(capture);
            buyer.map = market;
            for (Player seller : market.players) {
                if (!OfflineMarket.isMerchant(seller)) continue;
                int tier = seller.id - 30010 + 6;
                require(OfflineMarket.view(capture, seller), "Merchant shop packet");
                require(new String(capture.packet, java.nio.charset.StandardCharsets.UTF_8).contains("Mề đay"), "Shop title");
                long before = buyer.gold;
                require(OfflineMarket.buy(capture, seller, (short)4587, (byte)3), "Buy handled");
                require(buyer.gold == before - (tier - 5) * 1000L, "Exact price");
                require(buyer.item.bag3[tier - 6].tier == tier, "Bought actual upgraded item");
                require(seller.point3 >= seller.level + 504 && seller.point4 >= seller.level + 504, "Bot potential bonuses");
                require(seller.body.total_item_param(36) >= 2000 && seller.body.total_item_param(34) >= 4000, "Bot combat bonuses");
            }
            Player seller = market.players.stream().filter(OfflineMarket::isMerchant).findFirst().orElseThrow();
            buyer.gold = 0;
            OfflineMarket.buy(capture, seller, (short)4587, (byte)3);
            require(buyer.gold == 0 && buyer.item.bag3[5] == null, "No purchase without funds");
            for (int id = 46; id <= 145; id++) require(ItemTemplate7.item.get(id).getPrice() == 1, "Medal materials cost one gold");
            for (int clazz = 0; clazz < 4; clazz++) {
                Item3 medal = OfflineMarket.lotteryMedal(clazz);
                require(medal.tier == 15 && medal.clazz == clazz, "Lottery upgraded medal by class");
                require(medal.op.stream().anyMatch(op -> op.id == 76 && op.getParam(0) == 500), "5 percent burn chance");
                require(medal.op.stream().anyMatch(op -> op.id == 77 && op.getParam(0) == 5), "Five second burn duration");
            }
            require(MoLy.item_mo_ly.length == 10, "Lottery catalog includes four medals");
            MoLy.show_table_to_choose_item(buyer);
            require(capture.packet[1] == 10, "Lottery catalog packet count");
            for (var entry : ItemSellCoin.entry) {
                Item3 item = entry.createItem();
                if (!OfflineSkins.removed(item.id) && (item.type == 15 || item.type >= 21 && item.type <= 32))
                    require(!item.op.isEmpty(), "Cosmetic stats missing for " + item.id);
            }
            buyer.item.wear[11] = offer(4807);
            buyer.item.wear[13] = offer(4634);
            buyer.item.wear[15] = new Item3();
            require(Service.get_id_mat_na(buyer) == -1 && Service.get_id_phiphong(buyer) == -1, "Dream outfit hides mask and cloak");
            require(OfflineSkins.bodyEffect(buyer) == 253, "Full dream outfit kept");
            buyer.item.wear[11] = null;
            require(Service.get_id_mat_na(buyer) >= 0, "Mask returns after removing outfit");
            buyer.type_use_mount = 24;
            buyer.id_horse = 145;
            require(OfflineSkins.mountParam(buyer, 23) == 4 && OfflineSkins.mountParam(buyer, 27) == 500, "Mount stats apply when riding");
            buyer.type_use_mount = -1;
            require(OfflineSkins.mountParam(buyer, 23) == 0, "Unmount removes mount bonus");
            require(Files.readString(Path.of(args[0], "restore-result.txt")).contains("thành công"), "Pending import applied at startup");
            require(SQL.gI().exportSave().contains("transqa23"), "Transferred character persists after reboot");
            System.out.println("OFFLINE23_PASS merchants, actual purchases, prices, arena stats, lottery, cosmetics, mount stats, restore reboot");
            System.exit(0);
        } catch (Throwable error) {
            error.printStackTrace();
            System.exit(1);
        }
    }
}
