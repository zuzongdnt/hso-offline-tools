# Kiểm tra bản Java offline

## Offline 37 Lite

- Bản phát hành mang phiên bản MIDlet `37.0.0` và dùng máy chủ Offline 37, bộ hình x1 cùng cơ sở dữ liệu mẫu đã kiểm tra không chứa tài khoản hoặc nhân vật của người chơi.
- Trên J2ME Loader 1.8.2 và giả lập Android 14, bật chế độ máy bay, tắt Wi-Fi và dữ liệu. Cài đè JAR 32, đọc lại nhân vật thử, vào bản đồ, di chuyển, mở hành trang và mở lại game sau khi đã lưu.
- Trong lần khởi động đầu sau cập nhật, phải đóng hộp đang kết nối và bấm **Chơi tiếp** lại sau khi thế giới báo sẵn sàng. Chưa thử trên thiết bị thật hoặc trình giả lập Java khác.

## Offline 31 Lite

Ngày 18/11/2026, trình J2ME Loader 1.8.2 trên giả lập Android 14 cài JAR Lite, mở thế giới nội bộ và tạo nhân vật khi tắt cả Wi-Fi lẫn dữ liệu di động. Sau khi cài đè bản sửa gói tin thông tin nhân vật, nhân vật thử vẫn còn và vào được bản đồ mở đầu. Trên bản đồ hiển thị nhân vật, NPC và địa hình.

Bản Lite dùng gói hình x1 và dung lượng khoảng 12,2 MB. Kiểm tra máy chủ bao phủ việc hiển thị lại bot hết tàng hình, định dạng tin lính canh và tin di chuyển của bot Chiến trường. Chưa chơi hết trận Lôi đài hoặc Chiến trường trên J2ME Loader và chưa thử JAR Lite trên điện thoại thật.

## Bản Java 1.0.0

Ngày kiểm tra: 06/11/2026, múi giờ Việt Nam.

## Đã quan sát

- Build từ client **online Java v403**, không sử dụng Hso offline từng port cho R36S.
- Script xác nhận hash client đầu vào không đổi, ZIP/JAR không lỗi CRC, DEX hợp lệ và ghép đủ các đoạn dữ liệu thế giới.
- J2ME Loader **1.8.2 bản phát hành chính thức**, chạy trên máy giả lập **Android 14 / API 34, x86_64**.
- Cài/chuyển đổi JAR thành công bằng trình cài của J2ME Loader.
- Lần chạy đầu tự giải nén dữ liệu và mở thế giới tại loopback trên chính Android; log `WORLD_READY`.
- Bật chế độ máy bay, tắt Wi-Fi và dữ liệu di động trước khi đăng nhập, giữ nguyên trong các lượt thử tiếp theo.
- Đăng nhập `javaoff`, tạo nhân vật mới `zuzongjava` (ID 1), chọn nhân vật và vào bản đồ mở đầu.
- Nhìn thấy nhân vật, nhà, cây và NPC; di chuyển bằng nút cảm ứng; mở hành trang, thấy vật phẩm ban đầu và tiền.
- Log server ghi nhận vị trí di chuyển từ vùng bắt đầu đến `map=0`, khoảng `(144,522)`.
- Đưa game về nền ghi nhận lượt lưu. Dừng tiến trình thử nghiệm, mở lại J2ME Loader: thế giới mở từ save sẵn có, nhân vật vẫn ở danh sách; vào lại thấy vị trí gần căn nhà đã di chuyển tới, minimap `6:21` thay cho vị trí đầu `5:4`.
- Kiểm tra hồi quy công cụ xuất: giữ đúng mẫu boss `id=-1`, loại nhân vật/tài khoản thật; test `tests/test_export_world.py` đạt.

## Giới hạn

- Chưa thử điện thoại thật, Android 13, phiên bản J2ME Loader khác, toàn bộ bản đồ, nhiệm vụ, chiến đấu, shop, pet và Tinh Tú trên riêng client Java này.
- Cùng bộ xử lý server với APK offline, nhưng các kiểm tra APK/PC trước đó không thay thế kiểm tra mọi tính năng của JAR.
- Dữ liệu nội bộ không nằm trong RMS. Sao lưu RMS mặc định chưa sao lưu SQLite này. Gỡ/xóa dữ liệu J2ME Loader làm mất save.
- Chỉ chạy trên Android 13+ có J2ME Loader, không dùng cho R36S/FreeJ2ME, điện thoại Java cổ hoặc Java SE.

## Lệnh kiểm tra hồi quy

```powershell
python -m unittest discover -s tests -p test_export_world.py -v
```

Ảnh/log chạy thử được lưu riêng trên máy build, không đưa client/tài nguyên/save vào Git.
