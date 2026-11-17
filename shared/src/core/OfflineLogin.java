package core;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/** Reconnect an automatic local account after importing another device's save. */
public final class OfflineLogin {
    private OfflineLogin() {}
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
