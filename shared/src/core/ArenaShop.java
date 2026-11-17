package core;

import client.Player;
import io.Message;
import java.io.IOException;
import java.util.List;
import java.util.Set;
import template.Item3;
import template.ItemSellCoin;

/** Ten point rewards; other costumes remain available from the gold merchant. */
public final class ArenaShop {
    public static final byte SHOP_TYPE = 46;
    public static final int PRICE = 300;
    private static final Set<Integer> IDS = Set.of(4807,4808,4846,4847,4868,4869,4870,4871,4872,4688);
    public static boolean contains(short id) { return IDS.contains((int) id); }
    public static List<ItemSellCoin> stock() {
        return ItemSellCoin.entry.stream().filter(row -> contains(row.id) && row.available())
                .collect(java.util.stream.Collectors.toList());
    }
    public static void show(Player p, int page) throws IOException {
        p.conn.shopType = SHOP_TYPE;
        Message packet = new Message(23);
        packet.writer().writeUTF("Lôi đài · 300 điểm/món · Còn " + p.point_active[2] + " điểm");
        packet.writer().writeByte(1);
        List<ItemSellCoin> stock = stock(); packet.writer().writeShort(stock.size());
        for (ItemSellCoin offer : stock) {
            Item3 item = offer.createItem();
            packet.writer().writeShort(item.id);packet.writer().writeUTF(item.name + " · 300 điểm");
            packet.writer().writeByte(item.clazz);packet.writer().writeByte(item.type);
            packet.writer().writeShort(item.icon);
            // shortcut: stock clients only label gold/gems; show point cost in the title/name.
            packet.writer().writeLong(0);
            packet.writer().writeShort(item.level);packet.writer().writeByte(item.color);
            item.writeItemOptions(packet,p.clazz);packet.writer().writeByte(0);
        }
        p.conn.addmsg(packet);packet.cleanup();
    }
    public static void select(Player p,int index) throws IOException { show(p,0); }
    public static void buy(Player p, short id, int quantity) throws IOException {
        synchronized (p) {
            if (p.conn.shopType != SHOP_TYPE || quantity < 1 || !contains(id)) return;
            ItemSellCoin offer = stock().stream().filter(row -> row.id == id).findFirst().orElse(null);
            if (offer == null) return;
            long total = (long) PRICE * quantity;
            if (p.point_active[2] < total) { Service.send_notice_box(p.conn,"Chưa đủ điểm Lôi đài.");return; }
            if (p.item.get_bag_able() < quantity) { Service.send_notice_box(p.conn,"Hành trang đầy.");return; }
            for (int i=0;i<quantity;i++) {
                if (!p.item.add_item_bag3(offer.createItem())) break;
                p.point_active[2] -= PRICE;
            }
            p.flush();p.item.char_inventory(3);
            Service.send_notice_box(p.conn,"Đã đổi skin. Còn " + p.point_active[2] + " điểm Lôi đài.");
        }
    }
}
