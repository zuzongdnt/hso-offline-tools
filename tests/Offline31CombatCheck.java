package offline;

import ai.Player_Nhan_Ban;
import client.Player;
import core.CombatVisuals;
import core.Manager;
import core.SQL;
import event_daily.ChienTruong;
import event_daily.LoiDai;
import io.Message;
import io.Session;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.nio.file.Path;
import java.util.HashMap;
import map.Map;
import template.ItemSellCoin;

public final class Offline31CombatCheck {
    private static final class Capture extends Session {
        int removed, shown, walked;
        byte[] actor;

        Capture() { super(null); zoomlv = 1; connected = true; }

        @Override public void addmsg(Message message) {
            switch (message.cmd) {
                case 8 -> removed++;
                case 5 -> { shown++; actor = message.getData().clone(); }
                case 4 -> walked++;
                default -> { }
            }
        }
    }

    private static void check(boolean result, String detail) {
        if (!result) throw new AssertionError(detail);
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        try {
            Manager.gI().init();
            Capture connection = new Capture();
            Player seed = new Player(connection, 120);
            Player viewer = LoiDai.createOpponent(seed, 120, 59);
            viewer.conn = connection;
            connection.p = viewer;
            viewer.other_player_inside = new HashMap<>();
            Player opponent = LoiDai.createOpponent(viewer, 121, 59);
            Map arena = Map.get_map_by_id(102)[0];
            synchronized (arena) {
                opponent.map = viewer.map = arena;
                viewer.x = opponent.x = 288;
                viewer.y = opponent.y = 228;
                arena.players.add(viewer);
                arena.players.add(opponent);
                opponent.add_eff(-204, 1, -10);
                check(opponent.get_eff(-204) == null, "an expired buff cannot prevent combat");
                opponent.add_eff(-204, 1, 10_000);
                CombatVisuals.show(opponent, 17, 100);
                check(connection.removed == 1 && opponent.invisibilityHidden, "opponent hides for the viewer");
                CombatVisuals.restoreVisibility(opponent);
                check(connection.shown == 0, "visibility does not reset early");
                opponent.get_eff(-204).time = 0;
                CombatVisuals.restoreVisibility(opponent);
                check(connection.shown == 1 && !opponent.invisibilityHidden, "viewer receives the actor again");
                arena.players.clear();
            }

            ChienTruong battle = ChienTruong.gI();
            battle.setStatus(2);
            Player_Nhan_Ban.beginBattle(battle.list_ai);
            check(battle.list_ai.stream().filter(actor -> actor.roaming).count() == 8, "eight battlefield fighters");
            Player_Nhan_Ban guard = battle.list_ai.get(0);
            viewer.map = guard.map;
            viewer.x = guard.x;
            viewer.y = guard.y;
            battle.get_ai(viewer, guard.id);
            try (DataInputStream data = new DataInputStream(new ByteArrayInputStream(connection.actor))) {
                check(data.readShort() == guard.id && data.readUTF().equals("Lính canh"), "guard identity");
                data.skipNBytes(19);
                check(data.readUnsignedByte() == guard.flag(), "guard is represented with its own faction");
                data.skipNBytes(2);
                int count = data.readUnsignedByte();
                data.skipNBytes(count * 11L);
                data.skipNBytes(3);
                check(data.readUnsignedByte() == 7, "fashion part count");
                for (int i = 0; i < 7; i++) check(data.readShort() == -1, "fashion part serialized as a short");
            }
            Player_Nhan_Ban fighter = battle.list_ai.stream().filter(actor -> actor.roaming).findFirst().orElseThrow();
            Map field = fighter.map;
            synchronized (field) {
                viewer.map = field;
                viewer.x = fighter.x;
                viewer.y = fighter.y;
                viewer.typepk = (byte) fighter.flag();
                field.players.add(viewer);
                int oldShown = connection.shown;
                for (int i = 0; i < 8; i++) Player_Nhan_Ban.update(field);
                check(connection.shown > oldShown, "bot appears before movement");
                check(connection.walked > 0, "bot walks using position updates");
                field.players.clear();
            }
            battle.setStatus(0);
            var mask = ItemSellCoin.entry.stream().filter(offer -> offer.id == 4635).findFirst().orElseThrow().createItem();
            check(mask.tier == 15 && mask.level == 1 && mask.getParamByOptionId(7) == 5500
                    && mask.getParamByOptionId(37) == 3, "mask tooltip uses reference values");
            System.out.println("OFFLINE31_PASS combat visibility, battlefield packet, fighter movement and mask stats");
        } catch (Throwable failure) {
            failure.printStackTrace();
            System.exit(1);
        } finally {
            if (SQL.is_connected) SQL.gI().close();
        }
        System.exit(0);
    }
}
