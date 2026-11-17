package offline;

import core.SQL;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

public final class SQLiteCheck {
    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        try {
            try (Connection connection = SQL.gI().getConnection(); Statement statement = connection.createStatement()) {
                statement.executeUpdate("CREATE TABLE IF NOT EXISTS ios_storage_check (id INTEGER PRIMARY KEY, label TEXT)");
                if (args[1].equals("write")) {
                    try (PreparedStatement insert = connection.prepareStatement("INSERT INTO ios_storage_check VALUES (?,?)")) {
                        for (int index = 1; index <= 3; index++) {
                            insert.setInt(1, index);
                            insert.setNString(2, "Tiếng Việt " + index);
                            insert.executeUpdate();
                        }
                    }
                }
                try (Statement scrolling = connection.createStatement(ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY);
                        ResultSet rows = scrolling.executeQuery("SELECT * FROM ios_storage_check ORDER BY id")) {
                    if (!rows.last() || rows.getRow() != 3) throw new AssertionError("Character list scroll");
                    rows.afterLast();
                    for (int index = 3; index >= 1; index--) {
                        if (!rows.previous() || rows.getInt("id") != index
                                || !rows.getString("label").equals("Tiếng Việt " + index)) {
                            throw new AssertionError("SQLite Unicode/result order");
                        }
                    }
                }
            }
            SQL.gI().checkpoint();
            System.out.println("SQLite storage and scroll passed: " + args[1]);
        } finally {
            if (SQL.is_connected) SQL.gI().close();
        }
    }
}
