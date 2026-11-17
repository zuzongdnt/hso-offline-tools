package offline;

import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** Shared map workers: the embedded client GC also sees server native threads. */
public final class MapScheduler {
    private static final AtomicInteger SEQUENCE = new AtomicInteger();
    private static final ScheduledThreadPoolExecutor WORKERS = createWorkers();

    private static ScheduledThreadPoolExecutor createWorkers() {
        ThreadFactory factory = task -> {
            Thread thread = new Thread(task, "HSO-Map-" + SEQUENCE.incrementAndGet());
            thread.setDaemon(true);
            return thread;
        };
        ScheduledThreadPoolExecutor executor = new ScheduledThreadPoolExecutor(4, factory);
        executor.setRemoveOnCancelPolicy(true);
        return executor;
    }

    public static ScheduledFuture<?> schedule(Runnable map, long delayMillis) {
        return WORKERS.schedule(map, Math.max(1L, delayMillis), TimeUnit.MILLISECONDS);
    }

    public static int workerCount() {
        return WORKERS.getPoolSize();
    }
}
