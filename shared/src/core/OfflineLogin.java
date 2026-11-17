package core;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/** Reconnect an automatic local account after importing another device's save. */
public final class OfflineLogin {
    private OfflineLogin() {}
    public record Credentials(String user,String pass) {}
    private static java.nio.file.Path preference(){return java.nio.file.Path.of(System.getProperty("hso.root","."),"restored-account.txt");}
    public static String remember(org.json.simple.JSONObject tables)throws java.io.IOException {
        String chosen=null;int highest=-1;
        for(Object value:(org.json.simple.JSONArray)tables.get("account")){
            var account=(org.json.simple.JSONArray)value;
            Object names=org.json.simple.JSONValue.parse((String)account.get(3));
            if(!(names instanceof org.json.simple.JSONArray characters))continue;
            for(Object playerValue:(org.json.simple.JSONArray)tables.get("player")){
                var player=(org.json.simple.JSONArray)playerValue;
                int level=Integer.parseInt((String)player.get(7));
                if(characters.contains(player.get(1))&&level>highest){highest=level;chosen=(String)account.get(1);}
            }
        }
        if(chosen!=null)java.nio.file.Files.writeString(preference(),chosen,java.nio.charset.StandardCharsets.UTF_8);
        return chosen;
    }
    public static Credentials credentials(Connection connection,String user,String pass)throws SQLException {
        if((user.matches("knightauto_h(?:sod|od)_[0-9]+")&&"hsr_132".equals(pass))
                ||("1".equals(user)&&"1".equals(pass))){
            try{
                if(java.nio.file.Files.isRegularFile(preference())){
                    String selected=java.nio.file.Files.readString(preference()).trim();
                    try(PreparedStatement q=connection.prepareStatement("SELECT user,pass FROM account WHERE user=?")){
                        q.setString(1,selected);
                        try(ResultSet row=q.executeQuery()){if(row.next())return new Credentials(row.getString(1),row.getString(2));}
                    }
                }
            }catch(java.io.IOException error){throw new SQLException("Chưa đọc được tài khoản khôi phục",error);}
        }
        return new Credentials(resolve(connection,user,pass),pass);
    }
    public static String resolve(Connection connection, String user, String pass) throws SQLException {
        if (!user.matches("knightauto_h(?:sod|od)_[0-9]+") || !"hsr_132".equals(pass)) return user;
        try (PreparedStatement query = connection.prepareStatement(
                "SELECT `user` FROM `account` WHERE `pass`=? AND (`user` LIKE 'knightauto_hsod_%'"
                + " OR `user` LIKE 'knightauto_hod_%') ORDER BY CASE WHEN `user`=? THEN 0 ELSE 1 END,`id`")) {
            query.setString(1, pass); query.setString(2, user);
            try (ResultSet rows = query.executeQuery()) {
                while (rows.next()) {
                    String candidate=rows.getString(1);
                    if(candidate.matches("knightauto_h(?:sod|od)_[0-9]+")) return candidate;
                }
                return user;
            }
        }
    }
}
