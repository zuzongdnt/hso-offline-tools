import json
import plistlib
import shutil
import socket
import subprocess
import time
from pathlib import Path


def run(*args):
    return subprocess.check_output(args, text=True).strip()


root = Path.cwd()
app = root / "probe/HSOProbe.app"
(app / "Frameworks").mkdir(parents=True)
library = next((root / "target/gluonfx/x86_64-ios").glob("*.dylib"))
embedded = app / "Frameworks/HSOOfflineWorld.dylib"
shutil.copy2(library, embedded)
shutil.copytree(root / "fixture", app / "offline")
run("install_name_tool", "-id", "@executable_path/Frameworks/HSOOfflineWorld.dylib", str(embedded))
source = app.parent / "main.m"
source.write_text("""
#import <UIKit/UIKit.h>
@interface HSOProbeDelegate : UIResponder <UIApplicationDelegate>
@property (strong, nonatomic) UIWindow *window;
@end
@implementation HSOProbeDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options {
    self.window = [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
    self.window.rootViewController = [UIViewController new];
    self.window.rootViewController.view.backgroundColor = UIColor.whiteColor;
    [self.window makeKeyAndVisible];
    return YES;
}
@end
int main(int argc, char **argv) {
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, NSStringFromClass(HSOProbeDelegate.class));
    }
}
""")
sdk = run("xcrun", "--sdk", "iphonesimulator", "--show-sdk-path")
run("xcrun", "--sdk", "iphonesimulator", "clang", "-arch", "x86_64",
    "-isysroot", sdk, "-mios-simulator-version-min=15.0", "-fobjc-arc",
    "-framework", "Foundation", "-framework", "UIKit", str(source),
    "-Wl,-u,_hso_world_start", str(embedded), "-o", str(app / "HSOProbe"))
with (app / "Info.plist").open("wb") as output:
    plistlib.dump({
        "CFBundleIdentifier": "com.zuzong.hso.probe",
        "CFBundleExecutable": "HSOProbe",
        "CFBundleName": "HSOProbe",
        "CFBundlePackageType": "APPL",
        "CFBundleVersion": "1",
        "CFBundleShortVersionString": "1",
        "MinimumOSVersion": "15.0",
        "LSRequiresIPhoneOS": True,
        "UIDeviceFamily": [1, 2],
        "UILaunchScreen": {},
    }, output)
run("codesign", "--force", "--sign", "-", str(embedded))
run("codesign", "--force", "--sign", "-", str(app))
available = json.loads(run("xcrun", "simctl", "list", "devices", "available", "--json"))
devices = [device for runtime, entries in available["devices"].items() if "iOS" in runtime
           for device in entries if device["name"].startswith("iPhone")]
if not devices:
    raise RuntimeError("No available iPhone simulator")
device = devices[0]["udid"]
if devices[0]["state"] != "Booted":
    run("xcrun", "simctl", "boot", device)
run("xcrun", "simctl", "bootstatus", device, "-b")
run("xcrun", "simctl", "install", device, str(app))
run("xcrun", "simctl", "launch", device, "com.zuzong.hso.probe")
container = Path(run("xcrun", "simctl", "get_app_container", device, "com.zuzong.hso.probe", "data"))
report = container / "Library/Application Support/HSOOffline/world/offline-startup-error.txt"
deadline = time.monotonic() + 150
while time.monotonic() < deadline:
    if report.exists():
        text = report.read_text()
        (root / "simulator-startup.log").write_text(text)
        raise RuntimeError(text)
    try:
        with socket.create_connection(("127.0.0.1", 19139), timeout=1) as client:
            client.settimeout(3)
            client.sendall(bytes((216, 0, 0)))
            reply = client.recv(128)
            if not reply or reply[0] != 216:
                raise RuntimeError("Invalid HSO simulator handshake")
            message = "iOS simulator started the embedded world and completed the HSO handshake"
            (root / "simulator-startup.log").write_text(message)
            print(message)
            break
    except OSError:
        time.sleep(0.5)
else:
    raise TimeoutError("iOS simulator world startup timed out")
run("xcrun", "simctl", "terminate", device, "com.zuzong.hso.probe")
