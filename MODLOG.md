# Các điểm đã đối chiếu với client

- `MainObject.paintPlayer`: khi đang cưỡi, vòng vẽ có chỉ số `i == 1` gọi `paintMount_Sau`. Nếu `getTypePart(1)` trả số âm, cả lớp ngựa sau lưng biến mất. Với Mộng Mơ ngồi (effect 255/256), giữ giá trị 0 ở lớp này và ẩn các bộ phận nhân vật thường khác.
- `MainObject.getFrameHorse`: mỗi pha có 21 frame, ba hướng có offset 0/7/14. Đã đọc đủ 10 thú cưỡi nhập thêm; số frame đều chia hết cho 21.
- Effect 220 đang gắn nhãn Hổ lửa, nhưng hình thực tế là mô-tô lửa. Frame đầu ở ba hướng có biên dưới tại y=34/33/31, trong khi mô-tô 246 nằm gần y=6. Profile Hổ lửa đặt y=0 làm xe rơi xuống dưới nhân vật; hiệu chỉnh riêng profile 332 lên 25 đơn vị.
- PowerShell 5.1 phát hơn 580 KB tiến độ CLIXML khi giải nén gói nhiều file. Java ProcessBuilder cũ không đọc pipe; thử nghiệm bị kẹt trước khi đọc pipe. `SilentlyContinue` hoàn tất trong 2,5 giây với cùng dữ liệu và pipe chưa được đọc.
- File `.hsosave` PC kiểm tra SHA-256 hợp lệ; đã nhập hai bản lưu PC vào bản sao SQLite tách biệt bằng lớp SQL iOS và so khớp đủ bốn bảng. Việc giữ mật khẩu thiết bị đích trong `SaveTransfer.replace` làm mật khẩu PC không được phục hồi khi trùng tên tài khoản.

Mã dịch ngược và ảnh đối chiếu nằm ở thư mục riêng trên máy, không đưa vào Git.
# Offline 30 — các mốc đã kiểm tra

- Client PC `ReadMessenge.List_Serverz` dùng list type 6 để hiện nút Thách đấu; type 1 chỉ là bảng top thường. `List_Server` gửi action 0 và tên đối thủ qua packet -101. Xem trang bị trong danh sách này yêu cầu packet 49 type 100.
- Nhánh đăng nhập Chơi mới lần đầu gửi `1/1` và trước đây luôn tạo tài khoản mới. Cần chọn tài khoản vừa nhập trước nhánh này, ngoài việc nối lại tên tài khoản tự động đã lưu.
- Profile Cá chép đầu tiên là 24; bảng DY_CHAR_MOVE có 12 số, sáu số đầu dành cho hai hướng ngang. Chỉnh cả ba pha mỗi hướng về 29; các hướng dọc giữ nguyên.
- Hoạt ảnh 112_30 / 112_32 / 112_24 có đủ PNG và metadata trong bộ tài nguyên đã cung cấp; ý nghĩa Lục Bảo / Sinh Mệnh / Lú lẫn được người dùng xác nhận. Chưa mở rộng bảng ý nghĩa cho các ID khác.
- Item4 241 là vé mê cung, 242 là Đèn Thần, 243 là gói vé. Map native 74–79 có hai cửa và các thần canh cửa 149/155. Item3 tai nghe native 4718/4719 là type 26, part 98/99; món nhập thêm 4845 đang có part 0. Chưa có ánh xạ hình hợp lệ, không gán tùy ý sang hiệu ứng khác.

## Offline 36

- PNG x1 trong JAR 1.8.3 trùng từng pixel với bộ Offline ở các mã 12–20, 22–23, 42 và 45. Mã 54 có ảnh khác giữa hai bản. HSONTC xác nhận Bỏng lạnh 12, Bỏng lửa 13, Lú lẫn 14, Khiên ma thuật 15 và Ngọc Lục bảo 20. Bản 36 dùng ảnh 22 cho Khải hoàn theo ảnh từ Zuzong.
- `ReadMessenge.objectMove` nhận byte 127 để chạy hiệu ứng đẩy lùi. `DataSkillEff` dùng cờ di chuyển 1 để khóa chân và cờ 17 để tàng hình. `EffFormServer` ánh xạ loại 5 sang hiệu ứng đóng băng 100 trong một bảng mã riêng.
- Hình địa hình và minimap của map 36 khớp ảnh thách đấu. Map 102 là Lôi đài thường. Hai điểm bắt đầu của mỗi map nằm trên ô có thể đi.
