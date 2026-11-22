import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import org.objectweb.asm.*;

/** Patch only the user's original online client; no decompiled client is distributed. */
public final class PatchJ2me implements Opcodes {
    static int changes;
    static final String BOOT = "zuzong/j2me/Bootstrap";
    static byte[] patch(String file, byte[] bytes) {
        ClassWriter writer = new ClassWriter(ClassWriter.COMPUTE_MAXS);
        new ClassReader(bytes).accept(new ClassVisitor(ASM9, writer) {
            public MethodVisitor visitMethod(int access, String name, String desc, String sig, String[] exceptions) {
                MethodVisitor mv = super.visitMethod(access, name, desc, sig, exceptions);
                if (file.equals("com/silverknight/TemMidlet.class") && name.equals("connectHTTP")) {
                    mv.visitCode(); mv.visitLdcInsn("Offline:127.0.0.1:19149:0"); mv.visitInsn(ARETURN);
                    mv.visitMaxs(1, 1); mv.visitEnd(); changes++; return null;
                }
                if (file.equals("CLib/mSocket.class") && name.equals("<init>")) {
                    changes++;
                    return new MethodVisitor(ASM9, mv) {
                        public void visitCode() {
                            super.visitCode();
                            super.visitMethodInsn(INVOKESTATIC, BOOT, "awaitReady", "()V", false);
                            super.visitLdcInsn("127.0.0.1"); super.visitVarInsn(ASTORE, 1);
                            super.visitLdcInsn(19149); super.visitVarInsn(ISTORE, 2);
                        }
                    };
                }
                boolean midlet = file.equals("com/silverknight/TemMidlet.class");
                boolean login = file.equals("GameScreen/LoginScreen.class") && name.equals("<init>");
                if (midlet && (name.equals("pauseApp") || name.equals("destroyApp"))) {
                    changes++;
                    return new MethodVisitor(ASM9, mv) { public void visitCode() {
                        super.visitCode(); super.visitMethodInsn(INVOKESTATIC, BOOT, "save", "()V", false);
                    }};
                }
                if ((midlet && name.equals("<init>")) || login) {
                    changes++;
                    return new MethodVisitor(ASM9, mv) { public void visitInsn(int op) {
                        if (op == RETURN) {
                            if (login) {
                                for (String[] field : new String[][]{{"tfusername","javaoff"},{"tfpassword","offline"}}) {
                                    super.visitFieldInsn(GETSTATIC,"GameScreen/LoginScreen",field[0],"LCLib/TField;");
                                    super.visitLdcInsn(field[1]);
                                    super.visitMethodInsn(INVOKEVIRTUAL,"CLib/TField","setText","(Ljava/lang/String;)V",false);
                                }
                            } else super.visitMethodInsn(INVOKESTATIC, BOOT, "start", "()V", false);
                        }
                        super.visitInsn(op);
                    }};
                }
                return mv;
            }
        }, 0);
        return writer.toByteArray();
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("input.jar output.jar version");
        if (Files.exists(Path.of(args[1]))) throw new IOException("Output exists");
        try (JarFile src = new JarFile(args[0])) {
            Manifest mf = src.getManifest();
            mf.getMainAttributes().putValue("MIDlet-Name", "HSO Java Offline Zuzong");
            mf.getMainAttributes().putValue("MIDlet-Vendor", "Zuzong");
            mf.getMainAttributes().putValue("MIDlet-Version", args[2]);
            mf.getMainAttributes().putValue("MIDlet-1", "HSO Java Offline Zuzong,/icon.png,com.silverknight.TemMidlet");
            mf.getMainAttributes().putValue("MIDlet-Permissions-Opt", "javax.microedition.io.Connector.socket");
            mf.getMainAttributes().remove(new Attributes.Name("MIDlet-Jar-URL"));
            mf.getMainAttributes().remove(new Attributes.Name("MIDlet-Jar-Size"));
            try (JarOutputStream out = new JarOutputStream(Files.newOutputStream(Path.of(args[1])), mf)) {
                for (Enumeration<JarEntry> it = src.entries(); it.hasMoreElements();) {
                    JarEntry entry = it.nextElement(); String name = entry.getName();
                    if (name.equalsIgnoreCase("META-INF/MANIFEST.MF") || name.matches("(?i)META-INF/.*\\.(SF|RSA|DSA)")) continue;
                    byte[] bytes = src.getInputStream(entry).readAllBytes();
                    if (name.equals("com/silverknight/TemMidlet.class") || name.equals("CLib/mSocket.class") || name.equals("GameScreen/LoginScreen.class")) bytes = patch(name, bytes);
                    out.putNextEntry(new JarEntry(name)); out.write(bytes); out.closeEntry();
                }
            }
        }
        if (changes != 6) throw new IllegalStateException("Expected 6 method hooks, got " + changes);
        System.out.println("6 offline hooks applied");
    }
}
