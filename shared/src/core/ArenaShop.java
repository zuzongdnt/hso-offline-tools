package core;

import client.Player;
import java.io.IOException;
import java.util.List;
import template.Item3;
import template.ItemSellCoin;
import template.ItemTemplate3;
import template.OfflineSkins;

/** The normal NPC menu keeps point purchases compatible with every client. */
public final class ArenaShop {
    private static final int PAGE_SIZE = 8;
    public static boolean contains(short id) {
        int type = ItemTemplate3.item.get(id).getType();
        return !OfflineSkins.removed(id) && !OfflineSkins.isCraftedArmor(id)
                && (type == 15 || type >= 21 && type <= 27);
    }
    private static List<ItemSellCoin> stock() {
        return ItemSellCoin.entry.stream().filter(row -> row.available() && contains(row.id)).collect(java.util.stream.Collectors.toList());
    }
    private static int price(ItemSellCoin offer) { return 300; }
    private static final java.util.Map<Integer, Integer> pages = new java.util.concurrent.ConcurrentHashMap<>();
    public static void show(Player p, int page) throws IOException {
        List<ItemSellCoin> stock = stock();
        int maxPage = Math.max(0, (stock.size() - 1) / PAGE_SIZE);
        page = Math.max(0, Math.min(page, maxPage));
        pages.put(p.id, page);
        java.util.List<String> labels = new java.util.ArrayList<>();
        labels.add("Điểm: " + p.point_active[2] + " · Trang " + (page + 1));
        for (int i = page * PAGE_SIZE; i < Math.min(stock.size(), (page + 1) * PAGE_SIZE); i++) {
            ItemSellCoin offer = stock.get(i);
            labels.add(ItemTemplate3.item.get(offer.id).getName() + " · " + price(offer) + " điểm");
        }
        labels.add("Trang trước"); labels.add("Trang sau"); labels.add("Đổi vàng và rương");
        MenuController.send_menu_select(p.conn, 12001, labels.toArray(new String[0]));
    }
    public static void select(Player p, int index) throws IOException {
        synchronized (p) {
            Integer page = pages.get(p.id);
            if (page == null) return;
            List<ItemSellCoin> stock = stock();
            int start = page * PAGE_SIZE;
            int count = Math.min(PAGE_SIZE, stock.size() - start);
            if (index == 0) { show(p, page); return; }
            if (index == count + 1) { show(p, page - 1); return; }
            if (index == count + 2) { show(p, page + 1); return; }
            if (index == count + 3) { event_daily.LoiDai.claimRankReward(p); return; }
            if (index < 1 || index > count) return;
            ItemSellCoin offer = stock.get(start + index - 1);
            if (p.point_active[2] < price(offer)) { Service.send_notice_box(p.conn, "Chưa đủ điểm Lôi đài."); return; }
            if (p.item.get_bag_able() < 1) { Service.send_notice_box(p.conn, "Hành trang đầy."); return; }
            Item3 item = offer.createItem();
            if (!p.item.add_item_bag3(item)) return;
            p.point_active[2] -= price(offer);
            p.flush(); p.item.char_inventory(3);
            Service.send_notice_box(p.conn, "Đã đổi " + item.name + ". Còn " + p.point_active[2] + " điểm.");
        }
    }
}
