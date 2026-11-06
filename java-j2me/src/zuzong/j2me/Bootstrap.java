package zuzong.j2me;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import dalvik.system.DexClassLoader;
import java.io.*;

/** Small Java 8 entry point; the Java 17 server is kept out of the MIDlet converter. */
public final class Bootstrap {
    private static boolean started;
    private static volatile boolean ready;
    private static Throwable failure;
    private static Class<?> engine;
    private static AlertDialog progress;
    private static final Handler ui = new Handler(Looper.getMainLooper());

    public static synchronized void start() {
        if (started) return;
        started = true;
        new Thread(new Runnable() {
            public void run() {
                Activity activity = null;
                try {
                    if (Build.VERSION.SDK_INT < 33) throw new IOException("Cần Android 13 trở lên.");
                    Class<?> holder = Class.forName("javax.microedition.util.ContextHolder");
                    activity = (Activity) holder.getMethod("getActivity").invoke(null);
                    final Activity screen = activity;
                    ui.post(new Runnable() { public void run() {
                        if (!screen.isFinishing()) progress = new AlertDialog.Builder(screen)
                            .setTitle("HSO Java Offline")
                            .setMessage("Đang mở thế giới offline. Lần đầu có thể mất vài phút...")
                            .setCancelable(false).show();
                    }});
                    Context context = activity.getApplicationContext();
                    File code = new File(context.getCodeCacheDir(), "hso-java-offline-v1");
                    if (!code.isDirectory() && !code.mkdirs()) throw new IOException("Không tạo được bộ nhớ game.");
                    // A content-addressed file avoids replacing a loaded or read-only DEX on updates.
                    String version = readText("/offline/engine-id.txt").trim();
                    if (!version.matches("[a-f0-9]{64}")) throw new IOException("Sai mã bộ xử lý offline.");
                    File dex = new File(code, "engine-" + version + ".dex");
                    if (!dex.isFile()) {
                        File temp = new File(code, "engine-" + version + ".tmp");
                        try (InputStream in = resource("/offline/engine.bin");
                             FileOutputStream out = new FileOutputStream(temp)) {
                            copy(in, out);
                            out.getFD().sync();
                        }
                        if (!temp.setReadOnly() || !temp.renameTo(dex)) throw new IOException("Không cài được bộ xử lý offline.");
                    }
                    DexClassLoader loader = new DexClassLoader(dex.getAbsolutePath(), code.getAbsolutePath(), null, Bootstrap.class.getClassLoader());
                    engine = loader.loadClass("offline.J2meEngine");
                    engine.getMethod("start", Context.class, File.class, InputStream.class).invoke(null,
                        context, new File(context.getFilesDir(), "hso-java-offline"), new WorldStream());
                    synchronized (Bootstrap.class) { ready = true; Bootstrap.class.notifyAll(); }
                    ui.post(new Runnable() { public void run() { if (progress != null) progress.dismiss(); }});
                } catch (Throwable error) {
                    while (error.getCause() != null) error = error.getCause();
                    error.printStackTrace();
                    synchronized (Bootstrap.class) { failure = error; Bootstrap.class.notifyAll(); }
                    final String message = error.toString();
                    final Activity screen = activity;
                    if (screen != null) ui.post(new Runnable() { public void run() {
                        if (progress != null) progress.dismiss();
                        if (!screen.isFinishing()) new AlertDialog.Builder(screen).setTitle("Chưa mở được game")
                            .setMessage(message).setPositiveButton("Đóng", null).show();
                    }});
                }
            }
        }, "HSO-Java-Offline-Boot").start();
    }

    public static synchronized void awaitReady() throws IOException {
        start();
        long end = System.currentTimeMillis() + 240000L;
        while (!ready && failure == null && System.currentTimeMillis() < end) {
            try { Bootstrap.class.wait(500L); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new IOException("Đã ngắt mở game."); }
        }
        if (!ready) throw new IOException(failure == null ? "Mở thế giới quá lâu. Hãy thử lại." : failure.toString());
    }

    public static void save() {
        try { if (ready && engine != null) engine.getMethod("save").invoke(null); }
        catch (Throwable e) { e.printStackTrace(); }
    }

    private static InputStream resource(String name) throws IOException {
        InputStream in = Bootstrap.class.getResourceAsStream(name);
        if (in == null) throw new IOException("Thiếu dữ liệu: " + name);
        return in;
    }
    private static String readText(String name) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (InputStream in = resource(name)) { copy(in, out); }
        return new String(out.toByteArray(), "UTF-8");
    }
    private static void copy(InputStream in, OutputStream out) throws IOException {
        byte[] buf = new byte[65536]; int n;
        while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
    }

    /** J2ME Loader buffers each resource: keep each piece small instead of allocating the whole world. */
    private static final class WorldStream extends InputStream {
        private int index;
        private InputStream current;
        private final int count;
        WorldStream() throws IOException { count = Integer.parseInt(readText("/offline/world-count.txt").trim()); }
        public int read() throws IOException { byte[] one = new byte[1]; return read(one, 0, 1) == -1 ? -1 : one[0] & 255; }
        public int read(byte[] b, int off, int len) throws IOException {
            if (len == 0) return 0;
            while (true) {
                if (current == null) {
                    if (index == count) return -1;
                    current = resource("/offline/world-" + index++ + ".bin");
                }
                int n = current.read(b, off, len);
                if (n != -1) return n;
                current.close(); current = null;
            }
        }
        public void close() throws IOException { if (current != null) current.close(); current = null; index = count; }
    }
}
