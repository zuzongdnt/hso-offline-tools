# HSO Offline 27: bản thử server

Nguồn nền: JAR server trong bộ cài PC 26 trùng SHA-256 với `build/server-offline23/target/HSO_Re_2-1.0-jar-with-dependencies.jar`. JAR phát hành nằm tại `build/server-offline27-release/target/HSO_Re_2-1.0-jar-with-dependencies.jar`. Đã đóng gói APK Android và ZIP cập nhật PC riêng; chưa thay file trong bộ cài đang dùng, chưa mở hoặc sửa database nhân vật, chưa tạo IPA 27.

## Đã làm

- Lôi đài: chờ 3 giây trước mỗi hiệp; chặn di chuyển và dùng kỹ năng khi chờ; đặt lại vị trí, máu và mana sau mỗi hiệp; ghép bot theo nhóm 55-64, 65-74, tiếp đến 135-139. Cấp 50-54 ghép nhóm đầu. Giới hạn người chơi cấp 50-139. Bỏ mục nhận quà thử.
- Thú cưỡi: không xóa trạng thái đang cưỡi khi nhân vật chết; gửi lại trạng thái thú cưỡi sau hồi sinh tại chỗ. Cần xác nhận bằng hình ảnh trên client PC và Android.
- Ngọc: Khải Hoàn không kích hoạt nếu chưa khảm. Nhiều viên Hỗn Nguyên và Khải Hoàn lấy trung bình số đòn cần thiết; ví dụ 25, 15, 10 cho kết quả 16. Lục Bảo được thử kích hoạt lúc chịu sát thương từ quái hoặc người chơi. Tỷ lệ kích hoạt Lục Bảo vẫn dùng giá trị bản nền vì bài diễn đàn không cung cấp bảng tỷ lệ đầy đủ.
- Tinh Tú: xác nhận bằng kiểm tra lớp nhân vật rằng Chính xác chỉ có tác dụng khi vũ khí và hai nhẫn thuộc nhóm 2 đều được mặc. Gửi tên riêng "Chính xác (chưa kích hoạt)" cho client khi chưa đủ nhóm.
- Mề đay: cho phép đeo khác phái; năm người bán trong khu mua bán được đặt rải vị trí, giữ các mức +6 đến +10 như cũ. Mề đay +15 chỉ lấy từ Mở Ly. Chưa kiểm chứng chỉ số của từng mề đay.
- Chiến trường: giữ cơ chế bản nền; phần đăng ký bất kỳ giờ nào, bot người chơi và cân bằng chỉ số được để sau.
- Dòng thông báo: NPC Mr Ballard và thông báo định kỳ hướng dẫn đến lôi đài, chiến trường, khu mua bán. Bỏ tin quảng bá Tài Xỉu định kỳ.

## Chưa xong

- Linh thú hoàn chỉnh: ghép bốn mảnh mùa, ấp trứng 48 giờ, sức khỏe, cho ăn, lên cấp và kỹ năng.
- Toàn bộ chỉ số và hình ảnh ngọc khảm, đặc biệt hiệu ứng đỏ của Ngọc Hấp Thụ. Bài ngọc được dẫn không mô tả Ngọc Hấp Thụ hoặc mã hiệu ứng đỏ.
- Shop đổi skin bằng điểm Lôi đài, chuyển skin khỏi shop cũ, trang phục bot mới, danh sách bot trên bảng xếp hạng và thách đấu từ bảng.
- Giảm giá nguyên liệu mề đay cấp 3; đối chiếu chỉ số mề đay từ Mở Ly; cơ chế ẩn thân và các hiệu ứng mề đay khác.
- Mê cung: các map 74-79 có sẵn trong dữ liệu nền nhưng chưa có vòng chơi 5 phút, vé, cửa canh, thùng và Đèn Thần.
- Chiến trường: bot người chơi các phe, xác minh cân bằng chỉ số trong trận và kiểm tra luồng kết thúc/nhận quà.
- Kiểm tra gameplay trực tiếp trên client PC/iPhone và trang phục Hiệp sĩ Mộng Mơ khi cưỡi thú.

## Kiểm tra đã chạy

- Biên dịch 12 lớp Java bị ảnh hưởng bằng JDK đi kèm bộ cài 26, dựa trên JAR server nền. Maven không có trong PATH nên chưa chạy build Maven đầy đủ.
- `tests/Offline27Check.java` chạy trực tiếp trên JAR bản thử: Khải Hoàn không ngọc; trung bình ngọc 25, 15, 10; trạng thái kích hoạt và tên hiển thị của Chính xác.
- `scripts/stage_offline27.py` dựng lại mã nguồn từ bản 23 sang thư mục mới; không ghi đè thư mục đã có. Phiên bản dữ liệu/cập nhật của server tăng lên 27.
- Android: sửa cuộc đua khởi động, cho luồng kết nối chờ server offline sẵn sàng. APK thử versionCode 239 đã cài cập nhật trên giả lập Android 10, vào được màn chọn nhân vật mà không có `ECONNREFUSED` của lần khởi động mới. Chưa kiểm tra trên điện thoại thật và chưa xác định nguyên nhân vùng đen ở chế độ dọc trong ảnh người dùng.

Nguồn đối chiếu: các bài diễn đàn về [ngọc khảm](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=3955240&p=0&sz=15), [Tinh Tú](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=5957634&p=0&sz=15), [mề đay](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=2909490&p=0&sz=15), [linh thú](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=6567565&p=0&sz=15), [mê cung](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=4856759&p=0&sz=15), [chiến trường](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=1752372&p=0&sz=155).
