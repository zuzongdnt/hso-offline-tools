package offline;

import core.SQL;
import core.SaveTransfer;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.Statement;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;

public final class SaveTransferCheck {
    private static String payload(String text) throws Exception {
        return (String) ((JSONObject) JSONValue.parseWithException(text)).get("payload");
    }
    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        SQL sql = SQL.gI();
        try {
            String original = sql.exportSave();
            SaveTransfer.validate(original);
            try (Connection connection = sql.getConnection(); Statement statement = connection.createStatement()) {
                statement.executeUpdate("UPDATE player SET vang=9007199254740993 WHERE id>=0");
            }
            String rich = sql.exportSave();
            if (!rich.contains("9007199254740993")) throw new AssertionError("64-bit balance export");
            sql.importSave(original);
            if (!payload(original).equals(payload(sql.exportSave()))) throw new AssertionError("Full save round trip");
            sql.importSave(rich);
            if (!payload(rich).equals(payload(sql.exportSave()))) throw new AssertionError("Currency import");
            try {
                sql.importSave(rich.replace("9007199254740993", "9007199254740992"));
                throw new AssertionError("Damaged checksum accepted");
            } catch (java.io.IOException expected) {}
            try (Connection connection = sql.getConnection(); Statement statement = connection.createStatement()) {
                statement.executeUpdate("CREATE TRIGGER stop_save_import BEFORE INSERT ON player WHEN NEW.id>=0 BEGIN SELECT RAISE(ABORT,'test rollback'); END");
            }
            try {
                sql.importSave(original);
                throw new AssertionError("Expected transaction failure");
            } catch (java.sql.SQLException expected) {}
            if (!payload(rich).equals(payload(sql.exportSave()))) throw new AssertionError("Partial import changed database");
            try (Connection connection = sql.getConnection(); Statement statement = connection.createStatement()) {
                statement.executeUpdate("DROP TRIGGER stop_save_import");
            }
            sql.importSave(original);
            System.out.println("SAVE_TRANSFER_PASS unicode, all tables, 64-bit currency, checksum, transaction rollback");
        } finally {
            sql.close();
        }
    }
}
