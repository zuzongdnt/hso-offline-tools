"""Use the same bounded map workers on PC, Android and iOS."""
def patch(text):
    if 'this.mapthread = offline.MapScheduler.schedule(this, delay);' in text:return text
    text=text.replace('private final Thread mapthread;', 'private java.util.concurrent.ScheduledFuture<?> mapthread;\n    private long nextWorldUpdate;')
    text=text.replace('private boolean running;', 'private volatile boolean running;')
    text=text.replace('this.mapthread = new Thread(this);','this.mapthread = null;')
    begin=text.index('    @Override\n    public void run() {')
    end=text.index('    private synchronized void update_nhanban()',begin)
    body_begin=text.index('\t\t\t\tif (time1 >= nextWorldUpdate)',begin)
    body_end=text.index('\t\t\t\ttime2 = System.currentTimeMillis();',body_begin)
    body=text[body_begin:body_end]
    replacement='''    @Override
    public void run() {
        if (!this.running) return;
        long time1 = System.currentTimeMillis();
        try {
'''+body+'''        } catch (Exception error) {
            System.err.println("Map tick failed: " + map_id + "/" + zone_id);
            error.printStackTrace();
        } finally {
            synchronized (this) {
                if (this.running) {
                    long period = this.ld == null ? 1000L : LoiDai.UPDATE_MILLIS;
                    long delay = period - (System.currentTimeMillis() - time1);
                    this.mapthread = offline.MapScheduler.schedule(this, delay);
                }
            }
        }
    }

'''
    text=text[:begin]+replacement+text[end:]
    old='''    public void start_map() {
        this.mapthread.start();
    }

    public void stop_map() {
        this.running = false;
        this.mapthread.interrupt();
    }'''
    new='''    public synchronized void start_map() {
        if (this.running) return;
        this.running = true;
        this.mapthread = offline.MapScheduler.schedule(this, 0);
    }

    public synchronized void stop_map() {
        this.running = false;
        if (this.mapthread != null) this.mapthread.cancel(false);
    }'''
    if text.count(old)!=1:raise ValueError('Unexpected map lifecycle')
    return text.replace(old,new)
