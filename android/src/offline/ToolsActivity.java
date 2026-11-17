package offline;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.LinearLayout;
import android.widget.Button;
import java.io.File;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public final class ToolsActivity extends Activity {
    private ValueCallback<Uri[]> chooser;
    private String exportUrl;
    private File installer;
    private WebView web;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        Button close = new Button(this);
        close.setText("Quay lại game");
        close.setOnClickListener(view -> finish());
        layout.addView(close);
        web = new WebView(this);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(true);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return navigate(request.getUrl());
            }
        });
        web.setDownloadListener((url, agent, disposition, type, length) -> navigate(Uri.parse(url)));
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (chooser != null) chooser.onReceiveValue(null);
                chooser = callback;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);
                startActivityForResult(intent, 41);
                return true;
            }
            @Override public boolean onJsConfirm(WebView view, String url, String text, android.webkit.JsResult result) {
                new AlertDialog.Builder(ToolsActivity.this).setMessage(text)
                    .setPositiveButton("Khôi phục", (dialog, which) -> result.confirm())
                    .setNegativeButton("Hủy", (dialog, which) -> result.cancel())
                    .setOnCancelListener(dialog -> result.cancel()).show();
                return true;
            }
        });
        layout.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(layout);
        web.loadUrl("http://127.0.0.1:19140/");
    }

    private boolean navigate(Uri uri) {
        if ("http".equals(uri.getScheme()) && "127.0.0.1".equals(uri.getHost()) && uri.getPort() == 19140) {
            if ("/export".equals(uri.getPath())) {
                exportUrl = uri.toString();
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/octet-stream")
                        .addCategory(Intent.CATEGORY_OPENABLE)
                        .putExtra(Intent.EXTRA_TITLE, "HSO-" + System.currentTimeMillis() + ".hsosave");
                startActivityForResult(intent, 42);
                return true;
            }
            return false;
        }
        String text = uri.toString();
        if (text.equals("https://www.tiktok.com/@thinhdzuong") || text.equals("mailto:zuzong68@gmail.com")) {
            try {
                startActivity(new Intent("mailto".equals(uri.getScheme()) ? Intent.ACTION_SENDTO : Intent.ACTION_VIEW, uri));
            } catch (android.content.ActivityNotFoundException error) {
                message("Chưa có ứng dụng để mở liên kết.");
            }
        } else if (text.startsWith("https://github.com/zuzongdnt/hso-offline-tools/releases/download/") && text.endsWith(".apk")) {
            downloadUpdate(text);
        }
        return true;
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == 41 && chooser != null) {
            chooser.onReceiveValue(result == RESULT_OK && data != null && data.getData() != null ? new Uri[]{data.getData()} : null);
            chooser = null;
        }
        if (request == 42 && result == RESULT_OK && data != null && data.getData() != null) {
            Uri target = data.getData();
            transfer(exportUrl, () -> getContentResolver().openOutputStream(target), () -> message("Đã xuất file sao lưu."));
        }
        if (request == 43 && getPackageManager().canRequestPackageInstalls()) install();
    }

    private void downloadUpdate(String url) {
        File update = new File(getCacheDir(), "update.apk");
        transfer(url, () -> new java.io.FileOutputStream(update), () -> {
            installer = update;
            if (getPackageManager().canRequestPackageInstalls()) install();
            else startActivityForResult(new Intent(android.provider.Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + getPackageName())), 43);
        });
    }

    private void install() {
        if (installer == null) return;
        Uri content = Uri.parse("content://" + getPackageName() + ".updates/update.apk");
        startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(content, "application/vnd.android.package-archive")
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION));
    }

    private interface Destination { OutputStream open() throws Exception; }
    private void transfer(String url, Destination target, Runnable success) {
        AlertDialog progress = new AlertDialog.Builder(this).setMessage("Đang tải file…").setCancelable(false).show();
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setConnectTimeout(15000);
                connection.setReadTimeout(30000);
                if (connection.getResponseCode() != 200) throw new java.io.IOException("Máy chủ chưa gửi được file.");
                try (InputStream input = connection.getInputStream(); OutputStream output = target.open()) {
                    if (output == null) throw new java.io.IOException("Không mở được nơi lưu file.");
                    byte[] buffer = new byte[65536];
                    int size;
                    while ((size = input.read(buffer)) != -1) output.write(buffer, 0, size);
                }
                runOnUiThread(() -> { progress.dismiss(); success.run(); });
            } catch (Exception error) {
                runOnUiThread(() -> { progress.dismiss(); message("Chưa tải được file. " + error.getMessage()); });
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "HSO-File-Transfer").start();
    }

    private void message(String text) {
        if (!isFinishing()) new AlertDialog.Builder(this).setMessage(text).setPositiveButton("Đóng", null).show();
    }
    @Override protected void onDestroy() {
        if (chooser != null) chooser.onReceiveValue(null);
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
