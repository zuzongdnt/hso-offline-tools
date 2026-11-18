package offline;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.os.Handler;
import android.os.Looper;
import java.io.*;
import java.net.Socket;
import java.util.concurrent.*;
import java.util.zip.*;

public final class OfflineEngine {
    private static boolean started;
    private static Activity gameActivity;
    private static final java.util.concurrent.CountDownLatch serverReady = new java.util.concurrent.CountDownLatch(1);
    private static volatile Throwable startupError;
    private static final Handler ui=new Handler(Looper.getMainLooper());
    public static void lockLandscape(Activity activity) {
        int orientation = activity.getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE
                ? ActivityInfo.SCREEN_ORIENTATION_LOCKED : ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE;
        if (activity.getRequestedOrientation() != orientation) {
            activity.setRequestedOrientation(orientation);
        }
    }
    public static synchronized void start(final Activity activity){
        gameActivity = activity;
        if(started)return;started=true;
        final File root=new File(activity.getFilesDir(),"offline-world");
        final AlertDialog[] progress={null};
        ui.post(()->{if(!activity.isFinishing())progress[0]=new AlertDialog.Builder(activity).setTitle("HSO Offline").setMessage("Đang chuẩn bị game, vui lòng chờ...").setCancelable(false).show();});
        new Thread(()->{
            try{
                File complete=new File(root,".ready-v1");
                if(!complete.isFile()){
                    root.mkdirs();
                    try(ZipInputStream zip=new ZipInputStream(activity.getAssets().open("offline-world.zip"))){
                        ZipEntry entry;byte[] buffer=new byte[65536];
                        while((entry=zip.getNextEntry())!=null){
                            File target=new File(root,entry.getName());
                            if(!target.getCanonicalPath().startsWith(root.getCanonicalPath()+File.separator))throw new IOException("Invalid asset path");
                            if(entry.isDirectory()){target.mkdirs();continue;}
                            target.getParentFile().mkdirs();
                            try(FileOutputStream output=new FileOutputStream(target)){
                                int n;while((n=zip.read(buffer))!=-1)output.write(buffer,0,n);
                            }
                        }
                    }
                    complete.createNewFile();
                }
                installCosmetics(activity, root);
                System.setProperty("hso.root",root.getAbsolutePath());
                if (java.util.Arrays.asList(activity.getAssets().list("")).contains("offline-lite"))
                    System.setProperty("hso.assets.max2", "true");
                final java.util.concurrent.atomic.AtomicReference<Throwable> serverError=new java.util.concurrent.atomic.AtomicReference<>();
                new Thread(()->{try{core.Start.main(new String[0]);}catch(Throwable e){serverError.set(e);android.util.Log.e("HSOOffline","Server failed",e);}},"HSO-Offline-Server").start();
                boolean ready=false;
                for(int i=0;i<180;i++){
                    if(serverError.get()!=null)throw new IOException("Không mở được thế giới: "+serverError.get().toString());
                    try(Socket socket=new Socket("127.0.0.1",19139)){ready=true;break;}
                    catch(IOException e){Thread.sleep(500);}
                }
                if(!ready)throw new IOException("Không khởi động được thế giới Offline.");
                serverReady.countDown();
                Executors.newSingleThreadScheduledExecutor().scheduleWithFixedDelay(()->{
                    try{core.SaveData.process();}catch(Exception e){android.util.Log.e("HSOOffline","Autosave",e);}
                },30,30,TimeUnit.SECONDS);
                ui.post(()->{if(progress[0]!=null)progress[0].dismiss();});
            }catch(final Throwable error){
                startupError = error;
                serverReady.countDown();
                android.util.Log.e("HSOOffline","Startup failed",error);
                ui.post(()->{
                    if(progress[0]!=null)progress[0].dismiss();
                    if(!activity.isFinishing())new AlertDialog.Builder(activity).setTitle("HSO Offline").setMessage("Chưa mở được game: "+error.getMessage()).setPositiveButton("Đóng",(d,w)->activity.finish()).show();
                });
            }
        },"HSO-Offline-Prepare").start();
    }
    public static void awaitServerReady() throws IOException, InterruptedException {
        if (!serverReady.await(95, TimeUnit.SECONDS)) throw new IOException("Máy chủ Offline khởi động quá lâu.");
        if (startupError != null) throw new IOException("Máy chủ Offline không khởi động được.", startupError);
    }
    private static void installCosmetics(Activity activity, File root) throws IOException {
        File marker = new File(root, ".cosmetics-v30");
        if (marker.isFile()) return;
        boolean present = java.util.Arrays.asList(activity.getAssets().list("")).contains("offline-cosmetics.zip");
        if (!present) return;
        try (ZipInputStream zip = new ZipInputStream(activity.getAssets().open("offline-cosmetics.zip"))) {
            String dataRoot = new File(root, "data").getCanonicalPath() + File.separator;
            ZipEntry entry;
            byte[] buffer = new byte[65536];
            while ((entry = zip.getNextEntry()) != null) {
                File target = new File(root, entry.getName());
                if (!target.getCanonicalPath().startsWith(dataRoot)) throw new IOException("Invalid cosmetic asset path");
                if (entry.isDirectory()) continue;
                target.getParentFile().mkdirs();
                try (FileOutputStream output = new FileOutputStream(target)) {
                    int count;
                    while ((count = zip.read(buffer)) != -1) output.write(buffer, 0, count);
                }
            }
        }
        marker.createNewFile();
    }

    public static void save(){
        if(!started)return;
        new Thread(()->{try{if(core.SQL.is_connected)core.SaveData.process();}catch(Throwable e){android.util.Log.e("HSOOffline","Pause save",e);}},"HSO-Offline-Save").start();
    }
    public static void openTools() {
        Activity activity = gameActivity;
        if (activity != null) activity.startActivity(new android.content.Intent(activity, ToolsActivity.class));
    }
}
