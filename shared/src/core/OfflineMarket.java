package core;

import client.Player;
import event_daily.LoiDai;
import io.Message;
import io.Session;
import java.io.IOException;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import template.Item3;
import template.ItemSellCoin;
import template.Option;

/** Permanent offline merchants reuse the normal player-shop protocol. */
public final class OfflineMarket {
    private static final Map<Integer, Integer> TIERS = new HashMap<>();
    private static final int[] MEDALS = {4587, 4589, 4588, 4590};
    private OfflineMarket() {}
    public static boolean isMerchant(Player player) { return TIERS.containsKey(player.id); }

    public static void populate() {
        for (map.Map[] zones : map.Map.entrys) {
            if (zones.length == 0) continue;
            String name = Normalizer.normalize(zones[0].name, Normalizer.Form.NFD)
                    .replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT);
            if (!name.contains("khu mua ban")) continue;
            try {
                Session session = new Session(null) { @Override public void addmsg(Message message) {} };
                Player model = new Player(session, 29990);
                model.level = 100;
                for (map.Map market : zones) {
                    List<Integer> tiers = new ArrayList<>(List.of(6, 7, 8, 9, 10));
                    Collections.shuffle(tiers);
                    synchronized (market) {
                        for (int position = 0; position < tiers.size(); position++) {
                            int tier = tiers.get(position);
                            Player seller = LoiDai.createOpponent(model, 30010 + market.zone_id * 5 + position);
                            seller.name = "Mề đay +" + tier;
                            seller.typepk = -1;
                            seller.my_store_name = "Mề đay +" + tier + " • 4 phái";
                            seller.map = market;
                            seller.x = (short) (150 + position * 65);
                            seller.y = 200;
                            seller.my_store = new ArrayList<>();
                            TIERS.put(seller.id, tier);
                            market.players.add(seller);
                        }
                    }
                }
                System.out.println("HSO_MEDAL_MERCHANTS map=" + zones[0].map_id + " count=" + TIERS.size());
            } catch (IOException error) {
                throw new IllegalStateException("Cannot initialize medal merchants", error);
            }
            return;
        }
        throw new IllegalStateException("Missing Khu Mua Bán map");
    }

    private static Item3 medal(int clazz, int tier) {
        ItemSellCoin offer = ItemSellCoin.entry.stream().filter(row -> row.id == MEDALS[clazz]).findFirst().orElseThrow();
        Item3 item = offer.createItem();
        item.clazz = (byte) clazz;
        item.tier = (byte) tier;
        item.color = 5;
        item.level = 1;
        item.op = new ArrayList<>(List.of(new Option(Item3.getClassDamageOptionId((byte) clazz), 800),
                new Option(7, 1000), new Option(8 + new int[]{1,3,0,2}[clazz], 1500),
                new Option(27, 1500), new Option(28, 1000), new Option(37, 2), new Option(33, 1000)));
        return item;
    }

    public static Item3 lotteryMedal(int clazz) {
        Item3 item = medal(clazz, 15);
        item.op = new ArrayList<>(List.of(new Option(Item3.getClassDamageOptionId((byte) clazz), 599),
                new Option(27, 1000), new Option(29, 500), new Option(37, 3), new Option(38, 3),
                new Option(80, 50), new Option(33, 500), new Option(81, 5), new Option(82, 50),
                new Option(87, 50), new Option(88, 3), new Option(8 + new int[]{1,3,0,2}[clazz], 900),
                new Option(76, 500), new Option(77, 5)));
        return item;
    }

    public static boolean view(Session connection, Player seller) throws IOException {
        Integer tier = seller == null ? null : TIERS.get(seller.id);
        if (tier == null) return false;
        if (seller.map != connection.p.map) return true;
        Message packet = new Message(23);
        packet.writer().writeUTF(seller.my_store_name);
        packet.writer().writeByte(17);
        packet.writer().writeShort(4);
        for (int clazz = 0; clazz < 4; clazz++) {
            Item3 item = medal(clazz, tier);
            packet.writer().writeByte(3);
            packet.writer().writeShort(item.id);
            packet.writer().writeUTF(item.name);
            packet.writer().writeByte(item.clazz);
            packet.writer().writeByte(item.type);
            packet.writer().writeShort(item.icon);
            packet.writer().writeByte(item.tier);
            packet.writer().writeShort(item.level);
            packet.writer().writeByte(item.color);
            packet.writer().writeByte(item.op.size() + 1);
            for (Option option : item.op) {
                packet.writer().writeByte(option.id);
                packet.writer().writeInt(option.getParam(item.tier));
            }
            packet.writer().writeByte(70);
            packet.writer().writeInt(price(tier));
            packet.writer().writeByte(0); // currency; price is already sent in option 70
        }
        packet.writer().writeShort(seller.id);
        connection.addmsg(packet);
        packet.cleanup();
        return true;
    }

    private static int price(int tier) { return (tier - 5) * 1000; }

    public static boolean buy(Session connection, Player seller, short itemId, byte category) throws IOException {
        Integer tier = seller == null ? null : TIERS.get(seller.id);
        if (tier == null) return false;
        if (seller.map != connection.p.map || category != 3) return true;
        int clazz = -1;
        for (int i = 0; i < MEDALS.length; i++) if (MEDALS[i] == itemId) clazz = i;
        if (clazz < 0) return true;
        synchronized (connection.p) {
            if (connection.p.item.get_bag_able() < 1) {
                Service.send_notice_box(connection, "Hành trang đầy.");
            } else if (connection.p.get_vang() < price(tier)) {
                Service.send_notice_box(connection, "Bạn cần " + price(tier) + " vàng.");
            } else if (connection.p.item.add_item_bag3(medal(clazz, tier))) {
                connection.p.update_vang(-price(tier));
                connection.p.item.char_inventory(3);
                connection.p.item.char_inventory(5);
                Service.send_notice_box(connection, "Đã mua mề đay +" + tier + ".");
            }
        }
        return true;
    }
}
