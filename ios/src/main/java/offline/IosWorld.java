package offline;

import core.SQL;
import core.SaveData;
import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public final class IosWorld {
    private static boolean started;

    public static synchronized void start(Path root, Path bundle) throws Exception {
        if (started) return;
        Files.createDirectories(root);
        Path marker = root.resolve(".ready-ios-v1");
        if (!Files.exists(marker)) {
            // An incomplete first extraction can be retried. The database is copied only
            // if absent, so a retry cannot replace an existing character save.
            extract(bundle.resolve("offline-world.zip"), root, true);
            extract(bundle.resolve("offline-cosmetics.zip"), root, false);
            Files.createFile(marker);
        }
        Path cosmetics = root.resolve(".cosmetics-ios-v26");
        if (!Files.exists(cosmetics)) {
            extract(bundle.resolve("offline-cosmetics.zip"), root, false);
            Files.createFile(cosmetics);
        }
        System.setProperty("hso.root", root.toAbsolutePath().toString());
        SQL.gI();
        AtomicReference<Throwable> failure = new AtomicReference<>();
        new Thread(() -> {
            try {
                core.Start.main(new String[0]);
            } catch (Throwable error) {
                failure.set(error);
            }
        }, "HSO-iOS-World").start();
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(120);
        while (System.nanoTime() < deadline) {
            if (failure.get() != null) throw new IOException("Cannot start offline world", failure.get());
            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress("127.0.0.1", 19139), 500);
                started = true;
                int mapCount = map.Map.entrys.stream().mapToInt(zones -> zones.length).sum();
                System.out.println("IOS_MAP_SCHEDULER maps=" + mapCount
                        + " workers=" + MapScheduler.workerCount() + " javaThreads=" + Thread.activeCount());
                Executors.newSingleThreadScheduledExecutor(task -> {
                    Thread thread = new Thread(task, "HSO-iOS-Autosave");
                    thread.setDaemon(true);
                    return thread;
                }).scheduleWithFixedDelay(IosWorld::saveQuietly, 15, 15, TimeUnit.SECONDS);
                return;
            } catch (IOException error) {
                Thread.sleep(250);
            }
        }
        throw new IOException("Timed out starting offline world");
    }

    private static void extract(Path archive, Path root, boolean preserveDatabase) throws IOException {
        try (InputStream input = Files.newInputStream(archive);
                ZipInputStream zip = new ZipInputStream(input)) {
            ZipEntry entry;
            Path canonicalRoot = root.toRealPath();
            while ((entry = zip.getNextEntry()) != null) {
                Path target = canonicalRoot.resolve(entry.getName()).normalize();
                if (!target.startsWith(canonicalRoot)) throw new IOException("Invalid world archive path");
                if (entry.isDirectory()) {
                    Files.createDirectories(target);
                } else {
                    Files.createDirectories(target.getParent());
                    if (preserveDatabase && entry.getName().equals("hso.sqlite")) {
                        if (Files.exists(target)) continue;
                        Path seed = target.resolveSibling("hso.sqlite.seed");
                        Files.copy(zip, seed, StandardCopyOption.REPLACE_EXISTING);
                        Files.move(seed, target, StandardCopyOption.ATOMIC_MOVE);
                    } else {
                        Files.copy(zip, target, StandardCopyOption.REPLACE_EXISTING);
                    }
                }
            }
        }
    }

    public static void save() throws Exception {
        if (SQL.is_connected) {
            SaveData.process();
            SQL.gI().checkpoint();
        }
    }

    private static void saveQuietly() {
        try {
            save();
        } catch (Exception error) {
            error.printStackTrace();
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("Expected save directory and resource directory");
        start(Path.of(args[0]), Path.of(args[1]));
        System.out.println("IOS_WORLD_READY");
    }
}
