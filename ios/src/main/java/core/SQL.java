package core;

import io.roastedroot.sqlite4j.JDBC;
import io.roastedroot.sqlite4j.SQLiteConnection;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import javax.sql.rowset.CachedRowSet;
import javax.sql.rowset.RowSetProvider;

/** All SQLite4j access runs on one thread because its SQLite build is single-threaded. */
public final class SQL {
    public static volatile boolean is_connected;
    private static SQL instance;
    private final ExecutorService worker = Executors.newSingleThreadExecutor(task -> {
        Thread thread = new Thread(task, "HSO-SQLite");
        thread.setDaemon(true);
        return thread;
    });
    private final Path file = Path.of(System.getProperty("hso.root"), "hso.sqlite");
    private final SQLiteConnection database;
    private boolean dirty;
    public final String url = "sqlite:local";

    private SQL() throws SQLException {
        database = call(() -> {
            if (!Files.isRegularFile(file)) throw new IOException("Missing offline database");
            SQLiteConnection connection = (SQLiteConnection) new JDBC().connect("jdbc:sqlite::memory:", new Properties());
            try {
                connection.deserialize("main", Files.readAllBytes(file));
                return connection;
            } catch (Exception error) {
                connection.close();
                throw error;
            }
        });
        is_connected = true;
    }

    public static synchronized SQL gI() {
        if (instance == null) {
            try {
                instance = new SQL();
            } catch (SQLException error) {
                throw new IllegalStateException("Cannot open offline SQLite", error);
            }
        }
        return instance;
    }

    private <T> T call(Callable<T> action) throws SQLException {
        try {
            return worker.submit(action).get();
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new SQLException("Interrupted SQLite operation", error);
        } catch (ExecutionException error) {
            Throwable cause = error.getCause();
            if (cause instanceof SQLException sql) throw sql;
            throw new SQLException("Offline SQLite operation failed", cause);
        }
    }

    private static Object invoke(Method method, Object target, Object[] args) throws Exception {
        try {
            return method.invoke(target, args);
        } catch (InvocationTargetException error) {
            if (error.getCause() instanceof Exception cause) throw cause;
            throw error;
        }
    }

    private static String translate(String text) {
        return text.replaceAll("(?i)INSERT\\s+IGNORE\\s+INTO", "INSERT OR IGNORE INTO")
                .replaceAll("(?i)TRUNCATE\\s+TABLE", "DELETE FROM")
                .replaceAll("(?i)NOW\\(\\)", "datetime('now')")
                .replaceAll("(?i)LAST_INSERT_ID\\(\\)", "last_insert_rowid()");
    }

    @SuppressWarnings("unchecked")
    public Connection getConnection() throws SQLException {
        if (!is_connected) throw new SQLException("Offline database is closed");
        List<Statement> statements = new ArrayList<>();
        boolean[] closed = {false};
        return (Connection) Proxy.newProxyInstance(SQL.class.getClassLoader(),
                new Class<?>[]{Connection.class}, (proxy, method, args) -> call(() -> {
                    String name = method.getName();
                    if (name.equals("isClosed")) return closed[0];
                    if (name.equals("close")) {
                        for (Statement statement : statements) statement.close();
                        statements.clear();
                        closed[0] = true;
                        return null;
                    }
                    if (closed[0]) throw new SQLException("Connection is closed");
                    if (name.equals("createStatement")) {
                        Statement statement = database.createStatement();
                        statements.add(statement);
                        return wrapStatement(statement, Statement.class);
                    }
                    if (name.equals("prepareStatement")) {
                        PreparedStatement statement = database.prepareStatement(translate((String) args[0]));
                        statements.add(statement);
                        return wrapStatement(statement, PreparedStatement.class);
                    }
                    // Existing game callers use autocommit. A logical connection never owns
                    // the shared physical connection's transaction.
                    if (name.equals("setAutoCommit")) {
                        if (!(Boolean) args[0]) throw new SQLFeatureNotSupportedException("Offline transactions");
                        return null;
                    }
                    if (name.equals("getAutoCommit")) return true;
                    if (name.equals("commit") || name.equals("rollback")) {
                        throw new SQLFeatureNotSupportedException("Offline transactions");
                    }
                    return invoke(method, database, args);
                }));
    }

    private Object wrapStatement(Statement statement, Class<?> type) {
        return Proxy.newProxyInstance(SQL.class.getClassLoader(), new Class<?>[]{type},
                (proxy, method, args) -> call(() -> {
                    String name = method.getName();
                    if (name.equals("setNString")) {
                        ((PreparedStatement) statement).setString((Integer) args[0], (String) args[1]);
                        return null;
                    }
                    Object[] translated = args;
                    if (name.startsWith("execute") && args != null && args.length > 0 && args[0] instanceof String) {
                        translated = args.clone();
                        translated[0] = translate((String) args[0]);
                    }
                    Object result = invoke(method, statement, translated);
                    if (name.startsWith("execute")) dirty = true;
                    if (result instanceof ResultSet rows) {
                        // Character selection walks backwards through results. Materialize
                        // each query before releasing the single SQLite thread.
                        try (rows) {
                            CachedRowSet cached = RowSetProvider.newFactory().createCachedRowSet();
                            cached.populate(rows);
                            return cached;
                        }
                    }
                    return result;
                }));
    }

    public String exportSave() throws Exception {
        return call(() -> {
            database.setAutoCommit(false);
            try {
                String text = core.SaveTransfer.capture(database);
                database.commit();
                return text;
            } catch (Exception error) {
                database.rollback();
                throw error;
            } finally {
                database.setAutoCommit(true);
            }
        });
    }

    public void importSave(String text) throws Exception {
        core.SaveTransfer.validate(text);
        call(() -> {
            database.setAutoCommit(false);
            try {
                core.SaveTransfer.replace(database, text);
                database.commit();
                dirty = true;
            } catch (Exception error) {
                database.rollback();
                throw error;
            } finally {
                database.setAutoCommit(true);
            }
            return null;
        });
        checkpoint();
    }

    public void checkpoint() throws SQLException {
        call(() -> {
            if (!dirty) return null;
            Path pending = file.resolveSibling("hso.sqlite.pending");
            Files.write(pending, database.serialize("main"));
            try (FileChannel channel = FileChannel.open(pending, StandardOpenOption.WRITE)) {
                channel.force(true);
            }
            Files.move(pending, file, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            dirty = false;
            return null;
        });
    }

    public void close() {
        try {
            checkpoint();
            call(() -> {
                database.close();
                return null;
            });
        } catch (SQLException error) {
            throw new IllegalStateException("Cannot close offline database", error);
        } finally {
            is_connected = false;
            worker.shutdown();
        }
    }
}
