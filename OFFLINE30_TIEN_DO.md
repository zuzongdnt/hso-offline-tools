# HSO Offline 30

## Đã sửa

- File chuyển máy có thể chứa nhiều tài khoản. Sau khi nhập, game ghi rõ tài khoản có nhân vật cấp cao nhất và dùng tài khoản đó khi bấm Chơi mới, kể cả lần đầu trên thiết bị mới gửi cặp mã tự động `1/1`. Đổi tài khoản vẫn kiểm tra mật khẩu gốc; cả hai nhân vật trong file đều được giữ. Không công khai thông tin đăng nhập hoặc đóng gói dữ liệu cá nhân vào bản phát hành.
- Hiệu ứng Lục Bảo dùng hoạt ảnh native 30; Sinh Mệnh dùng 32; Lú lẫn dùng 24 theo xác nhận của người dùng. Lú lẫn trên trang bị có tỉ lệ tối thiểu 15%, thống nhất giữa mô tả và chiến đấu; hiệu ứng được gửi tới đúng đối tượng. Các hoạt ảnh chưa xác minh giữ nguyên và chưa được coi là đã đối chiếu đầy đủ với bản chính.
- Hổ lửa 332 ngừng bán và ngừng kích hoạt; đồ đã có vẫn nằm trong túi. Cá chép giữ cùng độ cao người cưỡi ở ba pha đi ngang, giữ nguyên hướng lên/xuống và các thú khác. Đây là chỉnh bảng tọa độ, chưa xác nhận trực quan toàn bộ động tác trên thiết bị thật.
- Danh sách thi đấu dùng đúng màn hình Top native, loại danh sách 6 có nút Thách đấu. Người chơi mới đứng cuối 45 bot; thắng lấy hạng đối thủ, thua giữ hạng. Điểm Lôi đài không thay đổi khi thách đấu. Thứ hạng và trạng thái phải trả 1 ngọc sau trận thua được lưu theo nhân vật; chờ 2 phút khi thách lại người vừa thua. Trận đấu tái sử dụng bộ mô phỏng hiệp đấu hiện có.
- Huy hiệu Lôi đài tự lên theo mốc điểm, giữ bậc cao nhất đã đạt khi đổi skin bằng điểm. Loại bỏ trạng thái huy hiệu thử cũ. Mốc hiện dùng: 840, 1260, 1680 và 2520.
- Mề bán sẵn và mề Mở Ly được chỉnh mức sát thương theo ảnh tham khảo. Mề xạ thủ +7 có 1405 sát thương vật lý, 27,25% vật lý và 25,96% ánh sáng; các cấp khác tăng theo bộ cường hóa hiện tại. Mề tự chế đã có chỉ số riêng được giữ; chỉ những mề mang bộ chỉ số cố định cũ của shop mới được cập nhật. Đây là cấu hình offline được hiệu chỉnh theo ảnh, **chưa xác nhận công thức ngẫu nhiên toàn bộ mề của server chính thức**.
- Mr Ballard nhận đăng ký bất kỳ lúc nào, cấp tối thiểu 40; phí 500.000 vàng hoặc 2 ngọc. Bấm Vào chiến trường để bắt đầu ngay. Cả bốn phe đều có nhà trong lượt chơi một người; giữ hệ thống lính canh, bản đồ và điểm sẵn có. Đây là sửa lối vào, chưa thay toàn bộ AI hoặc mọi luật chiến trường trong bài hướng dẫn.
- Vé mê cung 241/243 đã mở được lượt vượt mê cung riêng dài 5 phút, đi qua các phòng native được xáo thứ tự. Thần canh cửa phải chết mới qua cửa. Tới phòng kho báu chọn Nhặt Đèn Thần; có thể dùng `/mecung` mở lại lựa chọn và `/velang` để thoát. Đèn có quà tiêu hao và kinh nghiệm. **Chưa đủ thùng gỗ/bom, đồ thời trang thời hạn và toàn bộ bảng quà của sự kiện chính thức**.

## Cách cập nhật

PC bấm Cập nhật trong game. Android cài đè APK. iOS ký/cài đè IPA bằng iLoader khi IPA đã có trên bản phát hành.

Sau khi cập nhật, nhập lại file `.hsosave`, tắt hẳn game và mở lại, bấm Chơi mới. Kết quả nhập sẽ ghi rõ tài khoản được chọn; file có hai nhân vật vẫn giữ cả hai. Nếu muốn nhân vật khác, dùng Đổi tài khoản với thông tin của tài khoản đó.

## Kiểm tra và giới hạn

`tests/Offline30WorldCheck.java` dùng SQLite riêng và đường dẫn file sao lưu nằm ngoài Git. Đã kiểm tra: chọn đúng tài khoản khôi phục cho cả mã tự động cũ và Chơi mới lần đầu; mề +7; danh sách native và kết quả trận thách đấu không cộng điểm Lôi đài; huy hiệu tự lên; vé mê cung tiêu hao đúng một vé, nhận đèn một lần, trả về đúng bản đồ; chiến trường mở và vào ngay với đủ bốn phe. Các kiểm tra ngọc, shop, pet/cánh bot và đệ tử của bản 29 vẫn chạy kèm.

Tai nghe chưa có ánh xạ hình được xác nhận. Chưa khẳng định toàn bộ chỉ số mề hoặc hoạt ảnh đều trùng bản chính. Chưa thử bản này trực tiếp trên iPhone thật; chưa kiểm tra toàn bộ tổ hợp ngoại trang/thú cưỡi.

## Nguồn đối chiếu

- [Top PK / Top thi đấu](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=2182676&p=0&sz=15).
- [Mê cung](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=4856759&p=0&sz=15).
- [Chiến trường](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=1752372&p=0&sz=15).
- [Chế tạo mề đay](http://forum.knightageonline.com/app/index.php?for=forum&do=list&uid=2909490&p=0&sz=15).
