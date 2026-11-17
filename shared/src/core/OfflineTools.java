package core;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;

/** Local-only backup and release UI used by the three platform launchers. */
public final class OfflineTools {
    public static final int VERSION = 26;
    private static final int PORT = Manager.gI().server_port == 19140 ? 19141 : 19140;
    public static final String ADDRESS = "http://127.0.0.1:" + PORT + "/";
    private static final String RELEASE = "https://github.com/zuzongdnt/hso-offline-tools/releases/latest/download/update.json";
    private static final String TOKEN = UUID.randomUUID().toString();
    private static volatile String latest = "{}";
    private static boolean started;

    private OfflineTools() {}
    private static Path root() { return new File(System.getProperty("hso.root", ".")).toPath(); }

    public static void restorePending() throws Exception {
        Path pending = root().resolve("import-pending.hsosave");
        if (!Files.isRegularFile(pending)) return;
        Path backups = root().resolve("backups");
        Files.createDirectories(backups);
        String stamp = Long.toString(System.currentTimeMillis());
        try {
            if (Files.size(pending) > SaveTransfer.LIMIT) throw new IOException("File vượt quá 32 MB.");
            String text = new String(Files.readAllBytes(pending), StandardCharsets.UTF_8);
            JSONObject restored = SaveTransfer.validate(text);
            Files.write(backups.resolve("before-import-" + stamp + ".hsosave"),
                    SQL.gI().exportSave().getBytes(StandardCharsets.UTF_8));
            SQL.gI().importSave(text);
            String selectedAccount = OfflineLogin.remember(restored);
            Files.move(pending, backups.resolve("imported-" + stamp + ".hsosave"));
            Files.write(root().resolve("restore-result.txt"), ("Khôi phục thành công. Tài khoản được chọn: " + selectedAccount
                    + ". Mở lại game và bấm Chơi mới để vào tài khoản vừa khôi phục; Đổi tài khoản vẫn dùng thông tin trong file.").getBytes(StandardCharsets.UTF_8));
            System.out.println("HSO_SAVE_IMPORTED " + stamp);
        } catch (Exception error) {
            Files.move(pending, backups.resolve("rejected-" + stamp + ".hsosave"));
            Files.write(root().resolve("restore-result.txt"), ("Khôi phục chưa thành công. " + error.getMessage()).getBytes(StandardCharsets.UTF_8));
            error.printStackTrace();
        }
    }

    public static synchronized void start() {
        if (started) return;
        started = true;
        Thread listener = new Thread(() -> {
            try (ServerSocket server = new ServerSocket(PORT, 8, InetAddress.getByName("127.0.0.1"))) {
                System.out.println("HSO_TOOLS_READY " + ADDRESS);
                while (!server.isClosed()) {
                    try (Socket socket = server.accept()) {
                        socket.setSoTimeout(15000);
                        handle(socket);
                    } catch (Exception error) {
                        System.err.println("Offline tools request: " + error.getMessage());
                    }
                }
            } catch (IOException error) {
                error.printStackTrace();
            }
        }, "HSO-Data-Tools");
        listener.setDaemon(true);
        listener.start();
        Thread updates = new Thread(OfflineTools::refreshRelease, "HSO-Update-Check");
        updates.setDaemon(true);
        updates.start();
    }

    private static byte[] read(InputStream input, int count) throws IOException {
        if (count < 0 || count > SaveTransfer.LIMIT) throw new IOException("File vượt quá 32 MB.");
        byte[] bytes = new byte[count];
        int total = 0;
        while (total < count) {
            int size = input.read(bytes, total, count - total);
            if (size < 0) throw new IOException("File chưa tải đủ.");
            total += size;
        }
        return bytes;
    }

