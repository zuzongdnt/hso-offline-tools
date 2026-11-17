package offline;

import java.nio.file.Path;
import java.nio.file.Files;
import java.io.PrintWriter;
import java.io.StringWriter;
import org.graalvm.nativeimage.IsolateThread;
import org.graalvm.nativeimage.c.function.CEntryPoint;
import org.graalvm.nativeimage.c.type.CCharPointer;
import org.graalvm.nativeimage.c.type.CTypeConversion;

public final class NativeWorld {
    private static volatile String error = "";

    @CEntryPoint(name = "hso_world_start")
    public static int start(IsolateThread thread, CCharPointer saveRoot, CCharPointer resources) {
        try {
            IosWorld.start(Path.of(CTypeConversion.toJavaString(saveRoot)),
                    Path.of(CTypeConversion.toJavaString(resources)));
            return 0;
        } catch (Throwable failure) {
            error = describe(failure);
            try {
                StringWriter report = new StringWriter();
                failure.printStackTrace(new PrintWriter(report));
                Files.writeString(Path.of(CTypeConversion.toJavaString(saveRoot), "offline-startup-error.txt"), report.toString());
            } catch (Exception writeError) {
                failure.addSuppressed(writeError);
            }
            failure.printStackTrace();
            return -1;
        }
    }

    @CEntryPoint(name = "hso_world_save")
    public static int save(IsolateThread thread) {
        try {
            IosWorld.save();
            return 0;
        } catch (Throwable failure) {
            error = describe(failure);
            failure.printStackTrace();
            return -1;
        }
    }

    private static String describe(Throwable failure) {
        StringBuilder message = new StringBuilder();
        Throwable current = failure;
        for (int depth = 0; current != null && depth < 8; depth++) {
            if (depth > 0) message.append("\n");
            message.append(current);
            if (current.getCause() == current) break;
            current = current.getCause();
        }
        return message.toString();
    }

    @CEntryPoint(name = "hso_world_error")
    public static int copyError(IsolateThread thread, CCharPointer buffer, int capacity) {
        byte[] text = error.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        int count = Math.min(text.length, Math.max(0, capacity - 1));
        for (int index = 0; index < count; index++) buffer.write(index, text[index]);
        if (capacity > 0) buffer.write(count, (byte) 0);
        return count;
    }

    public static void main(String[] args) throws Exception {
        IosWorld.main(args);
    }
}
