# HSO Offline Tools — Zuzong

Mã sửa và công cụ build bản HSO offline độc lập trên Windows và Android 10 trở lên. Server chạy trên chính thiết bị, mỗi thiết bị có dữ liệu lưu riêng.

## Có gì trong repo

- `patches/`: các thay đổi trên server Java, gồm shop, Tinh Tú, pet, thưởng Zulu và phó bản.
- `android/src`: server SQLite trong ứng dụng, lớp tương thích JDBC, khởi động và tự lưu.
- `pc/ClientPatcher`: sửa kết nối client PC về `127.0.0.1:19139`, danh sách Offline và thư mục lưu riêng.
- `java-j2me`: [bản Java offline dành cho J2ME Loader trên Android 13+](java-j2me/README.md), dùng client online v403 và nhúng cùng bộ xử lý thế giới vào JAR.
- `scripts`: chuẩn bị server, xuất thế giới cục bộ, sửa APK và build Android.
- `tests`: kiểm tra gói tin, mua đồ bằng vàng, nâng Tinh Tú và ấp trứng.

Repo không chứa client/tài nguyên game, database nhân vật, tài khoản thật hoặc khóa ký APK. Cần chuẩn bị các đầu vào đó ở máy của bạn trong thư mục `inputs/` đã được bỏ qua bởi Git.

## Offline 32

Bản Java dùng đúng độ dài trường số lượng vật phẩm trong hành trang và rương. Client PC, Android và iOS tính vị trí ô đang chọn theo trang. Đồ thời trang dùng chỉ số có sẵn và không thể cường hóa, chuyển hóa cấp cường hóa, đục lỗ hoặc khảm ngọc.

Chuẩn bị server bằng `python scripts/stage_offline32.py --source build/server-offline31 --out build/server-offline32`. Bản PC áp `--inventory` của `pc/RepairPatcher` lên DLL đã vá ở bản 30 hoặc 31. Bản Android và iOS Lite dùng `scripts/compact_mobile_world.py` trên APK/IPA bản 30, sau đó ghép gói kết quả bằng `--lite` của trình build tương ứng. Hai bản Lite giới hạn zoom tài nguyên ở x2.

## Offline 31

Sửa trạng thái tàng hình tồn tại quá hạn ở Lôi đài và gói tin hiển thị lính canh ở Chiến trường. Khu giao tranh có tám bot chia bốn phe. Chúng đi theo ô đất, tìm mục tiêu khác phe và hồi sinh sau khi bị hạ.

Chuẩn bị server bằng `python scripts/stage_offline31.py --source build/server-offline30 --out build/server-offline31`. Sau khi build server, [đóng gói JAR Lite](java-j2me/README.md) bằng `--compact` và gói tài nguyên bản 30 qua `--cosmetics`.

## Offline 30

[Phạm vi bản 30 và các phần chưa hoàn tất](OFFLINE30_TIEN_DO.md). Sửa chọn nhân vật khi khôi phục, hiệu ứng 30/32/24, Top thách đấu độc lập với điểm Lôi đài, mề shop, lối vào chiến trường và vé mê cung.

Chuẩn bị server bằng `python scripts/stage_offline30.py --source build/server-offline29-release --out build/server-offline30`. Tạo overlay bằng `python scripts/package_offline30_assets.py --previous inputs/offline29-cosmetics.zip --out build/offline30-cosmetics.zip`. PC giữ DLL bản 29 và dùng `scripts/package_offline27_pc.py --version 30`; Android versionCode 242. iOS dùng `scripts/prepare_ios_server.py`, nguồn riêng nhánh `offline30-build`, IPA build 18.

Nếu runner của repo riêng bị chặn hạn mức, có workflow thủ công `.github/workflows/ios-world.yml` dùng runner tiêu chuẩn của repo công khai. `python scripts/dispatch_ios_build.py --ref offline30-build` tạo liên kết tải mã riêng tạm thời trong Actions secret, không lưu PAT vào repo công khai. Có thể chọn `--runner macos-26` hoặc `--runner macos-15-intel`; bản Intel biên dịch chéo sang iOS arm64. Liên kết có thời hạn, cần dispatch lại nếu hết hạn trong hàng chờ. Chỉ artifact thư viện được tải lên; không tải mã riêng, tài nguyên game hay file sao lưu vào artifact.

## Offline 29

[Chi tiết bản 29 và phạm vi kiểm tra](OFFLINE29_TIEN_DO.md). Sửa cập nhật PC và khôi phục tài khoản; thêm shop Lôi đài có icon với 10 skin, bot cao nhất cấp 139, hiệu ứng ngọc và sự kiện Đứa Bé/đệ tử. `/velang` về làng, `/detu` tìm Đứa Bé và mở lựa chọn nhận.

