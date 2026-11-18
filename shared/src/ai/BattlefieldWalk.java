package ai;

import core.Util;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.concurrent.ConcurrentHashMap;
import map.Map;

/** Walk only through connected ground tiles in the offline battlefield. */
final class BattlefieldWalk {
    private static final ConcurrentHashMap<Byte, BattlefieldWalk> MAPS = new ConcurrentHashMap<>();
    private final int width, height;
    private final boolean[] ground;

    static BattlefieldWalk of(Map map) throws IOException {
        BattlefieldWalk existing = MAPS.get(map.map_id);
        if (existing != null) return existing;
        BattlefieldWalk grid = new BattlefieldWalk(Util.loadfile("data/mapnew/" + map.map_id));
        BattlefieldWalk prior = MAPS.putIfAbsent(map.map_id, grid);
        return prior == null ? grid : prior;
    }

    private BattlefieldWalk(byte[] data) throws IOException {
        try (DataInputStream stream = new DataInputStream(new ByteArrayInputStream(data))) {
            stream.readShort();
            stream.readUTF();
            int length = stream.readUnsignedShort();
            width = stream.readUnsignedByte();
            height = stream.readUnsignedByte();
            int tileset = stream.readUnsignedByte();
            int limit = switch (tileset) {
                case 0 -> 26;
                case 1 -> 23;
                case 2 -> 16;
                case 4 -> 14;
                case 6 -> 30;
                default -> throw new IOException("Unknown battlefield tileset " + tileset);
            };
            if (width * height + 3 > length) throw new IOException("Incomplete battlefield map");
            ground = new boolean[width * height];
            for (int i = 0; i < ground.length; i++) {
                int tile = stream.readUnsignedByte();
                ground[i] = tile > 0 && tile < limit;
            }
        }
    }

    int nearest(int x, int y) {
        int best = -1, distance = Integer.MAX_VALUE;
        for (int i = 0; i < ground.length; i++) {
            if (!ground[i]) continue;
            int delta = Math.abs(x - x(i)) + Math.abs(y - y(i));
            if (delta < distance) {
                distance = delta;
                best = i;
            }
        }
        return best;
    }

    int x(int cell) { return cell % width * 24 + 12; }
    int y(int cell) { return cell / width * 24 + 12; }

    ArrayDeque<Integer> route(int start, int target) {
        ArrayDeque<Integer> path = new ArrayDeque<>();
        if (start < 0 || target < 0 || start == target) return path;
        int[] previous = new int[ground.length];
        Arrays.fill(previous, -1);
        int[] queue = new int[ground.length];
        queue[0] = start;
        previous[start] = start;
        int end = 1;
        for (int next = 0; next < end && previous[target] < 0; next++) {
            int cell = queue[next], col = cell % width, row = cell / width;
            for (int neighbor : new int[]{col > 0 ? cell - 1 : -1, col + 1 < width ? cell + 1 : -1,
                    row > 0 ? cell - width : -1, row + 1 < height ? cell + width : -1}) {
                if (neighbor >= 0 && ground[neighbor] && previous[neighbor] < 0) {
                    previous[neighbor] = cell;
                    queue[end++] = neighbor;
                }
            }
        }
        if (previous[target] >= 0) {
            for (int cell = target; cell != start; cell = previous[cell]) path.addFirst(cell);
        }
        return path;
    }
}
