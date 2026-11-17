#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <WebKit/WebKit.h>
#include <stdio.h>
#include <unistd.h>
typedef struct graal_isolate graal_isolate_t;
typedef struct graal_isolatethread graal_isolatethread_t;
extern int graal_create_isolate(void *, graal_isolate_t **, graal_isolatethread_t **);
extern int graal_attach_thread(graal_isolate_t *, graal_isolatethread_t **);
extern int graal_detach_thread(graal_isolatethread_t *);

extern int hso_world_start(graal_isolatethread_t *, const char *, const char *);
extern int hso_world_save(graal_isolatethread_t *);
extern int hso_world_error(graal_isolatethread_t *, char *, int);

static dispatch_queue_t worldQueue;
static graal_isolate_t *worldIsolate;
static NSString *startupError;
static BOOL worldReady;
static UIView *loadingView;
static UIButton *toolsButton;

@interface HSOToolsController : UIViewController <WKNavigationDelegate, WKUIDelegate>
@end

@implementation HSOToolsController
- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"Dữ liệu HSO Offline";
    self.navigationItem.leftBarButtonItem = [[[UIBarButtonItem alloc]
        initWithTitle:@"Quay lại game" style:UIBarButtonItemStylePlain target:self action:@selector(closeTools)] autorelease];
    WKWebView *web = [[[WKWebView alloc] initWithFrame:self.view.bounds] autorelease];
    web.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    web.navigationDelegate = self;
    web.UIDelegate = self;
    [self.view addSubview:web];
    [web loadRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:@"http://127.0.0.1:19140/"]]];
}
- (void)closeTools { [self dismissViewControllerAnimated:YES completion:nil]; }
- (void)showMessage:(NSString *)text {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"HSO Offline" message:text preferredStyle:UIAlertControllerStyleAlert];
    [alert addAction:[UIAlertAction actionWithTitle:@"Đóng" style:UIAlertActionStyleDefault handler:nil]];
    [self presentViewController:alert animated:YES completion:nil];
}
- (void)download:(NSURL *)url ipa:(BOOL)ipa {
    UIAlertController *progress = [UIAlertController alertControllerWithTitle:@"Đang tải file…"
        message:ipa ? @"Giữ game mở cho đến khi tải xong IPA." : @"Đang xuất dữ liệu nhân vật."
        preferredStyle:UIAlertControllerStyleAlert];
    [self presentViewController:progress animated:YES completion:nil];
    NSURLSessionDownloadTask *task = [NSURLSession.sharedSession downloadTaskWithURL:url
        completionHandler:^(NSURL *temporary, NSURLResponse *response, NSError *failure) {
            NSString *filename = [NSString stringWithFormat:@"HSO-%lld.%@",
                (long long)(NSDate.date.timeIntervalSince1970 * 1000), ipa ? @"ipa" : @"hsosave"];
            NSURL *destination = [NSURL fileURLWithPath:[[NSHomeDirectory() stringByAppendingPathComponent:@"Documents"] stringByAppendingPathComponent:filename]];
            NSError *error = failure;
            if (!error && [(NSHTTPURLResponse *)response statusCode] != 200)
                error = [NSError errorWithDomain:@"HSO" code:1 userInfo:@{NSLocalizedDescriptionKey:@"Máy chủ chưa gửi được file."}];
            if (!error) [NSFileManager.defaultManager copyItemAtURL:temporary toURL:destination error:&error];
            dispatch_async(dispatch_get_main_queue(), ^{
                [progress dismissViewControllerAnimated:YES completion:^{
                    if (error) { [self showMessage:error.localizedDescription]; return; }
                    UIActivityViewController *share = [[[UIActivityViewController alloc] initWithActivityItems:@[destination] applicationActivities:nil] autorelease];
                    share.popoverPresentationController.sourceView = self.view;
                    share.popoverPresentationController.sourceRect = CGRectMake(self.view.bounds.size.width / 2, 40, 1, 1);
                    [self presentViewController:share animated:YES completion:nil];
                }];
            });
        }];
    [task resume];
}
- (void)webView:(WKWebView *)web decidePolicyForNavigationAction:(WKNavigationAction *)action
        decisionHandler:(void (^)(WKNavigationActionPolicy))decision {
    NSURL *url = action.request.URL;
    BOOL local = [url.host isEqualToString:@"127.0.0.1"] && url.port.intValue == 19140;
    if (local && [url.path isEqualToString:@"/export"]) {
        decision(WKNavigationActionPolicyCancel);
        [self download:url ipa:NO];
    } else if ([url.absoluteString isEqualToString:@"https://www.tiktok.com/@thinhdzuong"]
            || [url.absoluteString isEqualToString:@"mailto:zuzong68@gmail.com"]) {
        decision(WKNavigationActionPolicyCancel);
        [UIApplication.sharedApplication openURL:url options:@{} completionHandler:^(BOOL success) {
            if (!success) [self showMessage:@"Chưa có ứng dụng để mở liên kết."];
        }];
    } else if ([url.absoluteString hasPrefix:@"https://github.com/zuzongdnt/hso-offline-tools/releases/download/"]
            && [url.pathExtension isEqualToString:@"ipa"]) {
        decision(WKNavigationActionPolicyCancel);
        [self download:url ipa:YES];
    } else {
        decision(local || [url.absoluteString isEqualToString:@"about:blank"]
            ? WKNavigationActionPolicyAllow : WKNavigationActionPolicyCancel);
    }
}
- (void)webView:(WKWebView *)web runJavaScriptConfirmPanelWithMessage:(NSString *)message
        initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(BOOL))completion {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"Khôi phục dữ liệu"
        message:message preferredStyle:UIAlertControllerStyleAlert];
    [alert addAction:[UIAlertAction actionWithTitle:@"Hủy" style:UIAlertActionStyleCancel handler:^(UIAlertAction *action) { completion(NO); }]];
    [alert addAction:[UIAlertAction actionWithTitle:@"Khôi phục" style:UIAlertActionStyleDefault handler:^(UIAlertAction *action) { completion(YES); }]];
    [self presentViewController:alert animated:YES completion:nil];
}
+ (void)openTools {
    UIWindow *window = nil;
    for (UIWindow *candidate in UIApplication.sharedApplication.windows) if (candidate.isKeyWindow) { window = candidate; break; }
    UIViewController *controller = window.rootViewController;
    while (controller.presentedViewController) controller = controller.presentedViewController;
    if (!controller || [controller isKindOfClass:[HSOToolsController class]]) return;
    HSOToolsController *tools = [[[HSOToolsController alloc] init] autorelease];
    UINavigationController *navigation = [[[UINavigationController alloc] initWithRootViewController:tools] autorelease];
    [controller presentViewController:navigation animated:YES completion:nil];
}
@end