Chuẩn bị server bằng `python scripts/stage_offline29.py --source build/server-offline28-extra --out build/server-offline29`. PC dùng `pc/RepairPatcher` với DLL bản 27. Tài nguyên bản 29 dùng `scripts/package_offline29_assets.py` trên gói tài nguyên bản 28 và thư mục `part_char/imgver` của client gốc; ngọc và tọa độ thú cưỡi được cập nhật khi cài gói.

iOS dùng `scripts/prepare_ios_server.py` để tạo thư mục nguồn từ server 29, rồi đẩy thư mục nguồn đó lên nhánh `offline29-build` của repo build riêng. Chạy `gh workflow run build.yml --repo zuzongdnt/hso-ios-offline-build --ref offline29-build -f runner=macos-26`; có thể chọn `runner=macos-15` nếu GitHub hết máy Mac 26. Tải artifact `ios-offline-world` rồi ghép IPA bằng `scripts/build_ios_ipa.py` với `--build 17 --dream-fashion`, IPA gốc và hai gói world/cosmetics riêng tư. IPA chưa ký; ký và cài đè bằng iLoader để giữ dữ liệu.

## Offline 28

Chi tiết sửa và các phần còn thiếu ở [OFFLINE28_TIEN_DO.md](OFFLINE28_TIEN_DO.md). Mrs Oda có shop skin bằng điểm; NPC bảng xếp hạng có danh sách bot, Top thi đấu và Về làng. Có thể chat `/velang`. PC mặc định không giới hạn FPS.

`scripts/stage_offline28.py --source build/server-offline27-release --out build/server-offline28` tạo mã server mới. Tài nguyên Hiệp sĩ Mộng Mơ được đóng gói bằng `scripts/package_offline28_assets.py`. PC dùng thêm `pc/RepairPatcher` trên DLL bản 27. iOS dùng nhánh `offline28-build` ở repo build riêng và IPA build 16.

## Offline 27

`scripts/stage_offline27.py` tạo mã server 27 từ mã server 23 đã chuẩn bị ở `build/server-offline23`. Bản này giữ người bán mề đay +6 đến +10; mề đay +15 chỉ ở Mở Ly. Android chờ server offline sẵn sàng trước khi nối game để tránh lỗi kết nối lúc mở. Chi tiết đã kiểm tra và việc còn lại ở [OFFLINE27_TIEN_DO.md](OFFLINE27_TIEN_DO.md).

iOS được build theo ba bước: `scripts/prepare_ios_server.py` ghép mã server vào dự án iOS; quy trình mẫu `ios/.github/workflows/build.yml` biên dịch thư viện `HSOOfflineWorld.dylib` arm64 bằng GraalVM trên macOS; `scripts/build_ios_ipa.py` ghép thư viện đó, dữ liệu thế giới và tài nguyên vào IPA gốc Tailscale v2 được cung cấp riêng. Thêm `--dream-fashion` để bật bản vá Hiệp sĩ Mộng Mơ. Bản 27 dùng nhánh `offline27-build` trong repo GitHub Actions riêng `zuzongdnt/hso-ios-offline-build`; chạy `gh workflow run build.yml --repo zuzongdnt/hso-ios-offline-build --ref offline27-build`. Workflow nằm trong thư mục `ios` chỉ là mẫu; nó không tự chạy từ gốc repo này. IPA bản 27 có bundle ID `com.zuzong.hso.offline403`, build số 15 và chưa ký; phải ký, cài đè bằng iLoader. Chưa kiểm tra gameplay trên iPhone thật.

## Thay đổi trong offline.16

- Dùng phần tóc gốc 52, 53, 54, 55, 66, 67, 69 cho bảy kiểu tóc nhập đầu tiên, giữ bảng vị trí và hướng nhìn gốc. Ngoại trang ở ô 11 che tóc riêng; tháo ngoại trang thì tóc riêng hiện lại và ẩn mũ trang bị.
- Bỏ các dải icon ba khung tự ghép từ dáng ngoài map. Icon balo trở lại ảnh tĩnh; các bộ ngoại trang vẫn có đầu đầy đủ khi mặc.
- Gỡ bốn món gán nhầm thành lồng đèn: mặt nạ nước, đầu sói lửa, kỳ lân đỏ, khúc xương. Gỡ hai bộ giáp bạc/đỏ tinh quang ghép thử chưa đúng bản gốc. ID cũ giữ làm mốc; các bản lưu bỏ sáu món này khi đăng nhập, gồm túi, rương và ô đang đeo. Sao lưu dữ liệu trước khi cập nhật.
- Cập nhật các dòng theo ảnh người dùng cung cấp cho Mặt nạ Loki, Mặt nạ thổ dân, Tia sét ma thuật, Tóc thời trang Du Hiệp và Lồng đèn Lân Rước Đèn. Đồ đang có được cập nhật khi tải nhân vật.
- Giữ các sửa chỉ số Cánh hồ ly, Chổi phép thuật và tóc Saiyan từ offline.15. Hai dòng Lời nguyền trên Chổi mới là thông tin chỉ số, chưa có xử lý kích hoạt. Chưa xác minh công thức giáp tím để khớp số trong ảnh +6; số khởi đầu hiện quay riêng 1–3% theo thông tin tạm từ người dùng.

