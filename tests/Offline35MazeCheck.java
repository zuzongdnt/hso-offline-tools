package offline;

import client.Player;
import core.Manager;
import core.MazeRun;
import core.MenuController;
import core.SQL;
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
import template.Item47;

public final class Offline35MazeCheck {
    private static final class Capture extends Session {
        byte[] menu;

        Capture() {
            super(null);
            connected = true;
            zoomlv = 2;
        }

        @Override public void addmsg(Message message) {
            if (message.cmd == -30) menu = message.getData().clone();
        }
    }

    private static void check(boolean passed, String details) {
        if (!passed) throw new AssertionError(details);
    }

    private static void walk(Player player, int x, int y) throws Exception {
        Message move = new Message(4);
        move.writer().writeShort(x);
        move.writer().writeShort(y);
        MapService.send_move(player.map, player, new Message((byte) 4, move.getData()));
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        try {
            Manager.gI().init();
            var connection = new Capture();
            var player = LoiDai.createOpponent(new Player(connection, 120), 121, 59);
            connection.p = player;
            player.conn = connection;
            player.name = "Offline35MazeFixture";
            player.date = new Date();
            player.maxbag = 42;
            player.other_player_inside = new HashMap<>();
            player.other_mob_inside = new HashMap<>();
            player.other_mob_inside_update = new HashMap<>();
            player.item.bag47 = new ArrayList<>();
            player.item.bag3 = new Item3[42];
            Map home = Map.get_map_by_id(1)[0];
            player.map = home;

            Item47 ticket = new Item47();
            ticket.category = 4;
            ticket.id = 241;
            ticket.quantity = 1;
            player.item.bag47.add(ticket);
            MazeRun.enter(player, ticket.id);
            MazeRun run = player.maze;
            check(run != null && player.item.total_item_by_id(4, 241) == 0, "a ticket starts the run");
            for (int room = 0; room < run.rooms.length; room++) {
                check(player.map == run.rooms[room], "walking through a door reaches the next room");
                check(player.list_npc.isEmpty(), "the event does not display teleport stones");
                check(player.map.mobs.length == (room == 2 ? 4 : 0), "only the guard room has monsters");
                if (room == run.rooms.length - 1) break;
                var door = player.map.vgos.get(1);
                walk(player, player.x + 48, player.y);
                if (room == 2) {
                    walk(player, door.x_old, door.y_old);
                    check(player.map == run.rooms[room], "living guards block the door");
                    for (var mob : player.map.mobs) {
                        mob.hp = 0;
                        mob.isdie = true;
                    }
                }
                walk(player, door.x_old, door.y_old);
            }

            try (var menu = new DataInputStream(new ByteArrayInputStream(connection.menu))) {
                check(menu.readShort() == MazeRun.TREASURE_MENU, "the treasure menu opens by itself");
                menu.skipNBytes(2);
                check(menu.readUTF().equals("Nhặt Đèn Thần"), "claiming the lamp is the first choice");
            }
            Message choice = new Message(0);
            choice.writer().writeShort(MazeRun.TREASURE_MENU);
            choice.writer().writeByte(0);
            choice.writer().writeByte(0);
            MenuController.processmenu(connection, new Message((byte) 0, choice.getData()));
            check(player.maze == null && player.map == home && player.item.total_item_by_id(4, 242) == 1,
                    "the lamp is granted and the player returns home");
            System.out.println("OFFLINE35_PASS door movement, no stones, four guards, treasure");
        } catch (Throwable failure) {
            failure.printStackTrace();
            System.exit(1);
        } finally {
            if (SQL.is_connected) SQL.gI().close();
        }
        System.exit(0);
    }
}
