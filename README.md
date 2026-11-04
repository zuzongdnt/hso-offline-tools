# HSO Offline Tools — Zuzong

Mã sửa và công cụ build bản HSO offline độc lập trên Windows và Android 13 trở lên. Server chạy trên chính thiết bị; dữ liệu giữa các thiết bị không đồng bộ. Chưa có bản iOS offline.

## Có gì trong repo

- `patches/server-offline.patch`: các thay đổi trên server Java, gồm shop, Tinh Tú, pet và thưởng Zulu.
- `android/src`: server SQLite trong ứng dụng, lớp tương thích JDBC, khởi động và tự lưu.
- `pc/ClientPatcher`: sửa kết nối client PC về `127.0.0.1:19139`, danh sách Offline và thư mục lưu riêng.
- `scripts`: chuẩn bị server, xuất thế giới cục bộ, sửa APK và build Android.
- `tests`: kiểm tra gói tin, mua đồ bằng vàng, nâng Tinh Tú và ấp trứng.

Repo không chứa client/tài nguyên game, database nhân vật, tài khoản thật hoặc khóa ký APK. Cần chuẩn bị các đầu vào đó ở máy của bạn trong thư mục `inputs/` đã được bỏ qua bởi Git.

## Những lỗi đã sửa trong offline.2

- Nâng Tinh Tú giữ nguyên option 58–60: đây là ID ngọc trong ba ô khảm, không phải chỉ số được tăng ngẫu nhiên. Ô trống `-1` cũng được giữ nguyên.
- Trứng Thỏ `4622`, Dê con `4708` đã có xử lý ấp. Ánh xạ đủ 14 loại trứng/pet theo hai chiều; Yêu tinh dùng đúng icon khởi đầu.
- Kiểm tra vị trí hành trang và loại trứng trước khi tiêu hao; chỉ trứng đang ấp mới chặn lượt ấp tiếp theo. Có thông báo bắt đầu ấp và thời gian 10 phút.
- Sửa nhầm biến khi cập nhật danh sách trứng còn đang ấp sau khi một trứng nở.
- Android lưu khi đưa app về nền, cùng với tự lưu mỗi 30 giây. Cài cập nhật cùng package/chữ ký giữ dữ liệu ứng dụng.

Ngọc đã bị thay đổi ở bản cũ không thể tự suy ra loại ban đầu. Trứng Thỏ/Dê dùng bốn dòng thuộc tính nền của server; chưa bổ sung các dòng phụ riêng chưa có dữ liệu xác minh. Chức năng kích hoạt dòng ẩn Tinh Tú vẫn chưa hoàn thiện.

## Build server Java

Cần Git, Python 3, JDK 17 trở lên và Maven. Upstream được ghim theo `upstream.json`.

```powershell
git clone https://github.com/ALKAstraverse/hso-server.git inputs/upstream
git -C inputs/upstream checkout 897a013cfe464e88b145cb8c06718fb819001be0
python scripts/prepare_server.py --upstream inputs/upstream
mvn -f build/server/pom.xml package -DskipTests
```

Lệnh chuẩn bị không sửa checkout gốc và từ chối ghi đè thư mục đầu ra đã có. Sau khi build, JAR chạy là `build/server/target/HSO_Re_2-1.0-jar-with-dependencies.jar`.

Để chạy PC, cần `data/` và database MySQL/MariaDB tương thích được chuẩn bị riêng. Sao chép `hso.conf.example` thành `hso.conf` ở thư mục chạy, điền thông tin database của bạn. Server PC dùng cổng MySQL `33317`, cổng game `19139`. Không dùng lại cổng/database của bản online. Các script này không khởi tạo hoặc thay thế dữ liệu nhân vật của bạn.

## Sửa client PC

Cần .NET 10. Truyền DLL gốc và đường dẫn DLL kết quả khác nhau:

```powershell
dotnet run --project pc/ClientPatcher -- inputs/Assembly-CSharp.dll build/Assembly-CSharp.dll
```

