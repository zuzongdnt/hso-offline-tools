package offline;

import core.SQL;
import core.SaveTransfer;
import java.nio.file.Files;
import java.nio.file.Path;
import org.json.simple.JSONArray;

public final class Save25Check {
    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        String incoming = Files.readString(Path.of(args[1]));
        var source = SaveTransfer.validate(incoming);
        var accounts = (JSONArray) source.get("account");
        if (accounts.isEmpty()) throw new AssertionError("Use a backup with an account");
        SQL sql = SQL.gI();
        try {
            sql.importSave(incoming);
            if (!source.equals(SaveTransfer.validate(sql.exportSave())))
                throw new AssertionError("A new account must retain its source login and character");

            var first = (JSONArray) accounts.get(0);
            String localPassword = "LocalRestoreCheck25";
            try (var connection = sql.getConnection();
                    var update = connection.prepareStatement("UPDATE account SET pass = ? WHERE id = ?")) {
                update.setString(1, localPassword);
                update.setString(2, (String) first.get(0));
                if (update.executeUpdate() != 1) throw new AssertionError("Test account is missing");
            }
            sql.importSave(incoming);
            first.set(2, localPassword);
            if (!source.equals(SaveTransfer.validate(sql.exportSave())))
                throw new AssertionError("Re-import must keep the existing login and restore every other field");
            System.out.println("SAVE25_PASS legacy file, original login for new accounts, existing login for matching accounts");
        } finally {
            sql.close();
        }
    }
}
