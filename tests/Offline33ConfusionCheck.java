package offline;

import client.Player;
import core.CombatVisuals;
import core.Manager;
import core.SQL;
import event_daily.LoiDai;
import io.Message;
import io.Session;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.nio.file.Path;
import map.Map;
import map.MapService;

public final class Offline33ConfusionCheck {
    private static final class Capture extends Session {
        byte[] effect;
        byte[] position;
        int positionCount;

        Capture() {
            super(null);
            zoomlv = 2;
            connected = true;
        }

        @Override public void addmsg(Message message) {
            if (message.cmd == -49) effect = message.getData().clone();
            if (message.cmd == 4) {
                position = message.getData().clone();
                positionCount++;
            }
        }
    }

    private static void check(boolean passed, String details) {
        if (!passed) throw new AssertionError(details);
    }

    private static void checkPosition(Capture capture, Player victim) throws Exception {
        try (var packet = new DataInputStream(new ByteArrayInputStream(capture.position))) {
            packet.skipNBytes(3);
            check(packet.readShort() == victim.id, "movement is applied to the victim");
            check(packet.readShort() == victim.x && packet.readShort() == victim.y, "position matches the server");
        }
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        try {
            Manager.gI().init();
            var viewerConnection = new Capture();
            var victimConnection = new Capture();
            var seed = new Player(viewerConnection, 120);
            Player viewer = LoiDai.createOpponent(seed, 120, 59);
            Player victim = LoiDai.createOpponent(viewer, 121, 59);
            viewerConnection.p = viewer;
            victimConnection.p = victim;
            viewer.conn = viewerConnection;
            victim.conn = victimConnection;
            Map arena = Map.get_map_by_id(102)[0];
            viewer.map = victim.map = arena;
            viewer.x = victim.x = 288;
            viewer.y = victim.y = 228;
            synchronized (arena) {
                arena.players.add(viewer);
                arena.players.add(victim);
                victim.add_eff(-211, 1, 3000);
                CombatVisuals.confuse(victim, 3000);
                check(viewerConnection.effect == null && victimConnection.effect == null,
                        "immune actors do not receive the confusion visual");
                victim.get_eff(-211).time = 0;
                CombatVisuals.confuse(victim, 3000);
                try (var packet = new DataInputStream(new ByteArrayInputStream(viewerConnection.effect))) {
                    check(packet.readUnsignedByte() == 2, "native animation packet");
                    packet.skipNBytes(packet.readUnsignedShort());
                    packet.skipNBytes(2);
                    check(packet.readUnsignedByte() == 14, "question mark animation");
                    check(packet.readShort() == victim.id, "the mark is attached to the victim");
                    packet.skipNBytes(2);
                    check(packet.readInt() == 3000, "client receives the exact duration");
                }

                CombatVisuals.moveConfused(victim);
                short upper = victim.y;
                checkPosition(viewerConnection, victim);
                checkPosition(victimConnection, victim);
                CombatVisuals.moveConfused(victim);
                short lower = victim.y;
                CombatVisuals.moveConfused(victim);
                check(upper < lower && victim.y == upper && victim.x == 288 && victim.y / 24 == 228 / 24,
                        "the victim alternates vertically inside the original tile");

                Message input = new Message(4);
                input.writer().writeShort(318);
                input.writer().writeShort(258);
                MapService.send_move(arena, victim, new Message((byte) 4, input.getData()));
                check(victim.x == 288 && victim.y == upper, "manual movement is blocked during confusion");

                victim.get_eff(-205).time = 0;
                int packets = viewerConnection.positionCount;
                CombatVisuals.moveConfused(victim);
                check(viewerConnection.positionCount == packets, "involuntary movement stops on expiry");
                check(victim.get_eff(-205) == null, "expired confusion no longer blocks control");
                arena.players.clear();
            }
            System.out.println("OFFLINE33_PASS victim question mark, movement, expiry and immunity");
        } catch (Throwable failure) {
            failure.printStackTrace();
            System.exit(1);
        } finally {
            if (SQL.is_connected) SQL.gI().close();
        }
        System.exit(0);
    }
}
