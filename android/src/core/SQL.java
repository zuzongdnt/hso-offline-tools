package core;

import java.sql.Connection;
import java.sql.SQLException;
import android.database.sqlite.SQLiteDatabase;
import offline.SQLiteBridge;

public class SQL {
    public static boolean is_connected=false;
    private static SQL instance;
    private final SQLiteDatabase database;
    public final String url="sqlite:local";
    private SQL() {
        database=SQLiteDatabase.openDatabase(System.getProperty("hso.root")+"/hso.sqlite",null,SQLiteDatabase.OPEN_READWRITE);
        database.enableWriteAheadLogging();
        is_connected=true;
    }
    public static synchronized SQL gI(){if(instance==null)instance=new SQL();return instance;}
    public Connection getConnection() throws SQLException{return SQLiteBridge.connection(database);}
    public void close(){if(database.isOpen())database.close();is_connected=false;}
}