Đã qua kiểm tra hồi quy Java và giao thức thực trên giả lập Android 10: giá trị đồ, gỡ món cũ, ưu tiên ngoại trang/tóc và icon tĩnh. Đã xem tóc bạc ở hướng trước/nghiêng trong map. Chưa kiểm tra điện thoại thật hoặc toàn bộ động tác chiến đấu của từng kiểu tóc.

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

Mặc định không xuất tài khoản, nhân vật của người chơi, clan, giftcode hoặc lịch sử thanh toán. Mẫu boss hệ thống `player.id=-1` được giữ vì server cần để khởi động. Nếu muốn giữ tài khoản/nhân vật của chính bạn để chơi, thêm `--include-private-save`; khi đó chỉ giữ file world/APK kết quả ở nơi riêng tư. Bản xuất không có tài khoản cần được bạn khởi tạo tài khoản theo schema của server trước khi đăng nhập; bản Java tự tạo tài khoản offline riêng. Công cụ không gửi dữ liệu lên Internet.

## Build Android từ APK v403b của bạn

Cần JDK, Android SDK Platform 36, Build Tools 36 trở lên, Apktool 3 và keystore của bạn. Ví dụ Windows, thay các đường dẫn bằng máy của bạn:

```powershell
$env:HSO_KEYSTORE_PASSWORD = 'mat-khau-keystore-cua-ban'
python scripts/build_android.py --apk inputs/Knight_Online_Android-v403b.apk --server build/server/target/HSO_Re_2-1.0-jar-with-dependencies.jar --source build/server --world build/world/offline-world.zip --apktool inputs/apktool.jar --sdk C:/Android/Sdk --jdk C:/Java/jdk-17 --keystore inputs/offline.jks --alias offline
```

APK kết quả nằm trong `build/android/HSO_Offline.apk`. Mỗi lần build chọn thư mục `--out` mới để giữ lại kết quả trước. Bản offline.16 có package `com.zuzong.hso.offline403`, versionCode `228` và yêu cầu tối thiểu Android 10 (API 29). Dùng cùng khóa ký để cài cập nhật và giữ dữ liệu.

## Kiểm tra

Xuất fixture template từ database của bạn, rồi truyền thư mục chạy có `data/` để kiểm tra:

```powershell
python scripts/export_fixtures.py --mysql inputs/mariadb.exe --defaults inputs/database-client.ini --database hso_offline --out inputs/fixtures.json
python scripts/test_server.py --jdk C:/Java/jdk-17 --jar build/server/target/HSO_Re_2-1.0-jar-with-dependencies.jar --fixtures inputs/fixtures.json --runtime inputs/runtime
```

Đã tái hiện lỗi đổi ngọc trên JAR cũ và chạy kiểm tra hồi quy trên JAR mới: giữ nguyên ngọc qua nâng thành công/thất bại, cả bốn mốc cấp, đủ 14 loại trứng, không tiêu hao khi yêu cầu sai hoặc đang ấp trứng khác. APK offline.2 đã thử qua giao thức thực trên máy giả lập Android 14 khi bật chế độ máy bay, tắt Wi-Fi: mua trứng Thỏ tại shop, gửi ấp trong Khu Vườn và nhận pet nở. Thời gian nở được rút ngắn bằng lệnh quản trị chỉ trong lượt kiểm tra. Chưa thử APK này trên điện thoại thật.

## Nguồn và giấy phép

Server nền: [ALKAstraverse/hso-server](https://github.com/ALKAstraverse/hso-server), commit được ghi trong `upstream.json`. Repo này phân phối bản vá để giữ rõ nguồn gốc của code nền, không chép client/tài nguyên game vào repo và không cấp lại giấy phép cho chúng. Các công cụ mới, bridge, bài kiểm tra và phần sửa do dự án này tạo được phát hành theo [MIT](LICENSE). Upstream hiện chưa khai báo giấy phép; điều đó không được thay đổi bởi giấy phép của công cụ trong repo này.
