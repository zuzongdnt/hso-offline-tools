# HSO Java Offline — J2ME Loader

Biến thể mới từ cùng bản vá server/SQLite của Android và PC trong repo này. Không sử dụng file Hso offline của tác giả khác từng dùng cho R36S. Client đầu vào là bản **online Java v403** của người build.

## Phạm vi

- Một file `.jar` chứa client, bộ xử lý thế giới và dữ liệu ban đầu; không cần chạy server trên PC, VPS hoặc Internet.
- Dành riêng cho **J2ME Loader trên Android 13 trở lên**. Đây không phải JAR cho điện thoại Java cổ, FreeJ2ME trên R36S hoặc Java SE trên Windows.
- Bộ xử lý chạy ngay trong tiến trình game trên Android. Client dùng loopback `127.0.0.1:19149` trên cùng thiết bị.
- Tài khoản offline mới: `javaoff`, mật khẩu `offline`. Tạo nhân vật trong game; không nhập tài khoản online thật.
- Dữ liệu nhân vật tách riêng khỏi bản APK/PC. Tự lưu mỗi 15 giây và khi MIDlet pause/thoát bình thường.

Phần ghép nối và công cụ build là mã bổ sung mới. Client/tài nguyên vẫn thuộc game gốc; server nền vẫn là upstream trong `upstream.json`. Repo không phải toàn bộ mã nguồn game do Zuzong viết từ đầu.

## Build

Chuẩn bị server theo README gốc và xuất `offline-world.zip` **không có** `--include-private-save`. Bản xuất giữ mẫu boss hệ thống `player.id=-1`, cần để server khởi động; không giữ nhân vật của người chơi. Công cụ từ chối world có tài khoản/nhân vật thật hoặc các bảng riêng tư đã có dữ liệu.

Cần JDK có thể compile target 8 và release 17, Android SDK Platform 36/Build Tools 36+, ASM 9.7.1, Python 3. Đặt các đầu vào riêng tư trong `inputs/`.

```powershell
python scripts/build_j2me.py --client inputs/KnightOnline_v403.jar --server build/server/target/HSO_Re_2-1.0-jar-with-dependencies.jar --source build/server --world build/world/offline-world.zip --sdk D:/Android/Sdk --jdk "C:/Program Files/Android/Android Studio/jbr" --asm inputs/asm-9.7.1.jar --out build/java-j2me
```

Kết quả: `build/java-j2me/HSO_Java_Offline_Zuzong.jar` và `SHA256.txt`. Luôn chọn `--out` mới. Script giữ nguyên file client đầu vào và kiểm tra hash sau khi build.

## Mở trên điện thoại

1. Cài [J2ME Loader](https://github.com/nikita36078/J2ME-Loader/releases/tag/1.8.2).
2. Chuẩn bị khoảng 1 GB bộ nhớ trống. Chép JAR sang điện thoại. Trong J2ME Loader, bấm dấu cộng, chọn file JAR và chờ cài đặt.
3. Bấm **START**, giữ màn hình game `240 × 320` trong lần thử đầu, rồi bấm **START** lần nữa.
4. Chờ chuẩn bị thế giới ở lần chạy đầu. File game lớn vì chứa dữ liệu thế giới offline.
5. Bấm **Chơi Tiếp: javaoff**, tạo nhân vật và vào game.

Thế giới nằm trong bộ nhớ riêng của ứng dụng J2ME Loader, thư mục `hso-java-offline`. Giữ nguyên tên game/vendor khi cập nhật. Gỡ hoặc xóa dữ liệu J2ME Loader sẽ làm mất save nội bộ này; bản sao lưu RMS thông thường của giả lập chưa bao gồm SQLite riêng.

## Kiểm tra

Tình trạng chạy thực tế được ghi trong `VERIFICATION.md`. Build thành công và cài JAR thành công chưa đủ chứng minh gameplay hoặc lưu/tải hoạt động.
