# HSO Offline 29

## Đã bổ sung và kiểm tra

- Trình cập nhật PC có trạng thái tải/cài, log lỗi và thông báo hoàn tất. Tắt tiến độ PowerShell gây đầy pipe; chờ launcher cũ lưu và tắt database trước khi mở bản mới. Đóng gói PowerShell bằng UTF-8 BOM cho Windows PowerShell 5.1.
- Khôi phục giữ đúng tài khoản và mật khẩu trong file nguồn. Tài khoản Chơi mới được nối lại khi mã tài khoản tự động của thiết bị đích đã thay đổi. Tài khoản thường vẫn kiểm tra đúng mật khẩu.
- Bản PC dùng chung 4 worker bản đồ như bản di động. Đo trên máy đang chạy: Java giảm từ khoảng 847 luồng xuống khoảng 61; chưa kết luận mọi nguyên nhân lag đã hết.
- 45 bot thi đấu xếp giảm dần, cao nhất cấp 139. Mề bot lấy từ Mở Ly +15, dùng được cả bốn phái; thêm pet theo cấp và cánh có tiến trình cường hóa. Nhóm 55–64 không có cánh, từ cấp 90 có cánh +30.
- Shop Lôi đài có icon, 10 skin, giá 300 điểm mỗi món. Skin khác trở lại shop vàng. Client gốc chỉ có nhãn vàng/ngọc nên giá điểm nằm trong tên món và tiêu đề; cửa hàng không thu thêm vàng.
- Sửa gốc tọa độ profile 332 (Hổ lửa, hình tài nguyên là mô-tô lửa). Mộng Mơ giữ lớp ngựa phía sau và ẩn bộ phận nhân vật thường khi cưỡi; đổi đúng biến thể ngồi khi lên/xuống thú trên PC, Android và iOS.
- Chỉ số ngọc lấy từ ID/cấp viên ngọc, thay cho số ngẫu nhiên cũ. Ngọc cấp 5 Hỗn Nguyên/Khải Hoàn hiện 5 hit. Sửa các nhóm ID Lục Bảo, Khải Hoàn, Sinh Mệnh, Tâm Linh; ngọc tinh luyện Hỗn Nguyên không mất nửa máu. Hiệu ứng dùng packet native có metadata và đầy đủ ID nhân vật.
- Hấp thụ có hiệu ứng đỏ. Tàng hình hiển thị mắt cho chủ, ẩn nhân vật với người khác trong thời gian hiệu lực. Mề có Tàng hình/Giáp hắc ám được nâng tỉ lệ lên tối thiểu 15%; sửa phép tung tỉ lệ để khớp phần trăm hiển thị.
- Toàn bộ nguyên liệu mề thuộc type 54, gồm cấp 1–3, có giá 1 vàng. Về làng bằng `/velang`, bảng xếp hạng hoặc mục Thông tin có nút Về làng nhanh.
- Mở sự kiện Đứa Bé: ngẫu nhiên bản đồ, thông báo kênh thế giới, tồn tại 20 phút; dẫn bằng kẹo hồ lô về Mr Master, hoặc nhận ngay khi ở gần. Sau khi được nhận, 90 phút mới thả bé khác; hết 20 phút thì thả lại ngay. Dùng `/detu` để tìm bé và mở lựa chọn. Lisa có kẹo/bùa gọi/vé luyện; phần luyện 180 phút, giới hạn cấp và lưu đệ tử dùng hệ thống sẵn có.

Giá nhận ngay 50 ngọc là cấu hình của bản offline, không xác nhận là giá máy chủ chính thức.

## Kiểm tra

- `tests/Offline29WorldCheck.java`: world thật với SQLite riêng, bản sao lưu người dùng được truyền từ đường dẫn ngoài Git; kiểm tra khôi phục và mật khẩu, bot, shop có icon, trừ điểm, nguyên liệu, công thức ngọc, packet hiệu ứng, sinh/dẫn/nhận/hết hạn đứa bé và lưu đệ tử.
- `tests/Offline27Check.java`: hồi quy bộ Tinh Tú và đếm hit ngọc; thêm kiểm tra Sinh Mệnh không bị hiểu nhầm thành Khải Hoàn.
- `tests/check_pc_updater_pipe.py`, `tests/check_pc_update_shutdown.py`: tiến độ không làm nghẽn pipe và launcher cũ phải tắt xong trước khi cài/mở bản mới; database được sao lưu.
- PC đã đăng nhập và vào bản đồ bằng nhân vật cấp 59 từ file sao lưu được cung cấp. Chưa thử trực tiếp toàn bộ tổ hợp skin/thú cưỡi và chưa chạy trên iPhone thật.

## Tham khảo

- [Ngọc khảm – bài hướng dẫn gốc](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=3955240&p=0&sz=15).
- [Đệ tử – bài hướng dẫn gốc](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=4671884&p=0&sz=15).

Các chức năng chưa hoàn tất ở bản 28 như Linh thú đầy đủ, Mê cung và mở rộng Chiến trường vẫn là hạng mục riêng; không coi bản sửa lỗi này là đã hoàn thành toàn bộ yêu cầu cũ.
