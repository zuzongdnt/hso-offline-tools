package offline;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import java.io.*;
import java.net.Socket;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.zip.*;

/** Uses the same patched server and SQLite bridge as the Android offline APK. */
public final class J2meEngine {
    public static synchronized void start(Context context, File root, InputStream world) throws Exception {
        File complete = new File(root, ".ready-v1");
        if (!complete.isFile()) {
            if (!root.isDirectory() && !root.mkdirs()) throw new IOException("Không tạo được thư mục lưu.");
            try (ZipInputStream zip = new ZipInputStream(world)) {
                ZipEntry entry; byte[] buffer = new byte[65536];
                while ((entry = zip.getNextEntry()) != null) {
                    File target = new File(root, entry.getName());
                    if (!target.getCanonicalPath().startsWith(root.getCanonicalPath() + File.separator))
                        throw new IOException("Invalid world path");
                    if (entry.isDirectory()) { target.mkdirs(); continue; }
                    target.getParentFile().mkdirs();
                    try (FileOutputStream out = new FileOutputStream(target)) {
                        int n; while ((n = zip.read(buffer)) != -1) out.write(buffer, 0, n);
                    }
                }
            }
            try (SQLiteDatabase db = SQLiteDatabase.openDatabase(new File(root, "hso.sqlite").toString(), null, SQLiteDatabase.OPEN_READWRITE)) {
                // This is a new, empty offline world, separate from APK, PC and online saves.
                db.execSQL("INSERT OR IGNORE INTO account (id,user,pass,char,status,`lock`,coin,phone,ip,tiennap,pass2,tongnap,checkmocnap) VALUES (1,'javaoff','offline','[]',1,0,0,'','127.0.0.1',0,'',0,'[]')");
            }
            if (!complete.createNewFile()) throw new IOException("Không ghi được trạng thái cài game.");
        } else world.close();
        System.setProperty("hso.root", root.getAbsolutePath());
        AtomicReference<Throwable> failure = new AtomicReference<>();
        new Thread(() -> { try { core.Start.main(new String[0]); }
            catch (Throwable e) { failure.set(e); android.util.Log.e("HSOJavaOffline", "Startup", e); }
        }, "HSO-Java-World").start();
        boolean ready = false;
        for (int i = 0; i < 180; i++) {
            if (failure.get() != null) throw new IOException("Không mở được thế giới", failure.get());
            try (Socket s = new Socket("127.0.0.1", 19149)) { ready = true; break; }
            catch (IOException e) { Thread.sleep(500); }
        }
        if (!ready) throw new IOException("Không khởi động được thế giới offline.");
        Executors.newSingleThreadScheduledExecutor().scheduleWithFixedDelay(J2meEngine::save, 15, 15, TimeUnit.SECONDS);
        android.util.Log.i("HSOJavaOffline", "WORLD_READY " + root);
    }

    public static void save() {
        try { if (core.SQL.is_connected) core.SaveData.process(); }
        catch (Throwable e) { android.util.Log.e("HSOJavaOffline", "Save", e); }
    }
}
