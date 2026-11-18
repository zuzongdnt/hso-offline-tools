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
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import map.Map;
import template.Item3;
import template.Item47;

public final class Offline34MazeCheck {
    private static final class Capture extends Session {
        int stones;

        Capture() {
            super(null);
            connected = true;
            zoomlv = 2;
        }

        @Override public void addmsg(Message message) {
            if (message.cmd != -50) return;
            try (var packet = new DataInputStream(new ByteArrayInputStream(message.getData()))) {
                if (packet.readUnsignedByte() == 1 && packet.readUTF().equals("Đá dịch chuyển")) {
                    packet.readUTF();
                    check(packet.readByte() == -55 && packet.readByte() == 21, "native teleport stone graphic");
                    stones++;
                }
            } catch (java.io.IOException badPacket) {
                throw new AssertionError(badPacket);
            }
        }
    }

    private static void check(boolean passed, String details) {
        if (!passed) throw new AssertionError(details);
    }

    private static void useStone(Player player, int choice, boolean nearby) throws Exception {
        var stone = player.list_npc.stream().filter(npc -> npc.id == MazeRun.STONE_NPC).findFirst().orElseThrow();
        player.x = (short) (stone.x + (nearby ? 0 : 120));
        player.y = stone.y;
        MenuController.request_menu(player.conn, new Message((byte) 0, new byte[]{MazeRun.STONE_NPC}));
        Message response = new Message(0);
        response.writer().writeShort(MazeRun.STONE_MENU);
        response.writer().writeByte(0);
        response.writer().writeByte(choice);
        MenuController.processmenu(player.conn, new Message((byte) 0, response.getData()));
    }

    private static void checkSpawn(Player player, Path root) throws Exception {
        try (var mapData = new DataInputStream(Files.newInputStream(root.resolve("data/mapnew/" + player.map.map_id)))) {
            mapData.readShort();
            mapData.readUTF();
            mapData.readUnsignedShort();
            int width = mapData.readUnsignedByte();
            int height = mapData.readUnsignedByte();
            check(player.x >= 0 && player.x < width * 24 && player.y >= 0 && player.y < height * 24,
                    "start position is inside the map");
        }
    }

    public static void main(String[] args) throws Exception {
        Path root = Path.of(args[0]).toAbsolutePath();
        System.setProperty("hso.root", root.toString());
        try {
            Manager.gI().init();
            var connection = new Capture();
            var player = LoiDai.createOpponent(new Player(connection, 120), 121, 59);
            player.conn = connection;
            connection.p = player;
            player.name = "Offline34MazeFixture";
            player.date = new Date();
            player.id_dua_be = -1;
            player.maxbag = 42;
            player.other_player_inside = new HashMap<>();
            player.other_mob_inside = new HashMap<>();
            player.other_mob_inside_update = new HashMap<>();
            player.item.bag47 = new ArrayList<>();
            player.item.bag3 = new Item3[42];
            var home = Map.get_map_by_id(1)[0];
            player.map = home;

            Item47 ticket = new Item47();
            ticket.category = 4;
            ticket.id = 241;
            ticket.quantity = 1;
            player.item.bag47.add(ticket);
            MazeRun.enter(player, ticket.id);
            var run = player.maze;
            check(run != null && connection.stones == 1, "ticket starts the event and displays a stone");
            check(player.item.total_item_by_id(4, 241) == 0, "one ticket consumed");
            checkSpawn(player, root);

            useStone(player, 0, false);
            check(player.map == run.rooms[0], "cannot choose a route away from the stone");
            for (int room = 0; room < run.rooms.length; room++) {
                check(player.map == run.rooms[room], "stone leads to the correct room");
                check(player.map.mobs.length == (room == 2 ? 4 : 0), "only the guardian room has monsters");
                if (room == 2) {
                    useStone(player, 0, true);
                    check(player.map == run.rooms[2], "live guards block progress");
                    for (var mob : player.map.mobs) {
                        mob.hp = 0;
                        mob.isdie = true;
                    }
                }
                useStone(player, 0, true);
                if (player.maze != null) checkSpawn(player, root);
            }
            check(connection.stones == 6, "all six rooms display a working stone");
            check(player.maze == null && player.map == home, "the lamp returns the player home");
            check(player.item.total_item_by_id(4, 242) == 1, "the awarded lamp is in the bag");
            run.claim();
            check(player.item.total_item_by_id(4, 242) == 1, "the lamp cannot be taken twice");
            System.out.println("OFFLINE34_PASS maze ticket, stones, four guards, treasure");
        } catch (Throwable failure) {
            failure.printStackTrace();
            System.exit(1);
        } finally {
            if (SQL.is_connected) SQL.gI().close();
        }
        System.exit(0);
    }
}
