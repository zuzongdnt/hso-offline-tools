"""Stage the existing server with the iOS storage and application lifecycle."""

import argparse
import shutil
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    parser.error("Choose an unused output directory.")
shutil.copytree(repo / "ios", args.out)
source = args.source / "src/main/java"
target = args.out / "src/main/java"
for path in source.rglob("*.java"):
    if path.relative_to(source).as_posix() == "core/SQL.java":
        continue
    text = path.read_text(encoding="utf-8-sig")
    if path.name == "Util.java":
        text = text.replace("new FileInputStream(url)",
                            'new FileInputStream(new java.io.File(System.getProperty("hso.root"), url))')
    if path.name == "Log.java":
        text = text.replace("new File(path)", 'new File(System.getProperty("hso.root"), path)')
    if path.relative_to(source).as_posix() == "core/Manager.java":
        replacements = [
            (
                'System.err.println("create cache fail!");\n                System.exit(0);',
                'throw new IllegalStateException("Cannot load offline resource cache", e);',
            ),
            (
                'System.err.println("load database err");\n                System.exit(0);\n                return;',
                'throw new IllegalStateException("Invalid offline database records");',
            ),
            (
                '} catch (IOException e) {\n            e.printStackTrace();\n        } catch (SQLException e) {',
                '} catch (IOException e) {\n            throw new IllegalStateException("Cannot load offline world assets", e);\n        } catch (SQLException e) {',
            ),
            (
                'System.err.println("load database err");\n            System.exit(0);',
                'throw new IllegalStateException("Cannot initialize offline world database", e);',
            ),
            (
                'System.err.println("load data map err " + map_id);\n                    System.exit(0);',
                'throw new IOException("Cannot load offline map " + map_id, e);',
            ),
            (
                'System.out.println("Config file not found!");\n            System.exit(0);',
                'throw new IOException("Offline configuration is missing");',
            ),
        ]
        for old, new in replacements:
            if text.count(old) != 1:
                raise ValueError("Expected Manager startup error handler: " + old)
            text = text.replace(old, new)
    if path.relative_to(source).as_posix() == "io/Session.java":
        shutdown = 'if (this.ip.equals("127.0.0.1") && m.cmd == -1) {'
        handshake = '} else if (m.cmd == -40) {'
        begin = text.index(shutdown)
        end = text.index(handshake, begin)
        text = text[:begin] + 'if (m.cmd == -1) {\n                        System.err.println("Ignored embedded server shutdown command");\n                    } else if (m.cmd == -40) {' + text[end + len(handshake):]
        if text.count("while (rs.previous()) {") != 1:
            raise ValueError("Expected the existing reverse character-list cursor.")
        text = text.replace("while (rs.previous()) {", "while (row > 0 && rs.previous()) {")
    if path.name == "SaveData.java":
        old = 'rs = ps.executeQuery("SELECT * FROM `player` ORDER BY `hieuchien` DESC, `id` LIMIT 1");'
        new = 'ps = conn.prepareStatement("SELECT * FROM `player` ORDER BY `hieuchien` DESC, `id` LIMIT 1");\n            rs = ps.executeQuery();'
        if text.count(old) != 1:
            raise ValueError("Expected the existing ranking query in SaveData.java.")
        text = text.replace(old, new)
    if path.relative_to(source).as_posix() == "core/Service.java":
        for job in ("chienbinh", "satthu", "phapsu", "xathu"):
            skill_table = f'Util.loadfile("data/msg/msg_29_{job}")'
            if text.count(skill_table) != 1:
                raise ValueError("Expected one skill table for " + job)
            text = text.replace(skill_table, f"offline.SkillPacket.forClient({skill_table})")
    if path.relative_to(source).as_posix() == "core/ServerManager.java":
        text = text.replace("private boolean running;", "private volatile boolean running;")
        begin = text.index("    public void run() {")
        end = text.index("    private void server_update_right_time()", begin)
        text = text[:begin] + '''    public void run() {
        var address = new java.net.InetSocketAddress("127.0.0.1", Manager.gI().server_port);
        while (this.running) {
            try (ServerSocket listener = new ServerSocket()) {
                listener.setReuseAddress(true);
                listener.bind(address, 50);
                synchronized (this) {
                    if (!this.running) return;
                    this.server = listener;
                }
                System.out.println("IOS_LISTENER_READY " + address);
                while (this.running) {
                    Socket client = listener.accept();
                    if (!this.running) {
                        client.close();
                        return;
                    }
                    new Session(client).init();
                }
            } catch (IOException error) {
                if (!this.running) return;
                System.err.println("Offline listener will reopen: " + error);
                try {
                    Thread.sleep(1000L);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }
    }

''' + text[end:]
        text = text.replace("public void close() throws IOException {", "public synchronized void close() throws IOException {")
        text = text.replace("        server.close();", "        if (server != null) server.close();")
    if path.relative_to(source).as_posix() == "client/MessageHandler.java":
        map_ack = "                conn.p.is_changemap = false;"
        if text.count(map_ack) != 1:
            raise ValueError("Expected one client map acknowledgement handler")
        text = text.replace(map_ack, map_ack + '\n                System.out.println("IOS_CLIENT_MAP_READY map=" + conn.p.map.map_id);')
    if path.relative_to(source).as_posix() == "map/Map.java" and "offline.MapScheduler.schedule(this, delay)" not in text:
        text = text.replace("private final Thread mapthread;", "private java.util.concurrent.ScheduledFuture<?> mapthread;\n    private long nextWorldUpdate;")
        text = text.replace("private boolean running;", "private volatile boolean running;")
        text = text.replace("this.mapthread = new Thread(this);", "this.mapthread = null;")
        begin = text.index("    @Override\n    public void run() {")
        end = text.index("    private synchronized void update_nhanban()", begin)
        body_begin = text.index("\t\t\t\tif (time1 >= nextWorldUpdate)", begin)
        body_end = text.index("\t\t\t\ttime2 = System.currentTimeMillis();", body_begin)
        body = text[body_begin:body_end]
        replacement = '''    @Override
    public void run() {
        if (!this.running) return;
        long time1 = System.currentTimeMillis();
        try {
''' + body + '''        } catch (Exception error) {
            System.err.println("iOS map tick failed: " + map_id + "/" + zone_id);
            error.printStackTrace();
        } finally {
            synchronized (this) {
                if (this.running) {
                    long period = this.ld == null ? 1000L : LoiDai.UPDATE_MILLIS;
                    long delay = period - (System.currentTimeMillis() - time1);
                    this.mapthread = offline.MapScheduler.schedule(this, delay);
                }
            }
        }
    }

'''
        text = text[:begin] + replacement + text[end:]
        old = '''    public void start_map() {
        this.mapthread.start();
    }

    public void stop_map() {
        this.running = false;
        this.mapthread.interrupt();
    }'''
        new = '''    public synchronized void start_map() {
        if (this.running) return;
        this.running = true;
        this.mapthread = offline.MapScheduler.schedule(this, 0);
    }

    public synchronized void stop_map() {
        this.running = false;
        if (this.mapthread != null) this.mapthread.cancel(false);
    }'''
        if text.count(old) != 1:
            raise ValueError("Expected the existing map thread lifecycle.")
        text = text.replace(old, new)
    output = target / path.relative_to(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
print(args.out.resolve())
