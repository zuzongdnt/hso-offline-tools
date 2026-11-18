"""Stage inventory protocol compatibility and fixed cosmetic rules over Offline 31."""
import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    parser.error('Choose an unused output directory.')
shutil.copytree(args.source / 'src', args.out / 'src')
shutil.copy2(args.source / 'pom.xml', args.out / 'pom.xml')
java = args.out / 'src/main/java'


def edit(file, old, new, count=1):
    path = java / file
    source = path.read_text(encoding='utf-8')
    if source.count(old) != count:
        raise ValueError(f'Unexpected source: {file}: {old[:65]}')
    path.write_text(source.replace(old, new), encoding='utf-8')


edit('core/OfflineTools.java', 'VERSION = 31;', 'VERSION = 32;')
edit('core/OfflineLogin.java',
     'java.nio.file.Files.writeString(preference(),chosen,java.nio.charset.StandardCharsets.UTF_8)',
     'java.nio.file.Files.write(preference(),chosen.getBytes(java.nio.charset.StandardCharsets.UTF_8))')
edit('core/OfflineLogin.java',
     'java.nio.file.Files.readString(preference())',
     'new String(java.nio.file.Files.readAllBytes(preference()),java.nio.charset.StandardCharsets.UTF_8)')
edit('client/Item.java', '    public void char_inventory(', '''    private static void writeInventoryCount(Message message, int count) throws IOException {
        // The original MIDlet reads a byte; the patched desktop and mobile clients read a short.
        if (Boolean.getBoolean("hso.client.j2me")) message.writer().writeByte(count);
        else message.writer().writeShort(count);
    }

    public void char_inventory(''')
for value in ('total_item_by_type(3)', 'total_item_by_type(type)', '0', 'total_item_by_type_box(3)', 'total_item_by_type_box(type)'):
    ending = ' // size item quest' if value == '0' else ''
    edit('client/Item.java', f'm.writer().writeShort({value});{ending}', f'writeInventoryCount(m, {value});', 2 if value == '0' else 1)

edit('template/ItemSellCoin.java', '    static boolean cosmetic(int type)', '    public static boolean cosmetic(int type)')
edit('core/GameSrc.java', 'import template.Item3;', 'import template.Item3;\nimport template.ItemSellCoin;')
edit('core/GameSrc.java', '    private static boolean check_item_can_rebuild(byte type) {', '''    private static boolean check_item_can_rebuild(byte type) {
        if (ItemSellCoin.cosmetic(type)) return false;''')
edit('core/GameSrc.java', '            case 15: // fashion\n', '')
edit('core/GameSrc.java', '''            case 21:
            case 22:
            case 23:
            case 24:
            case 25:
            case 26:
            case 11: {''', '            case 11: {')
edit('core/GameSrc.java', '                Item3 it3 = p.item.bag3[id_item];\n                if (it3 != null) {', '''                if (id_item < 0 || id_item >= p.item.bag3.length) return;
                Item3 it3 = p.item.bag3[id_item];
                if (it3 != null && ItemSellCoin.cosmetic(it3.type)) {
                    Service.send_notice_box(p.conn, "Trang phục không thể đục lỗ hoặc khảm ngọc.");
                    return;
                }
                if (it3 != null) {''', 2)

# An APK with the compact marker negotiates up to x2. Java Lite uses its own x1 marker.
edit('core/Manager.java', '            data_part_char_x3[i] =', '''            if (Boolean.getBoolean("hso.assets.max2")) continue;
            data_part_char_x3[i] =''')
edit('io/Session.java', '        System.out.println("CLIENT zoomlv="', '''        if (Boolean.getBoolean("hso.assets.max2") && this.zoomlv > 2) this.zoomlv = 2;
        System.out.println("CLIENT zoomlv="''')
print(args.out.resolve())
