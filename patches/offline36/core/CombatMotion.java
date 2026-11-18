package core;

import client.Player;
import io.Message;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;
import map.Map;
import map.MapService;

public final class CombatMotion {
    private static final int TILE = 24;
    private static final int[] BLOCKED_FROM = {39, 35, 19, 33, 20, 9, 35, 35, 17, 19, 5, 21, 34, 47, 26, 9, 42};
    private static final ConcurrentHashMap<Byte, Ground> GROUND = new ConcurrentHashMap<>();
    private static final int NATIVE_PUSH = 127;

    private CombatMotion() {}

    public static void position(Player player, boolean ownerOnly, boolean knockback) throws IOException {
        Message packet = new Message(4);
        packet.writer().writeByte(0);
        packet.writer().writeShort(0);
        packet.writer().writeShort(player.id);
        packet.writer().writeShort(player.x);
        packet.writer().writeShort(player.y);
        packet.writer().writeByte(knockback ? NATIVE_PUSH : -1);
        if (ownerOnly || player.invisibilityHidden) player.conn.addmsg(packet);
        else MapService.send_msg_player_inside(player.map, player, packet, true);
        packet.cleanup();
    }

    public static void reverse(Player player, short inputX, short inputY) throws IOException {
        int dx = Math.max(-TILE, Math.min(TILE, player.x - inputX));
        int dy = Math.max(-TILE, Math.min(TILE, player.y - inputY));
        displace(player, dx, dy);
        position(player, false, false);
    }

    public static void push(Player attacker, Player target) throws IOException {
        if (target.isdie || target.hp <= 0 || target.knockbackUntil > System.currentTimeMillis()) return;
        int dx = target.x - attacker.x;
        int dy = target.y - attacker.y;
        double distance = Math.hypot(dx, dy);
        if (distance == 0 || !displace(target, (int) Math.round(38 * dx / distance),
                (int) Math.round(38 * dy / distance))) return;
        target.knockbackUntil = System.currentTimeMillis() + 350;
        position(target, false, true);
    }

    public static boolean walkable(Map map, int x, int y) throws IOException {
        Ground ground = GROUND.get(map.map_id);
        if (ground == null) {
            ground = Ground.load(map.map_id);
            GROUND.putIfAbsent(map.map_id, ground);
        }
        return ground.walkable(x, y);
    }

    private static boolean displace(Player player, int dx, int dy) throws IOException {
        int x = player.x, y = player.y;
        int steps = Math.max(Math.abs(dx), Math.abs(dy));
        for (int step = 1; step <= steps; step++) {
            int nx = x + dx * step / steps, ny = y + dy * step / steps;
            if (!walkable(player.map, nx, ny)) break;
            player.x = (short) nx;
            player.y = (short) ny;
        }
        return player.x != x || player.y != y;
    }

    private record Ground(int width, int height, int blockedFrom, byte[] tiles) {
        static Ground load(int map) throws IOException {
            byte[] data = Util.loadfile("data/mapnew/" + map);
            try (var input = new DataInputStream(new ByteArrayInputStream(data))) {
                input.readShort();
                input.readUTF();
                int sectionLength = input.readUnsignedShort();
                int width = input.readUnsignedByte(), height = input.readUnsignedByte();
                int tileset = input.readUnsignedByte();
                if (tileset >= BLOCKED_FROM.length || width * height + 3 > sectionLength) {
                    throw new IOException("Invalid movement tiles for map " + map);
                }
                byte[] tiles = new byte[width * height];
                input.readFully(tiles);
                return new Ground(width, height, BLOCKED_FROM[tileset], tiles);
            }
        }

        boolean walkable(int x, int y) {
            if (x < 0 || y < 0 || x >= width * TILE || y >= height * TILE) return false;
            int tile = Byte.toUnsignedInt(tiles[(y / TILE) * width + x / TILE]);
            return tile > 0 && tile < blockedFrom;
        }
    }
}
