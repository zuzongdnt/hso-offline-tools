package offline;

import android.database.Cursor;
import android.database.MatrixCursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteProgram;
import android.database.sqlite.SQLiteStatement;
import java.lang.reflect.*;
import java.sql.*;
import java.util.*;

/** JDBC-shaped access to the app's SQLite database for the existing server. */
public final class SQLiteBridge {
    private static Object zero(Class<?> c){
        if(c==boolean.class)return false;if(c==int.class)return 0;if(c==long.class)return 0L;
        if(c==short.class)return (short)0;if(c==byte.class)return (byte)0;
        if(c==float.class)return 0f;if(c==double.class)return 0d;return null;
    }
    @SuppressWarnings("unchecked")
    private static <T> T proxy(Class<T> type,InvocationHandler h){
        return (T)Proxy.newProxyInstance(SQLiteBridge.class.getClassLoader(),new Class[]{type},h);
    }
    private static String sql(String s){
        return s.replaceAll("(?i)INSERT\\s+IGNORE\\s+INTO","INSERT OR IGNORE INTO")
            .replaceAll("(?i)TRUNCATE\\s+TABLE","DELETE FROM")
            .replaceAll("(?i)NOW\\(\\)","datetime('now')")
            .replaceAll("(?i)LAST_INSERT_ID\\(\\)","last_insert_rowid()")
            .replaceAll("(?i)ON DUPLICATE KEY UPDATE","ON CONFLICT DO UPDATE SET")
            .replaceAll("(?i)VALUES\\((`?[a-zA-Z0-9_]+`?)\\)","excluded.$1");
    }
    public static Connection connection(SQLiteDatabase db){return proxy(Connection.class,new Conn(db));}
    private static final class Conn implements InvocationHandler {
        final SQLiteDatabase db;boolean automatic=true,closed;
        Conn(SQLiteDatabase db){this.db=db;}
        public Object invoke(Object p,Method m,Object[] a)throws Throwable{
            try{
                switch(m.getName()){
                    case "createStatement":return proxy(Statement.class,new Stmt(this,null));
                    case "prepareStatement":return proxy(PreparedStatement.class,new Stmt(this,(String)a[0]));
                    case "setAutoCommit":
                        boolean auto=(Boolean)a[0];
                        if(!auto && automatic && !db.inTransaction())db.beginTransaction();
                        if(auto && !automatic && db.inTransaction()){db.setTransactionSuccessful();db.endTransaction();}
                        automatic=auto;return null;
                    case "getAutoCommit":return automatic;
                    case "commit":if(db.inTransaction()){db.setTransactionSuccessful();db.endTransaction();}return null;
                    case "rollback":if(db.inTransaction())db.endTransaction();return null;
                    case "close":if(!automatic && db.inTransaction())db.endTransaction();closed=true;return null;
                    case "isClosed":return closed;
                    case "isValid":return !closed && db.isOpen();
                    case "toString":return "OfflineSQLiteConnection";
                    default:return zero(m.getReturnType());
                }
            }catch(android.database.SQLException e){throw new SQLException(e.getMessage(),e);}
        }
    }
    private static final class Stmt implements InvocationHandler {
        final Conn conn;final String prepared;
        final TreeMap<Integer,Object> values=new TreeMap<>();
        final List<TreeMap<Integer,Object>> batches=new ArrayList<>();
        ResultSet last;long generated;int changed;
        Stmt(Conn c,String s){conn=c;prepared=s;}
        private void bind(SQLiteProgram st,TreeMap<Integer,Object> args){
            for(Map.Entry<Integer,Object> entry:args.entrySet()){
                Object v=entry.getValue();int i=entry.getKey();
                if(v==null)st.bindNull(i);
                else if(v instanceof byte[])st.bindBlob(i,(byte[])v);
                else if(v instanceof Float || v instanceof Double)st.bindDouble(i,((Number)v).doubleValue());
                else if(v instanceof Number)st.bindLong(i,((Number)v).longValue());
                else if(v instanceof Boolean)st.bindLong(i,(Boolean)v?1:0);
                else st.bindString(i,String.valueOf(v));
            }
        }
        private ResultSet query(String query){
            int count=values.isEmpty()?0:values.lastKey();String[] args=new String[count];
            for(int i=0;i<count;i++){Object v=values.get(i+1);args[i]=v==null?null:String.valueOf(v);}
            return result(conn.db.rawQuery(sql(query),args));
        }
        private int update(String text,TreeMap<Integer,Object> params){
            String query=sql(text);
            try(SQLiteStatement st=conn.db.compileStatement(query)){
                bind(st,params);
                if(query.trim().toUpperCase(Locale.ROOT).startsWith("INSERT")){
                    generated=st.executeInsert();return generated<0?0:1;
                }
                return st.executeUpdateDelete();
            }
        }
        public Object invoke(Object p,Method m,Object[] a)throws Throwable{
            try{
                String name=m.getName();
                if(name.startsWith("set") && a!=null && a.length>=2 && a[0] instanceof Integer){
                    values.put((Integer)a[0],name.equals("setNull")?null:a[1]);return null;
                }
                switch(name){
                    case "executeQuery":last=query(prepared!=null?prepared:(String)a[0]);return last;
                    case "executeUpdate":changed=update(prepared!=null?prepared:(String)a[0],values);return changed;
                    case "executeLargeUpdate":changed=update(prepared!=null?prepared:(String)a[0],values);return (long)changed;
                    case "execute":
                        String text=prepared!=null?prepared:(String)a[0];
                        if(text.trim().toUpperCase(Locale.ROOT).startsWith("SELECT")){last=query(text);return true;}
                        changed=update(text,values);return false;
                    case "getResultSet":return last;
                    case "getUpdateCount":return changed;
                    case "clearParameters":values.clear();return null;
                    case "addBatch":batches.add(new TreeMap<>(values));return null;
                    case "clearBatch":batches.clear();return null;
                    case "executeBatch":
                        int[] counts=new int[batches.size()];
                        for(int i=0;i<counts.length;i++)counts[i]=update(prepared,batches.get(i));
                        batches.clear();return counts;
                    case "getGeneratedKeys":
                        MatrixCursor keys=new MatrixCursor(new String[]{"GENERATED_KEY"});keys.addRow(new Object[]{generated});return result(keys);
                    case "close":if(last!=null)last.close();return null;
                    case "toString":return "OfflineSQLiteStatement";
                    default:return zero(m.getReturnType());
                }
            }catch(android.database.SQLException e){throw new SQLException(e.getMessage(),e);}
        }
    }
    public static ResultSet result(Cursor cursor){
        return proxy(ResultSet.class,new InvocationHandler(){
            boolean wasNull;
            private int column(Object key)throws SQLException{
                int index=key instanceof Number?((Number)key).intValue()-1:cursor.getColumnIndex(String.valueOf(key));
                if(index<0 || index>=cursor.getColumnCount())throw new SQLException("Unknown column: "+key);
                wasNull=cursor.isNull(index);return index;
            }
            public Object invoke(Object p,Method m,Object[] a)throws Throwable{
                switch(m.getName()){
                    case "next":return cursor.moveToNext();
                    case "previous":return cursor.moveToPrevious();
                    case "first":return cursor.moveToFirst();
                    case "last":return cursor.moveToLast();
                    case "beforeFirst":cursor.moveToPosition(-1);return null;
                    case "afterLast":cursor.moveToPosition(cursor.getCount());return null;
                    case "absolute":return cursor.moveToPosition(((Integer)a[0])-1);
                    case "getRow":return cursor.isBeforeFirst()||cursor.isAfterLast()?0:cursor.getPosition()+1;
                    case "findColumn":return cursor.getColumnIndexOrThrow((String)a[0])+1;
                    case "getString":int s=column(a[0]);return wasNull?null:cursor.getString(s);
                    case "getByte":return (byte)cursor.getInt(column(a[0]));
                    case "getShort":return (short)cursor.getInt(column(a[0]));
                    case "getInt":return cursor.getInt(column(a[0]));
                    case "getLong":return cursor.getLong(column(a[0]));
                    case "getFloat":return cursor.getFloat(column(a[0]));
                    case "getDouble":return cursor.getDouble(column(a[0]));
                    case "getBoolean":return cursor.getInt(column(a[0]))!=0;
                    case "getBytes":return cursor.getBlob(column(a[0]));
                    case "getObject":int v=column(a[0]);return wasNull?null:cursor.getString(v);
                    case "wasNull":return wasNull;
                    case "isClosed":return cursor.isClosed();
                    case "isBeforeFirst":return cursor.isBeforeFirst();
                    case "isAfterLast":return cursor.isAfterLast();
                    case "close":cursor.close();return null;
                    case "toString":return "OfflineSQLiteResult";
                    default:return zero(m.getReturnType());
                }
            }
        });
    }
}
