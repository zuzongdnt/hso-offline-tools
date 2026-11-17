"""Stage the PC updater, portable-login and arena corrections without touching saves."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from map_scheduler import patch as bound_maps

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,default=root/'build/server-offline28-extra')
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
if a.out.exists():p.error('Choose a new output directory.')
shutil.copytree(a.source/'src',a.out/'src')
shutil.copy2(a.source/'pom.xml',a.out/'pom.xml')
java=a.out/'src/main/java'
for name in ['OfflineTools','SaveTransfer','OfflineLogin','ArenaShop','ArenaRoster','ArenaBotEquipment']:
    text=(root/f'shared/src/core/{name}.java').read_text(encoding='utf-8')
    (java/f'core/{name}.java').write_text(text.replace('VERSION = 26;','VERSION = 29;'),encoding='utf-8')

def edit(name,old,new):
    path=java/name;text=path.read_text(encoding='utf-8')
    if text.count(old)!=1:raise ValueError(f'Unexpected source: {name}: {old[:70]}')
    path.write_text(text.replace(old,new),encoding='utf-8')

edit('event_daily/LoiDai.java','''        Session session = new Session(null) {''','''        int lower = player.level < 55 ? 50 : 55 + (player.level - 55) / 10 * 10;
        int upper = Math.min(139, player.level < 55 ? 64 : lower + 9);
        return createOpponent(player,id,lower + Util.random(upper-lower+1));
    }

    public static Player createOpponent(Player player, int id, int level) throws IOException {
        if (level < 50 || level > 139) throw new IllegalArgumentException("Arena level");
        Session session = new Session(null) {''')
edit('event_daily/LoiDai.java','''        int lower = player.level < 55 ? 50 : 55 + (player.level - 55) / 10 * 10;
        int upper = Math.min(139, player.level < 55 ? 64 : lower + 9);
        bot.level = (short) (lower + Util.random(upper - lower + 1));''','''        bot.level = (short)level;''')
edit('event_daily/LoiDai.java','''        bot.hp = bot.body.get_max_hp();''','''        core.ArenaBotEquipment.configure(bot);
        bot.hp = bot.body.get_max_hp();''')
edit('core/OfflineMarket.java','item.clazz = (byte) clazz;','item.clazz = 4;')
edit('template/OfflineSkins.java','''    public static void refreshSavedItem(Item3 item) {''','''    public static void refreshSavedItem(Item3 item) {
        if (item.type == 16) item.clazz = 4;''')
edit('core/Service.java','''        if (idbuy < 0 || quanity < 1) return;''','''        if (idbuy < 0 || quanity < 1) return;
        if (p.conn.shopType == core.ArenaShop.SHOP_TYPE) {
            if (type == 3) core.ArenaShop.buy(p,idbuy,quanity);
            return;
        }''')
edit('core/Service.java','''                            if (p.conn.shopType == 37 && ItemSellCoin.REMOVED_GOLD_STOCK.contains((int)idbuy)) return;''','''                            if (core.ArenaShop.contains(idbuy) || (p.conn.shopType == 37 && ItemSellCoin.REMOVED_GOLD_STOCK.contains((int)idbuy))) return;''')
edit('io/Session.java','''            String query = "SELECT * FROM `account` WHERE `user` = '" + user_ + "' AND `pass` = '" + pass_ + "' LIMIT 1;";''','''            try (Connection lookup = SQL.gI().getConnection()) {
                user_ = core.OfflineLogin.resolve(lookup,user_,pass_);
            } catch (SQLException error) {
                noticelogin("Chưa đọc được tài khoản. Hãy mở lại game.");return;
            }
            String query = "SELECT * FROM `account` WHERE `user` = '" + user_ + "' AND `pass` = '" + pass_ + "' LIMIT 1;";''')
subprocess.run([sys.executable,str(root/'scripts/apply_offline29_gems.py'),'--source',str(a.out)],check=True)
subprocess.run([sys.executable,str(root/'scripts/apply_offline29_disciple.py'),'--source',str(a.out)],check=True)
map_path=java/'map/Map.java'
map_path.write_text(bound_maps(map_path.read_text(encoding='utf-8')),encoding='utf-8')
(java/'offline').mkdir(exist_ok=True)
shutil.copy2(root/'ios/src/main/java/offline/MapScheduler.java',java/'offline/MapScheduler.java')
print(a.out.resolve())
