package offline;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;

/** Validates the shared skill table against the original iOS client's command 29. */
public final class SkillPacket {
    private SkillPacket() {}

    public static byte[] forClient(byte[] table) throws IOException {
        var input = new DataInputStream(new ByteArrayInputStream(table));
        int skills = input.readUnsignedByte();
        if (skills == 0 || skills > 127) throw new IOException("Invalid skill count");
        for (int skill = 0; skill < skills; skill++) {
            input.skipNBytes(2); // ID and icon
            input.skipNBytes(input.readUnsignedShort()); // name
            input.skipNBytes(3); // type and range
            input.skipNBytes(input.readUnsignedShort()); // description
            input.skipNBytes(2); // buff and secondary effect
            int levels = input.readUnsignedByte();
            if (levels == 0 || levels > 127) throw new IOException("Invalid skill level count");
            for (int level = 0; level < levels; level++) {
                input.skipNBytes(19); // cost, requirement, timing and recovery
                int options = input.readUnsignedByte();
                input.skipNBytes(options * 5 + 3); // options, target count and area range
            }
            input.skipNBytes(3); // animation duration and type
        }
        if (input.read() != -1) throw new IOException("Unexpected extra skill data");
        return table;
    }
}
