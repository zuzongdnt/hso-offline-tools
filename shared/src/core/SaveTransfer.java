package core;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;

/** Portable character saves. World templates always come from the installed game. */
public final class SaveTransfer {
    public static final int LIMIT = 32 * 1024 * 1024;
    private static final Map<String, String[]> TABLES = new LinkedHashMap<>();
    static {
        TABLES.put("account", columns("id user pass char status lock coin phone ip tiennap pass2 tongnap checkmocnap"));
        TABLES.put("clan", columns("id name name_short mems level exp slogan rule notice vang kimcuong max_mem icon item"));
        TABLES.put("wedding", columns("id name item"));
        TABLES.put("player", columns("id name body clazz maxbag diemdanh typeexp level exp site dquest rms_save nvtt tinhtu_material friend eff enemies skill item3 item4 item5 item7 itembox3 itembox4 itembox5 itembox7 itemwear pet vang kimcuong tiemnang kynang point1 point2 point3 point4 giftcode date medal_create_material point_active chucphuc hieuchien id_name chuyensinh tutien pointarena dropnlmd detu"));
    }

    private SaveTransfer() {}
    private static String[] columns(String text) { return text.split(" "); }
    private static String quoted(String[] names) { return "`" + String.join("`,`", names) + "`"; }
    private static String digest(String data) throws Exception {
        byte[] hash = MessageDigest.getInstance("SHA-256").digest(data.getBytes(StandardCharsets.UTF_8));
        StringBuilder text = new StringBuilder();
        for (byte value : hash) text.append(Integer.toHexString((value & 255) | 256).substring(1));
        return text.toString();
    }

    @SuppressWarnings("unchecked")
    public static String capture(Connection connection) throws Exception {
        JSONObject tables = new JSONObject();
        for (var entry : TABLES.entrySet()) {
            JSONArray rows = new JSONArray();
            String filter = entry.getKey().equals("player") ? " WHERE id >= 0" : "";
            try (Statement statement = connection.createStatement(); ResultSet result = statement.executeQuery(
                    "SELECT " + quoted(entry.getValue()) + " FROM `" + entry.getKey() + "`" + filter + " ORDER BY id")) {
                while (result.next()) {
                    JSONArray row = new JSONArray();
                    // Strings preserve 64-bit currency exactly on every platform.
                    for (String column : entry.getValue()) row.add(result.getString(column));
                    rows.add(row);
                }
            }
            tables.put(entry.getKey(), rows);
        }
        String payload = tables.toJSONString();
        JSONObject envelope = new JSONObject();
        envelope.put("format", "hso-save-v1");
        envelope.put("created", System.currentTimeMillis());
        envelope.put("payload", payload);
        envelope.put("sha256", digest(payload));
        return envelope.toJSONString();
    }

    public static JSONObject validate(String text) throws Exception {
        if (text.getBytes(StandardCharsets.UTF_8).length > LIMIT) throw new IOException("File sao lưu quá lớn.");
        Object parsed = JSONValue.parseWithException(text);
        if (!(parsed instanceof JSONObject envelope) || !"hso-save-v1".equals(envelope.get("format"))
                || !(envelope.get("payload") instanceof String payload)
                || !digest(payload).equals(envelope.get("sha256")))
            throw new IOException("File sao lưu sai định dạng hoặc bị hỏng.");
        Object data = JSONValue.parseWithException(payload);
        if (!(data instanceof JSONObject tables) || !tables.keySet().equals(TABLES.keySet()))
            throw new IOException("File thiếu bảng dữ liệu.");
        for (var entry : TABLES.entrySet()) {
            if (!(tables.get(entry.getKey()) instanceof JSONArray rows)) throw new IOException("Bảng dữ liệu không hợp lệ.");
            Set<Long> ids = new HashSet<>();
            for (Object value : rows) {
                if (!(value instanceof JSONArray row) || row.size() != entry.getValue().length)
                    throw new IOException("Phiên bản dữ liệu chưa tương thích.");
                for (Object cell : row) if (cell != null && !(cell instanceof String))
                    throw new IOException("Giá trị sao lưu không hợp lệ.");
                long id = Long.parseLong((String) row.get(0));
                if (id < 0 || !ids.add(id)) throw new IOException("ID dữ liệu không hợp lệ.");
                if (entry.getKey().equals("player")) {
                    int level = Integer.parseInt((String) row.get(7));
                    int clazz = Integer.parseInt((String) row.get(3));
                    if (level < 1 || level > 32767 || clazz < 0 || clazz > 3)
                        throw new IOException("Nhân vật không hợp lệ.");
                }
            }
        }
        return tables;
    }

    public static void replace(Connection connection, String text) throws Exception {
        JSONObject tables = validate(text);
        Map<String, String> localPasswords = new LinkedHashMap<>();
        try (Statement statement = connection.createStatement();
                ResultSet result = statement.executeQuery("SELECT `user`, `pass` FROM `account`")) {
            while (result.next()) localPasswords.put(result.getString(1), result.getString(2));
        }
        // The caller owns a real transaction and invokes this before loading any players.
        for (var entry : TABLES.entrySet()) {
            String table = entry.getKey();
            try (Statement statement = connection.createStatement()) {
                statement.executeUpdate("DELETE FROM `" + table + "`" + (table.equals("player") ? " WHERE id >= 0" : ""));
            }
            String[] markers = new String[entry.getValue().length];
            Arrays.fill(markers, "?");
            String sql = "INSERT INTO `" + table + "` (" + quoted(entry.getValue()) + ") VALUES ("
                    + String.join(",", markers) + ")";
            try (PreparedStatement statement = connection.prepareStatement(sql)) {
                for (Object value : (JSONArray) tables.get(table)) {
                    JSONArray row = (JSONArray) value;
                    for (int i = 0; i < row.size(); i++) statement.setString(i + 1, (String) row.get(i));
                    if (table.equals("account")) {
                        String user = (String) row.get(1);
                        if (localPasswords.containsKey(user)) statement.setString(3, localPasswords.get(user));
                    }
                    statement.executeUpdate();
                }
            }
        }
    }
}
