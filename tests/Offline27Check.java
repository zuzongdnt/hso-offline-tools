import client.Body;
import client.Item;
import client.Player;
import io.Session;
import java.util.ArrayList;
import template.Item3;
import template.Option;
import template.TinhTu;

public class Offline27Check {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) throws Exception {
        Session session = new Session(null);
        Player player = new Player(session, 30000);
        player.item = new Item(player);
        player.item.wear = new Item3[24];
        check(player.gemHitThreshold(402) == 0, "No Khải Hoàn gem must never activate");
        player.process_khai_hoan_hit();
        check(player.hit_count_ngoc_khai_hoan == 0, "No-gem hit counter changed");

        Item3 weapon = new Item3();
        weapon.op = new ArrayList<>();
        weapon.op.add(new Option(58, 382));
        weapon.op.add(new Option(59, 384));
        weapon.op.add(new Option(60, 385));
        player.item.wear[0] = weapon;
        check(player.gemHitThreshold(382) == 16, "Mixed Hỗn Nguyên sockets should average to 16 hits");
        check(player.gemHitThreshold(402) == 0, "Different gem must not count as Khải Hoàn");
        weapon.op.set(0, new Option(58, 402));
        check(player.gemHitThreshold(402) == 25, "Level 1 Khải Hoàn needs 25 hits");
        weapon.op.set(1, new Option(59, 406));
        check(player.gemHitThreshold(402) == 15, "Khải Hoàn sockets should average 25 and 5 hits");

        Item3 tinhTuWeapon = new Item3();
        tinhTuWeapon.id = 4672;
        tinhTuWeapon.color = 4;
        tinhTuWeapon.op = new ArrayList<>();
        tinhTuWeapon.op.add(new Option(170, 250));
        player.item.wear[0] = tinhTuWeapon;
        player.body = new Body(player);
        check(player.body.get_equipment_effect(170) == 0, "Chính xác must stay inactive without the full group");
        for (int slot : new int[]{3, 9}) {
            Item3 ring = new Item3();
            ring.id = 4669;
            ring.op = new ArrayList<>();
            player.item.wear[slot] = ring;
        }
        check(player.body.get_equipment_effect(170) == 250, "Chính xác must activate with weapon and two rings");
        check(TinhTu.displayedOption(170, false) == 195, "Inactive Chính xác should show its own label");
        check(TinhTu.displayedOption(170, true) == 170, "Active Chính xác should keep its effect label");
        System.out.println("Offline27Check OK");
    }
}
