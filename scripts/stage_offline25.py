"""Remove online account features from the staged offline server."""
import re

from stage_offline23 import SERVER, edit, main as stage_base


def remove_cases(source, ids):
    for case_id in ids:
        pattern = rf'(?ms)^            case {case_id}: \{{.*?(?=^            (?:case |default:))'
        source, count = re.subn(pattern, '', source)
        if count != 1:
            raise ValueError(f'Expected one case {case_id}, found {count}')
    return source


def main():
    stage_base()
    session = SERVER / 'io/Session.java'
    edit(session, 'noticelogin("Sai cmn pass rồi");',
         'noticelogin("Tên đăng nhập hoặc mật khẩu không đúng. Nếu vừa khôi phục, hãy kiểm tra tài khoản trong bản sao lưu.");')
    edit(session, '                this.status = rs.getByte("status");\n                System.out.println(this.status);',
         '                // Offline accounts do not require activation.')
    edit(session, '    public byte status = 1;', '    public byte status = 0;')
    battlefield = SERVER / 'event_daily/ChienTruong.java'
    source = battlefield.read_text(encoding='utf-8')
    battlefield.write_text(source.replace('''            if (p.conn.status != 0) {
                return;
            }
''', ''), encoding='utf-8')
    edit(session, '''                jsar.clear();
                String moc_nap_ = rs.getString("checkmocnap");
                if (moc_nap_ != null && !moc_nap_.isEmpty()) {
                    jsar = (JSONArray) JSONValue.parse(moc_nap_);
                    for (int i = 0; i < jsar.size(); i++) {
                        moc_nap.add(jsar.get(i).toString());
                    }
                }
''', '                // Ignore legacy top-up history on login.\n')

    gate = '''                if (conn.status != 0) {
                    Service.send_notice_box(conn, "Tài khoản chưa được kích hoạt, hãy kích hoạt");
                    return;
                }
'''
    for name in ('client/MessageHandler.java', 'client/TextFromClient.java', 'core/MenuController.java'):
        path = SERVER / name
        source = path.read_text(encoding='utf-8')
        source = source.replace(gate, '')
        if name == 'client/TextFromClient.java' and 'int coin_exchange' in source:
            source = remove_cases(source, (5, 14))
        path.write_text(source, encoding='utf-8')

    menu = SERVER / 'core/MenuController.java'
    source = menu.read_text(encoding='utf-8')
    source = source.replace('"Đổi coin sang ngọc", "Đổi coin sang vàng",\n                        ', '')
    source = source.replace(', "Nhận Quà Mốc Nạp" ', '')
    source = source.replace('ChienTruong.gI().getStatus() == 1 && conn.status == 0',
                            'ChienTruong.gI().getStatus() == 1')
    source = source.replace('''                if (conn.status == 0) {
                    send_menu_select(conn, 555, new String[]{"Nhận Nhiệm Vụ", "Trả Nhiệm Vụ", "Hủy Nhiệm Vụ", "Thông Tin", "Thêm lượt"});
                } else {
                    Service.send_notice_box(conn, "TK chua kich hoat");
                }''', '''                send_menu_select(conn, 555, new String[]{"Nhận Nhiệm Vụ", "Trả Nhiệm Vụ", "Hủy Nhiệm Vụ", "Thông Tin", "Thêm lượt"});''')
    source = source.replace('''            case 5: {
                send_menu_select(conn, 129, new String[]{"Nhận Mốc", "Hướng Dẫn", "Tổng Nạp"});
                break;
            }
''', '')
    source = source.replace(' +\n                "\\nTrạng Thái Tài Khoản: " + (conn.status == 0 ? "Đã Kích Hoạt" : "Chưa Kích Hoạt")', '')
    if 'Đổi coin sang ngọc' in source:
        source = remove_cases(source, (129, 557))
        start = source.index('    private static void Menu_Zulu(')
        end = source.index('    private static void Menu_ChangeZone(', start)
        zulu = remove_cases(source[start:end], (2, 3))
        zulu = re.sub(r'(?m)^            case ([4-9]):', lambda m: f'            case {int(m[1]) - 2}:', zulu)
        source = source[:start] + zulu + source[end:]
        start = source.index('    private static void Menu_MocNap(')
        end = source.index(' private static void Menu_Thongtincanhan(', start)
        source = source[:start] + source[end:]
    if any(item in source for item in ('Menu_MocNap(', 'QuaTang.get_qua(', 'Nhận Mốc', 'Đổi coin sang',
                                       'Nhận Quà Mốc Nạp', 'conn.status')):
        raise ValueError('A disabled function is still reachable from the NPC menus')
    menu.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
