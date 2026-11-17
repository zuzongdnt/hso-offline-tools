# Các điểm đã đối chiếu với client

- `MainObject.paintPlayer`: khi đang cưỡi, vòng vẽ có chỉ số `i == 1` gọi `paintMount_Sau`. Nếu `getTypePart(1)` trả số âm, cả lớp ngựa sau lưng biến mất. Với Mộng Mơ ngồi (effect 255/256), giữ giá trị 0 ở lớp này và ẩn các bộ phận nhân vật thường khác.
- `MainObject.getFrameHorse`: mỗi pha có 21 frame, ba hướng có offset 0/7/14. Đã đọc đủ 10 thú cưỡi nhập thêm; số frame đều chia hết cho 21.
- Effect 220 đang gắn nhãn Hổ lửa, nhưng hình thực tế là mô-tô lửa. Frame đầu ở ba hướng có biên dưới tại y=34/33/31, trong khi mô-tô 246 nằm gần y=6. Profile Hổ lửa đặt y=0 làm xe rơi xuống dưới nhân vật; hiệu chỉnh riêng profile 332 lên 25 đơn vị.
- PowerShell 5.1 phát hơn 580 KB tiến độ CLIXML khi giải nén gói nhiều file. Java ProcessBuilder cũ không đọc pipe; thử nghiệm bị kẹt trước khi đọc pipe. `SilentlyContinue` hoàn tất trong 2,5 giây với cùng dữ liệu và pipe chưa được đọc.
- File `.hsosave` PC kiểm tra SHA-256 hợp lệ; đã nhập hai bản lưu PC vào bản sao SQLite tách biệt bằng lớp SQL iOS và so khớp đủ bốn bảng. Việc giữ mật khẩu thiết bị đích trong `SaveTransfer.replace` làm mật khẩu PC không được phục hồi khi trùng tên tài khoản.

Mã dịch ngược và ảnh đối chiếu nằm ở thư mục riêng trên máy, không đưa vào Git.