    private static String line(InputStream input) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        int value;
        while ((value = input.read()) != -1 && value != '\n') {
            if (bytes.size() >= 8192) throw new IOException("Header quá lớn.");
            if (value != '\r') bytes.write(value);
        }
        return new String(bytes.toByteArray(), StandardCharsets.US_ASCII);
    }

    private static void handle(Socket socket) throws Exception {
        InputStream input = socket.getInputStream();
        String[] request = line(input).split(" ");
        if (request.length != 3) return;
        Map<String, String> headers = new HashMap<>();
        String header;
        int size = 0;
        while (!(header = line(input)).isEmpty()) {
            size += header.length();
            if (size > 16384) throw new IOException("Header quá lớn.");
            int colon = header.indexOf(':');
            if (colon <= 0) throw new IOException("Header không hợp lệ.");
            headers.put(header.substring(0, colon).toLowerCase(java.util.Locale.ROOT), header.substring(colon + 1).trim());
        }
        String path = request[1];
        if (!("127.0.0.1:" + PORT).equals(headers.get("host"))) {
            respond(socket, 403, "text/plain", "Địa chỉ không hợp lệ.");
            return;
        }
        try {
            if (request[0].equals("GET") && path.equals("/")) {
                String html = new String(Util.loadfile("data/offline-tools.html"), StandardCharsets.UTF_8);
                Path result = root().resolve("restore-result.txt");
                String message = Files.isRegularFile(result) ? new String(Files.readAllBytes(result), StandardCharsets.UTF_8) : "";
                html = html.replace("__RESTORE_RESULT__", message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"));
                respond(socket, 200, "text/html; charset=utf-8", html.replace("__TOKEN__", TOKEN)
                        .replace("__VERSION__", Integer.toString(VERSION)));
            } else if (request[0].equals("GET") && path.equals("/export?token=" + TOKEN)) {
                String save;
                synchronized (SaveData.class) {
                    SaveData.process();
                    save = SQL.gI().exportSave();
                }
                respond(socket, 200, "application/octet-stream\r\nContent-Disposition: attachment; filename=HSO-"
                        + System.currentTimeMillis() + ".hsosave", save);
            } else if (request[0].equals("POST") && path.equals("/import") && TOKEN.equals(headers.get("x-hso-token"))
                    && ADDRESS.substring(0, ADDRESS.length() - 1).equals(headers.get("origin"))) {
                int count = Integer.parseInt(headers.getOrDefault("content-length", "-1"));
                String text = new String(read(input, count), StandardCharsets.UTF_8);
                SaveTransfer.validate(text);
                Path pending = root().resolve("import-pending.hsosave");
                if (Files.exists(pending)) throw new IOException("Đã có file chờ khôi phục. Hãy đóng và mở lại game.");
                Path partial = root().resolve("import-upload.tmp");
                Files.write(partial, text.getBytes(StandardCharsets.UTF_8));
                Files.move(partial, pending, StandardCopyOption.ATOMIC_MOVE);
                String restart = System.getProperty("os.name", "").startsWith("Windows")
                        ? "Thoát game, chạy TAT_OFFLINE.cmd để tắt server rồi mở lại HSO Offline."
                        : "Thoát hẳn ứng dụng rồi mở lại game.";
                respond(socket, 200, "text/plain; charset=utf-8", "Đã nhận file. " + restart
                        + " Dữ liệu cũ được tự sao lưu trước khi nhập.");
            } else if (request[0].equals("GET") && path.equals("/updates?token=" + TOKEN)) {
                respond(socket, 200, "application/json; charset=utf-8", latest);
            } else if (request[0].equals("POST") && path.equals("/install-pc") && TOKEN.equals(headers.get("x-hso-token"))
                    && ADDRESS.substring(0, ADDRESS.length() - 1).equals(headers.get("origin"))
                    && System.getProperty("os.name", "").startsWith("Windows")) {
                Path game = root().toAbsolutePath().normalize().getParent();
                Path updater = game.resolve("CAP_NHAT_TU_DONG.ps1");
                if (!Files.isRegularFile(updater)) throw new IOException("Thiếu công cụ cập nhật PC.");
                Files.createDirectories(game.resolve("logs"));
                new ProcessBuilder("powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
                        "-File", updater.toString(), "-GameRoot", game.toString())
                        .redirectErrorStream(true)
                        .redirectOutput(ProcessBuilder.Redirect.appendTo(game.resolve("logs/updater-process.log").toFile()))
                        .start();
                respond(socket, 200, "text/plain; charset=utf-8", "Đã mở trình cập nhật PC. Xác nhận trong cửa sổ HSO Offline.");
            } else {
                respond(socket, 403, "text/plain; charset=utf-8", "Yêu cầu không hợp lệ. Mở lại trang Dữ liệu.");
            }
        } catch (Exception error) {
            respond(socket, 400, "text/plain; charset=utf-8", "Chưa thực hiện được. " + error.getMessage());
        }
    }

    private static void respond(Socket socket, int status, String type, String text) throws IOException {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        String header = "HTTP/1.1 " + status + " Response\r\nContent-Type: " + type
                + "\r\nContent-Length: " + bytes.length + "\r\nCache-Control: no-store\r\n"
                + "X-Content-Type-Options: nosniff\r\nConnection: close\r\n\r\n";
        OutputStream output = socket.getOutputStream();
        output.write(header.getBytes(StandardCharsets.US_ASCII));
        output.write(bytes);
        output.flush();
    }

    private static void refreshRelease() {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(RELEASE).openConnection();
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(5000);
            connection.setRequestProperty("User-Agent", "HSO-Offline/" + VERSION);
            try (InputStream input = connection.getInputStream()) {
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                byte[] buffer = new byte[4096];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (bytes.size() + count > 65536) throw new IOException("Release manifest too large");
                    bytes.write(buffer, 0, count);
                }
                Object value = JSONValue.parseWithException(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
                if (!(value instanceof JSONObject manifest) || !(manifest.get("version") instanceof Number))
                    throw new IOException("Invalid release manifest");
                latest = manifest.toJSONString();
            }
        } catch (Exception error) {
            System.out.println("HSO_UPDATE_CHECK " + error.getClass().getSimpleName());
        } finally {
            if (connection != null) connection.disconnect();
        }
    }
}