Đặt DLL kết quả vào bản sao thư mục game PC tại `hso_v403_Data/Managed/Assembly-CSharp.dll`. Tạo thư mục `local-save` bên cạnh file EXE trước khi mở game. Không sửa trực tiếp bản client đang dùng để chơi online.

## Xuất dữ liệu Android

Từ database cục bộ của bạn và thư mục tài nguyên server:

```powershell
python scripts/export_world.py --mysql inputs/mariadb.exe --defaults inputs/database-client.ini --database hso_offline --data inputs/data --config inputs/hso.conf --out build/world
```

Mặc định không xuất tài khoản, nhân vật, clan, giftcode hoặc lịch sử thanh toán. Nếu muốn giữ tài khoản/nhân vật của chính bạn để chơi, thêm `--include-private-save`; khi đó chỉ giữ file world/APK kết quả ở nơi riêng tư. Bản xuất không có tài khoản cần được bạn khởi tạo tài khoản theo schema của server trước khi đăng nhập. Công cụ không gửi dữ liệu lên Internet.

## Build Android từ APK v403b của bạn

Cần JDK, Android SDK Platform 36, Build Tools 36 trở lên, Apktool 3 và keystore của bạn. Ví dụ Windows, thay các đường dẫn bằng máy của bạn:

```powershell
$env:HSO_KEYSTORE_PASSWORD = 'mat-khau-keystore-cua-ban'
python scripts/build_android.py --apk inputs/Knight_Online_Android-v403b.apk --server build/server/target/HSO_Re_2-1.0-jar-with-dependencies.jar --source build/server --world build/world/offline-world.zip --apktool inputs/apktool.jar --sdk C:/Android/Sdk --jdk C:/Java/jdk-17 --keystore inputs/offline.jks --alias offline
```

APK kết quả nằm trong `build/android/HSO_Offline.apk`. Mỗi lần build chọn thư mục `--out` mới để giữ lại kết quả trước. App có package `com.zuzong.hso.offline403`, versionCode `214`. Để cập nhật app đã cài, phải dùng cùng khóa ký; repo không cung cấp khóa ký cá nhân.

## Kiểm tra

Xuất fixture template từ database của bạn, rồi truyền thư mục chạy có `data/` để kiểm tra:

```powershell
python scripts/export_fixtures.py --mysql inputs/mariadb.exe --defaults inputs/database-client.ini --database hso_offline --out inputs/fixtures.json
python scripts/test_server.py --jdk C:/Java/jdk-17 --jar build/server/target/HSO_Re_2-1.0-jar-with-dependencies.jar --fixtures inputs/fixtures.json --runtime inputs/runtime
```

Đã tái hiện lỗi đổi ngọc trên JAR cũ và chạy kiểm tra hồi quy trên JAR mới: giữ nguyên ngọc qua nâng thành công/thất bại, cả bốn mốc cấp, đủ 14 loại trứng, không tiêu hao khi yêu cầu sai hoặc đang ấp trứng khác. APK offline.2 đã thử qua giao thức thực trên máy giả lập Android 14 khi bật chế độ máy bay, tắt Wi-Fi: mua trứng Thỏ tại shop, gửi ấp trong Khu Vườn và nhận pet nở. Thời gian nở được rút ngắn bằng lệnh quản trị chỉ trong lượt kiểm tra. Chưa thử APK này trên điện thoại thật.

## Nguồn và giấy phép

Server nền: [ALKAstraverse/hso-server](https://github.com/ALKAstraverse/hso-server), commit được ghi trong `upstream.json`. Repo này phân phối bản vá để giữ rõ nguồn gốc của code nền, không chép client/tài nguyên game vào repo và không cấp lại giấy phép cho chúng. Các công cụ mới, bridge, bài kiểm tra và phần sửa do dự án này tạo được phát hành theo [MIT](LICENSE). Upstream hiện chưa khai báo giấy phép; điều đó không được thay đổi bởi giấy phép của công cụ trong repo này.
