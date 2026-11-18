package offline;

import client.Player;
import core.CombatMotion;
import core.CombatVisuals;
import core.Manager;
import core.SQL;
import core.SocketGems;
import event_daily.LoiDai;
import io.Message;
import io.Session;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import map.Map;
import map.MapService;
import template.Item3;
import template.Option;

public final class Offline36CombatCheck {
    private static final class Capture extends Session {
        byte[] visual;
        byte[] position;
        int removed;
        int visible;

        Capture() { super(null); connected = true; zoomlv = 2; }

        @Override public void addmsg(Message message) {
            switch (message.cmd) {
                case -49 -> visual = message.getData().clone();
                case 4 -> position = message.getData().clone();
                case 8 -> removed++;
                case 5 -> visible++;
                default -> { }
            }
        }
    }

    private static void check(boolean passed, String details) {
        if (!passed) throw new AssertionError(details);
    }

    private static Player fighter(int id, Capture capture) throws Exception {
        Player player = LoiDai.createOpponent(new Player(capture, id), id, 59);
        player.conn = capture;
        capture.p = player;
        player.date = new Date();
        player.other_player_inside = new HashMap<>();
        player.other_mob_inside = new HashMap<>();
        player.other_mob_inside_update = new HashMap<>();
        return player;
    }

    private static void effect(Capture capture, int image, int target, int mode) throws Exception {
        try (var packet = new DataInputStream(new ByteArrayInputStream(capture.visual))) {
            check(packet.readUnsignedByte() == 2, "skill visual packet");
            packet.skipNBytes(packet.readUnsignedShort() + 2);
            check(packet.readUnsignedByte() == image && packet.readShort() == target, "image is on the right actor");
            check(packet.readByte() == 0 && packet.readUnsignedByte() == mode, "native movement mode");
        }
    }

    private static void move(Player player, int x, int y) throws Exception {
        Message input = new Message(4);
        input.writer().writeShort(x);
        input.writer().writeShort(y);
        MapService.send_move(player.map, player, new Message((byte) 4, input.getData()));
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        try {
            Manager.gI().init();
            var owner = new Capture();
            var opponent = new Capture();
            Player player = fighter(121, owner);
            Player bot = fighter(122, opponent);
            Map home = Map.get_map_by_id(1)[0];
            player.map = home;
            LoiDai.startChallenge(player, bot, 20);
            var challenge = player.map.ld;
            player.map.stop_map();
            check(player.map.map_id == 36 && challenge.challengeRank == 20, "rank challenge uses the reference arena");
            challenge.ready();
            effect(owner, 16, player.id, 1);
            short x = player.x, y = player.y;
            move(player, x + 15, y);
            check(player.x == x && player.y == y, "countdown rejects movement");

            challenge.state_ld = 1;
            CombatVisuals.confuse(player, 3000);
            effect(opponent, 14, player.id, 0);
            move(player, x + 12, y);
            check(player.x == x - 12 && player.y == y, "confusion reverses input");
            int mana = player.mp;
            MapService.use_skill(player.map, owner, new Message((byte) 6, new byte[0]), 1);
            check(player.mp == mana, "confusion blocks an attack before spending mana");
            player.get_eff(-205).time = 0;
            move(player, x, y);
            check(player.x == x, "normal movement resumes after confusion");

            int oldBotX = bot.x;
            CombatMotion.push(player, bot);
            check(bot.x > oldBotX && CombatMotion.walkable(bot.map, bot.x, bot.y), "push moves away across walkable ground");
            check(Byte.toUnsignedInt(owner.position[owner.position.length - 1]) == 127, "native push animation is sent");
            move(bot, oldBotX, bot.y);
            check(bot.x > oldBotX, "client input cannot cancel a push in progress");

            player.add_eff(-204, 1, 3000);
            CombatVisuals.hide(player, 3000);
            effect(owner, 54, player.id, 17);
            check(opponent.removed == 1, "the opponent loses sight of the hidden player");
            opponent.position = null;
            move(player, x + 5, y);
            check(opponent.position == null, "hidden movement does not recreate the actor");
            player.get_eff(-204).time = 0;
            int visible = opponent.visible;
            CombatVisuals.restoreVisibility(player);
            check(opponent.visible == visible + 1, "the hidden actor returns when the effect expires");

            Item3 equipment = new Item3();
            equipment.op = new ArrayList<>();
            for (int i = 0; i < 30; i++) equipment.op.add(new Option(58, 366));
            equipment.op.add(new Option(59, 361));
            equipment.op.add(new Option(60, 356));
            player.item.wear = new Item3[24];
            player.item.wear[0] = equipment;
            SocketGems.absorb(player);
            effect(owner, 20, player.id, 0);
            player.hit_count_ngoc_khai_hoan = 4;
            SocketGems.khai(player);
            effect(owner, 22, player.id, 0);
            player.hit_count_ngoc_hon_nguyen = 4;
            SocketGems.hon(player);
            effect(owner, 18, player.id, 0);
            System.out.println("OFFLINE36_PASS map, countdown, confusion, push, invisibility, socket images");
        } catch (Throwable failure) {
            failure.printStackTrace();
            System.exit(1);
        } finally {
            if (SQL.is_connected) SQL.gI().close();
        }
        System.exit(0);
    }
}
