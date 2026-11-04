package offline;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Handler;
import android.os.Looper;
import java.io.*;
import java.net.Socket;
import java.util.concurrent.*;
import java.util.zip.*;

public final class OfflineEngine {
    private static boolean started;
    private static final Handler ui=new Handler(Looper.getMainLooper());
    public static synchronized void start(final Activity activity){
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
                System.setProperty("hso.root",root.getAbsolutePath());
                final java.util.concurrent.atomic.AtomicReference<Throwable> serverError=new java.util.concurrent.atomic.AtomicReference<>();
                new Thread(()->{try{core.Start.main(new String[0]);}catch(Throwable e){serverError.set(e);android.util.Log.e("HSOOffline","Server failed",e);}},"HSO-Offline-Server").start();
                boolean ready=false;
                for(int i=0;i<180;i++){
                    if(serverError.get()!=null)throw new IOException("Không mở được thế giới: "+serverError.get().toString());
                    try(Socket socket=new Socket("127.0.0.1",19139)){ready=true;break;}
                    catch(IOException e){Thread.sleep(500);}
                }
                if(!ready)throw new IOException("Không khởi động được thế giới Offline.");
                Executors.newSingleThreadScheduledExecutor().scheduleWithFixedDelay(()->{
                    try{core.SaveData.process();}catch(Exception e){android.util.Log.e("HSOOffline","Autosave",e);}
                },30,30,TimeUnit.SECONDS);
                ui.post(()->{if(progress[0]!=null)progress[0].dismiss();});
            }catch(final Throwable error){
                android.util.Log.e("HSOOffline","Startup failed",error);
                ui.post(()->{
                    if(progress[0]!=null)progress[0].dismiss();
                    if(!activity.isFinishing())new AlertDialog.Builder(activity).setTitle("HSO Offline").setMessage("Chưa mở được game: "+error.getMessage()).setPositiveButton("Đóng",(d,w)->activity.finish()).show();
                });
            }
        },"HSO-Offline-Prepare").start();
    }
    public static void save(){
        if(!started)return;
        new Thread(()->{try{if(core.SQL.is_connected)core.SaveData.process();}catch(Throwable e){android.util.Log.e("HSOOffline","Pause save",e);}},"HSO-Offline-Save").start();
    }
}