static void prepareDiagnosticLog(void) {
    NSString *documents = [NSHomeDirectory() stringByAppendingPathComponent:@"Documents"];
    NSError *error = nil;
    if (![NSFileManager.defaultManager createDirectoryAtPath:documents
            withIntermediateDirectories:YES attributes:nil error:&error]) return;
    NSString *filename = [NSString stringWithFormat:@"HSOOffline-%lld-%d.log",
        (long long)(NSDate.date.timeIntervalSince1970 * 1000), getpid()];
    NSString *path = [documents stringByAppendingPathComponent:filename];
    FILE *log = fopen(path.UTF8String, "a");
    if (!log) return;
    fflush(stdout);
    fflush(stderr);
    dup2(fileno(log), STDOUT_FILENO);
    dup2(fileno(log), STDERR_FILENO);
    fclose(log);
    setvbuf(stdout, NULL, _IOLBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    fprintf(stderr, "[HSO] build=17 offline=29 pid=%d os=%s\n", getpid(), NSProcessInfo.processInfo.operatingSystemVersionString.UTF8String);
}

static UIWindow *gameWindow(void) {
    for (UIWindow *window in UIApplication.sharedApplication.windows) {
        if (window.isKeyWindow) return window;
    }
    return UIApplication.sharedApplication.windows.firstObject;
}

static void showState(void) {
    UIWindow *window = gameWindow();
    if (!window) return;
    if (worldReady && !toolsButton) {
        toolsButton = [UIButton buttonWithType:UIButtonTypeSystem];
        toolsButton.backgroundColor = [UIColor colorWithRed:0.35 green:0.22 blue:0.12 alpha:0.9];
        toolsButton.layer.cornerRadius = 8;
        [toolsButton setTitle:@"Dữ liệu" forState:UIControlStateNormal];
        [toolsButton setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
        [toolsButton addTarget:[HSOToolsController class] action:@selector(openTools) forControlEvents:UIControlEventTouchUpInside];
        toolsButton.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin | UIViewAutoresizingFlexibleBottomMargin;
        toolsButton.frame = CGRectMake(window.bounds.size.width - window.safeAreaInsets.right - 92,
            window.safeAreaInsets.top + 4, 84, 32);
        [window addSubview:toolsButton];
    }
    [loadingView removeFromSuperview];
    [loadingView release];
    loadingView = nil;
    if (!worldReady && !startupError) {
        loadingView = [[UIView alloc] initWithFrame:window.bounds];
        loadingView.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
        loadingView.backgroundColor = [UIColor colorWithWhite:0 alpha:0.8];
        UILabel *label = [[UILabel alloc] initWithFrame:loadingView.bounds];
        label.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
        label.text = @"Đang mở thế giới offline…";
        label.textAlignment = NSTextAlignmentCenter;
        label.textColor = UIColor.whiteColor;
        [loadingView addSubview:label];
        [label release];
        [window addSubview:loadingView];
    }
    if (startupError) {
        UIViewController *controller = window.rootViewController;
        while (controller.presentedViewController) controller = controller.presentedViewController;
        UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"HSO Offline"
            message:startupError preferredStyle:UIAlertControllerStyleAlert];
        [alert addAction:[UIAlertAction actionWithTitle:@"Đóng" style:UIAlertActionStyleDefault handler:nil]];
        [controller presentViewController:alert animated:YES completion:nil];
    }
}

static void saveWorld(void) {
    if (!worldReady) return;
    __block UIBackgroundTaskIdentifier task = UIBackgroundTaskInvalid;
    task = [UIApplication.sharedApplication beginBackgroundTaskWithExpirationHandler:^{
            if (task != UIBackgroundTaskInvalid) {
                [UIApplication.sharedApplication endBackgroundTask:task];
                task = UIBackgroundTaskInvalid;
            }
        }];
    dispatch_async(worldQueue, ^{
        // worldQueue may use a different OS thread for each block.
        graal_isolatethread_t *thread = NULL;
        int status = graal_attach_thread(worldIsolate, &thread);
        if (status == 0) {
            hso_world_save(thread);
            graal_detach_thread(thread);
        }
        dispatch_async(dispatch_get_main_queue(), ^{
            if (task != UIBackgroundTaskInvalid) {
                [UIApplication.sharedApplication endBackgroundTask:task];
                task = UIBackgroundTaskInvalid;
            }
        });
    });
}

__attribute__((constructor))
static void startOfflineWorld(void) {
    @autoreleasepool {
        prepareDiagnosticLog();
        worldQueue = dispatch_queue_create("com.zuzong.hso.world", DISPATCH_QUEUE_SERIAL);
        NSNotificationCenter *notifications = NSNotificationCenter.defaultCenter;
        [notifications addObserverForName:UIApplicationDidBecomeActiveNotification object:nil
            queue:NSOperationQueue.mainQueue usingBlock:^(NSNotification *note) { showState(); }];
        [notifications addObserverForName:UIApplicationDidEnterBackgroundNotification object:nil
            queue:NSOperationQueue.mainQueue usingBlock:^(NSNotification *note) { saveWorld(); }];
        [notifications addObserverForName:UIApplicationWillTerminateNotification object:nil
            queue:NSOperationQueue.mainQueue usingBlock:^(NSNotification *note) { saveWorld(); }];
        dispatch_async(worldQueue, ^{
            @autoreleasepool {
                NSString *root = [NSHomeDirectory() stringByAppendingPathComponent:@"Library/Application Support/HSOOffline/world"];
                NSString *resources = [NSBundle.mainBundle.bundlePath stringByAppendingPathComponent:@"offline"];
                graal_isolatethread_t *thread = NULL;
                fprintf(stderr, "[HSO] creating server isolate\n");
                int status = graal_create_isolate(NULL, &worldIsolate, &thread);
                NSString *failure = nil;
                if (status == 0) {
                    fprintf(stderr, "[HSO] starting embedded world\n");
                    status = hso_world_start(thread, root.UTF8String, resources.UTF8String);
                    fprintf(stderr, "[HSO] embedded world start status=%d\n", status);
                    if (status != 0) {
                        char message[2048] = {0};
                        hso_world_error(thread, message, sizeof(message));
                        failure = [NSString stringWithUTF8String:message];
                    }
                    graal_detach_thread(thread);
                } else {
                    failure = [NSString stringWithFormat:@"Không khởi động được máy chủ (%d).", status];
                }
                dispatch_async(dispatch_get_main_queue(), ^{
                    worldReady = status == 0;
                    startupError = [failure copy];
                    fprintf(stderr, "[HSO] client startup screen released ready=%d\n", worldReady);
                    showState();
                });
            }
        });
    }
}
