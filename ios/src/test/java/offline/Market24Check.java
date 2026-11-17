package offline;

import client.Player;
import core.GameSrc;
import core.OfflineMarket;
import io.Message;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import map.Map;
import map.MapService;
import template.Item3;
import template.ItemSellCoin;
import template.Player_store;

public final class Market24Check {
    static class Buyer extends World23Check.Buyer {
        Buyer(World23Check.Capture connection) { super(connection); }
    }

    private static Message packet(int command, int seller, int item) throws Exception {
        Message message = new Message(-102);
        message.writer().writeByte(command);
        if (command == 2) message.writer().writeShort(item);
        message.writer().writeShort(seller);
        if (command == 2) message.writer().writeByte(3);
        return new Message((byte)-102, message.getData());
    }

    private static void check(boolean condition, String text) {
        if (!condition) throw new AssertionError(text);
    }

    public static void main(String[] args) throws Exception {
        try {
            IosWorld.start(Path.of(args[0]), Path.of(args[1]));
            Map[] markets = Map.get_map_by_id(82);
            Set<Integer> sellerIds = new HashSet<>();
            Set<String> arrangements = new HashSet<>();
            for (Map market : markets) {
                check(market.ismaplang, "Market must be a safe map for the client");
                List<Player> sellers = market.players.stream().filter(OfflineMarket::isMerchant).toList();
                check(sellers.size() == 5, "Every zone has five merchants");
                check(sellers.stream().noneMatch(s -> s.typepk != -1 || !sellerIds.add(s.id)), "Neutral, globally unique merchants");
                check(sellers.stream().map(s -> s.name).distinct().count() == 5, "All tiers present");
                arrangements.add(sellers.stream().map(s -> s.name).toList().toString());
            }
            check(arrangements.size() > 1, "Merchants were shuffled across zones");
            Map market = markets[0];
            var customerConnection = new World23Check.Capture();
            Buyer customer = new Buyer(customerConnection);
            customer.map = market;
            customer.typepk = -1;
            customer.nv_tinh_tu = new short[3];
            MapService.change_flag(market, customer, 0);
            check(customer.typepk == -1, "Market must block enabling đồ sát");

            Player bot = market.players.get(0);
            GameSrc.player_store(customerConnection, packet(1, bot.id, 0));
            check(customerConnection.packet != null, "View bot shop through command -102");
            GameSrc.player_store(customerConnection, packet(2, bot.id, 4587));
            check(customer.item.bag3[0] != null && customer.item.bag3[0].tier >= 6 && customer.gold < 100000,
                    "Buy actual medal through command -102");

            var sellerConnection = new World23Check.Capture();
            Player seller = new Player(sellerConnection, 124) {
                long gold = 100000;
                @Override public synchronized long get_vang() { return gold; }
                @Override public synchronized void update_vang(long amount) { gold += amount; }
            };
            sellerConnection.p = seller;
            seller.name = "MarketTester";
            seller.map = market;
            seller.item = new client.Item(seller);
            seller.item.bag3 = new Item3[10];
            seller.item.bag47 = new ArrayList<>();
            seller.my_store = new ArrayList<>();
            seller.my_store_name = "Sạp tài khoản thử";
            Item3 item = ItemSellCoin.entry.stream().filter(offer -> offer.id == 4587).findFirst().orElseThrow().createItem();
            item.islock = false;
            seller.item.bag3[0] = item;
            Player_store listing = new Player_store();
            listing.it_type = 3;
            listing.it_id = 0;
            listing.it_price = 10001;
            seller.my_store.add(listing);
            synchronized (market) { market.players.add(seller); }
            try {
                long gold = customer.gold;
                GameSrc.player_store(customerConnection, packet(1, seller.id, 0));
                GameSrc.player_store(customerConnection, packet(2, seller.id, item.id));
                check(customer.item.bag3[1] == item && seller.item.bag3[0] == null, "Player item changes hands");
                check(customer.gold == gold - 10001 && seller.get_vang() == 109500, "Buyer charge and 95 percent seller payout");
                GameSrc.player_store(customerConnection, packet(2, seller.id, item.id));
                check(customer.gold == gold - 10001, "Sold listing cannot be bought twice");
            } finally {
                synchronized (market) { market.players.remove(seller); }
            }
            Item3 wing = new Item3();
            wing.id = 2880;
            wing.name = "Cánh Chiến Thần";
            wing.type = 7;
            wing.op = new ArrayList<>();
            wing.time_use = System.currentTimeMillis() + 3600000;
            customer.item.bag3[2] = wing;
            for (int materialId : new int[]{8, 9, 10, 11, 0, 3}) {
                template.Item47 material = new template.Item47();
                material.id = (short) materialId;
                material.category = 7;
                material.quantity = 1000;
                customer.item.bag47.add(material);
            }
            customer.gold = 200000;
            for (int tier = 0; tier < 2; tier++) {
                Message upgrade = new Message(77);
                upgrade.writer().writeByte(3);
                upgrade.writer().writeInt(wing.id);
                upgrade.writer().writeShort(2);
                long before = customer.gold;
                GameSrc.Wings_Process(customerConnection, new Message((byte)77, upgrade.getData()));
                check(wing.tier == tier + 1 && wing.time_use == 0, "Wing upgrades immediately, including an old pending wing");
                check(before - customer.gold == GameSrc.wing_upgrade_material_gold[tier], "Wing charges displayed gold");
            }
            System.out.println("MARKET24_PASS all zones, shuffled tiers, PK blocked, bot and player purchases, and instant consecutive wing upgrades");
            System.exit(0);
        } catch (Throwable error) {
            error.printStackTrace();
            System.exit(1);
        }
    }
}
