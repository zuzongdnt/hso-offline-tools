# Java offline cho J2ME Loader

- Đầu vào là client online Java v403, entry point `com.silverknight.TemMidlet`; không sử dụng bản Hso offline của tác giả khác.
- Giữ client và tài nguyên gốc ở máy người build. Repo chỉ có công cụ sửa bytecode và phần ghép nối mới.
- `CLib.mSocket(String,int)` được gọi từ luồng kết nối; chờ thế giới sẵn sàng tại đây để không chặn luồng UI.
- `connectHTTP` trả danh sách offline; socket chỉ nối `127.0.0.1:19149` trên cùng điện thoại.
- Sáu hook: danh sách server, socket, khởi tạo MIDlet, thông tin đăng nhập mặc định, pause và destroy.
- J2ME Loader dùng DX để chuyển `.class`; bộ xử lý Java 17 được D8 chuyển trước thành DEX và đặt dưới dạng resource, tải bằng DexClassLoader trên Android 13+.
- J2ME Loader đọc resource vào mảng byte. Chia ZIP thế giới thành đoạn 4 MiB để tránh cấp phát một mảng hơn 160 MiB.
- Thế giới dùng cùng server nền và SQLite bridge với bản Android offline. Mã nền vẫn thuộc upstream được ghim trong `upstream.json`.
- Save mới tại files nội bộ của J2ME Loader, thư mục `hso-java-offline`; không dùng save của APK/PC/bản port cũ.
- Bản xuất sạch phải giữ `player.id=-1` là mẫu boss hệ thống. Xóa cả mẫu này làm `BossTG` khởi tạo Player thiếu Body và lỗi trước khi mở cổng game. Exporter chỉ giữ riêng ID này khi không xuất save.
