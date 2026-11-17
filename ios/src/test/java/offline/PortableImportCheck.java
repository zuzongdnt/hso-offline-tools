package offline;

import core.SQL;
import core.SaveTransfer;
import java.nio.file.Files;
import java.nio.file.Path;

public final class PortableImportCheck {
    public static void main(String[] args) throws Exception {
        System.setProperty("hso.root", Path.of(args[0]).toAbsolutePath().toString());
        String incoming = Files.readString(Path.of(args[1]));
        SQL storage = SQL.gI();
        try {
            storage.importSave(incoming);
            if (!SaveTransfer.validate(incoming).equals(SaveTransfer.validate(storage.exportSave())))
                throw new AssertionError("Cross-platform save mismatch");
            System.out.println("PORTABLE_IMPORT_PASS every account/player/clan/wedding field matches");
        } finally {
            storage.close();
        }
    }
}
