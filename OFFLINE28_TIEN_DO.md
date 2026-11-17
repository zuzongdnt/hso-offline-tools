# Offline 28

## Các sửa đã đưa vào mã và gói cập nhật

- Thú cưỡi: giữ trạng thái khi chết bởi AI lính canh; gửi lại thú cưỡi dùng từ túi khi vào map/hồi sinh về làng. Bản 27 chỉ sửa hai đường chết trong MapService nên còn sót AI.
- Lôi đài: đổi map để đặt lại hiệp, tránh bắt nhân vật chết tự chạy đường về chỗ cũ; PC/Android mở lại phím khi nhận map mới. Chưa xác minh toàn bộ kết thúc trận trên điện thoại thật.
- Shop skin Lôi đài: Mrs Oda, mục Shop skin Lôi đài. Các skin phù hợp, có tài nguyên trong danh mục được chuyển khỏi shop vàng, giá thiết kế offline 300 điểm/món. Có phân trang, kiểm tra điểm/ô trống và trừ điểm sau khi thêm đồ.
- Danh sách thi đấu: NPC bảng xếp hạng có Danh sách thi đấu, Top thi đấu và Về làng. Tạo danh sách 45 bot qua 9 nhóm cấp; chọn bot để xem trang bị hoặc thách đấu trong nhóm cấp của mình. Đây là danh sách bot offline của tính năng, không phải dữ liệu xếp hạng server chính thức.
- Mở Ly: hoàn tất lượt đang chờ bằng lựa chọn server đã lưu khi client gửi mã chơi tiếp; yêu cầu ba ô trống; khi trúng mề +15 có bảng nhận quà gồm tên và icon. Lượt không trúng vẫn có bảng quà an ủi.
- Mề đay: không giấu dòng thuộc tính khi người xem khác phái; đổi đơn vị thời gian hiển thị của Bỏng lửa, Tàng hình, Lú lẫn từ giây sang mili giây. Mề tạo mới dùng dòng đặc trưng Chí mạng/Né/Phản sát thương/Xuyên giáp theo phái. Các số còn lại là cấu hình offline có từ trước, chưa xác minh toàn bộ với game gốc.
- Hiệp sĩ Mộng Mơ: khôi phục đủ 72 khung từ tài nguyên gốc đang có, dùng bộ chọn khung chuẩn; thêm biến thể ngồi cưỡi lấy từ cùng tài nguyên, bỏ phần thấp dưới thân; ngăn hiệu ứng đứng yên vẽ đè lúc cưỡi. PC, Android và iOS đều nhận tài nguyên mới. Cần người dùng kiểm tra hình thực tế khi đánh và cưỡi.
- Đối chiếu ảnh người dùng: Mặt nạ đọa đày có Phòng thủ 5%, Máu 10%, Không tăng Exp 100%; Áo choàng Công tước có năm dòng sát thương, Máu, Mana đều 10%. Áp lại cho đồ đã lưu khi tải nhân vật.
- Về làng: mục tại NPC bảng xếp hạng hoặc chat `/velang`. Trong Lôi đài thì rời trận; khi đang ở phó bản/chiến trường cần rời hoạt động trước.
- PC: bỏ giới hạn ở lệnh đặt FPS và xóa khóa đường đi khi nhận map. Chưa đo FPS/CPU trên máy người dùng; không tuyên bố đã hết lag.

## Kiểm tra

- Maven build đầy đủ server 28 và dự án server iOS.
- Offline27Check: hồi quy ngọc/Tinh Tú.
- Offline28Check: thời gian hiệu ứng mề, dòng theo phái, hiển thị khác phái; mua skin đủ/thiếu điểm và lặp yêu cầu; Mở Ly hoàn tất lượt với mã chọn -1 và có bảng quà an ủi.
- APK versionCode 240 cài đè trên giả lập Android 10. Đã bắt và sửa lỗi Stream.toList không tương thích Android 10; lần khởi động sau server lên cổng 19139, không có lỗi khởi động mới trong log được đọc.
- iOS chỉ kiểm tra build arm64 và cấu trúc IPA; người dùng tự thử gameplay theo yêu cầu.

## Còn thiếu hoặc chưa xác minh

- Chưa bổ sung mọi skin mới của game gốc. Hai ảnh icon không có tên chưa đủ để xác định chắc chắn toàn bộ món hoặc mã hiệu ứng cây gậy.
- Chưa xác minh toàn bộ chỉ số mề +15 với bản gốc. Số `0s` trước đó là sai đơn vị hiển thị; Body vốn có chuyển giá trị giây nhỏ thành mili giây lúc kích hoạt.
- Danh sách Top thi đấu hiện là danh sách bot offline, chưa có mùa thi đấu và bảng điểm bot lưu lâu dài.
- Linh thú hoàn chỉnh, toàn bộ hiệu ứng ngọc (gồm đỏ Hấp Thụ), mê cung và mở rộng chiến trường vẫn chưa hoàn thành. Chiến trường được người dùng cho để sau.
- Chưa xác nhận hết lỗi hình ảnh thú cưỡi/Hiệp sĩ Mộng Mơ bằng lượt chơi trên thiết bị thật. Bản này là bản sửa để người dùng kiểm tra tiếp.
