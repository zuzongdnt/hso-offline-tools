using Mono.Cecil;
using Mono.Cecil.Cil;
using System.Security.Cryptography;

if (args.Length is < 2 or > 3)
    throw new ArgumentException("input.dll output.dll [port]");
int port = args.Length == 3 ? int.Parse(args[2]) : 19139;
var input = Path.GetFullPath(args[0]);
var output = Path.GetFullPath(args[1]);
if (input == output) throw new InvalidOperationException("Keep input unchanged");
var originalHash = SHA256.HashData(File.ReadAllBytes(input));
using var module = ModuleDefinition.ReadModule(input);
TypeDefinition Type(string name) => module.Types.Single(t => t.Name == name);
MethodDefinition Method(string type, string name) => Type(type).Methods.Single(m => m.Name == name);
void Replace(MethodDefinition m, Action<ILProcessor> emit)
{
    m.Body = new MethodBody(m);
    emit(m.Body.GetILProcessor());
}

// Redirect network and saves while retaining the original game logic and assets.
var connect = Method("Session_ME", "connect");
var il = connect.Body.GetILProcessor();
var first = connect.Body.Instructions[0];
il.InsertBefore(first, il.Create(OpCodes.Ldstr, "127.0.0.1"));
il.InsertBefore(first, il.Create(OpCodes.Starg, connect.Parameters[0]));
il.InsertBefore(first, il.Create(OpCodes.Ldc_I4, port));
il.InsertBefore(first, il.Create(OpCodes.Starg, connect.Parameters[1]));

var http = Method("Net", "connectHTTP");
var perform = Type("iCommand").Methods.Single(m => m.Name == "perform" && m.Parameters.Count == 1);
Replace(http, p =>
{
    var end = p.Create(OpCodes.Ret);
    p.Emit(OpCodes.Ldarg_1);
    p.Emit(OpCodes.Brfalse, end);
    p.Emit(OpCodes.Ldarg_1);
    p.Emit(OpCodes.Ldstr, $"Offline:127.0.0.1:{port}:0");
    p.Emit(OpCodes.Callvirt, perform);
    p.Append(end);
});

var savePath = Method("Rms", "GetiPhoneDocumentsPath");
var oldGetter = (MethodReference)savePath.Body.Instructions.Single(i => i.OpCode == OpCodes.Call).Operand;
var dataGetter = new MethodReference("get_dataPath", module.TypeSystem.String, oldGetter.DeclaringType) { HasThis = false };
var concat = new MethodReference("Concat", module.TypeSystem.String, module.TypeSystem.String) { HasThis = false };
concat.Parameters.Add(new ParameterDefinition(module.TypeSystem.String));
concat.Parameters.Add(new ParameterDefinition(module.TypeSystem.String));
Replace(savePath, p =>
{
    p.Emit(OpCodes.Call, dataGetter);
    p.Emit(OpCodes.Ldstr, "/../local-save");
    p.Emit(OpCodes.Call, concat);
    p.Emit(OpCodes.Ret);
});

var mainChar = Method("ReadMessenge", "mainCharInfo");
var inventory = Method("ReadMessenge", "update_InVen_Or_Chest");
var readerType = Type("myReader");
var readShort = readerType.Methods.Single(m => m.Name == "readShort" && m.Parameters.Count == 0);
bool IsField(Instruction i, string name) => i.Operand is FieldReference f && f.Name == name;
bool IsReadByte(Instruction i) => i.Operand is MethodReference m && m.Name == "readByte"
    && m.DeclaringType.Name == "myReader";
var capacity = mainChar.Body.Instructions.Single(i => i.OpCode == OpCodes.Stsfld && IsField(i, "maxInven"));
var capacityRead = mainChar.Body.Instructions.TakeWhile(i => i != capacity).Last(IsReadByte);
capacityRead.Operand = readShort;
var instructions = inventory.Body.Instructions;
var remove = instructions.Single(i => i.Operand is MethodReference m && m.Name == "removeUpdateItemVec");
var countReads = instructions.Skip(instructions.IndexOf(remove) + 1)
    .Where(IsReadByte).Where(i =>
    {
        var store = i.Next;
        if (store == null) return false;
        var firstLoop = store.Next;
        return firstLoop != null && firstLoop.OpCode == OpCodes.Ldc_I4_0
            && firstLoop.Next != null && firstLoop.Next.Next != null
            && firstLoop.Next.Next.OpCode.FlowControl == FlowControl.Branch;
    }).ToList();
if (countReads.Count != 4) throw new InvalidOperationException("Unexpected inventory count fields");
foreach (var read in countReads)
{
    read.Operand = readShort;
    if (read.Next.Operand is not VariableDefinition count)
        throw new InvalidOperationException("Inventory count must be a local");
    count.VariableType = module.TypeSystem.Int16;
}
foreach (var method in Type("TabShopNew").Methods.Where(m => m.HasBody).Append(mainChar))
{
    var bodyIl = method.Body.GetILProcessor();
    foreach (var load in method.Body.Instructions.Where(i => i.OpCode == OpCodes.Ldsfld
        && IsField(i, "maxInven") && i.Next?.OpCode == OpCodes.Ldc_I4_S
        && (sbyte)i.Next.Operand == 42).ToList())
    {
        var bias = bodyIl.Create(OpCodes.Ldc_I4_S, (sbyte)41);
        bodyIl.InsertAfter(load, bias);
        bodyIl.InsertAfter(bias, bodyIl.Create(OpCodes.Add));
    }
}

Directory.CreateDirectory(Path.GetDirectoryName(output)!);
// Accept the normal costume part packets on Windows, as the Android client already does.
{
    var receiver = Method("ReadMessenge", "loadImageDataCharPart");
    FieldDefinition Field(string type, string name) => Type(type).Fields.Single(f => f.Name == name);
    var apply = new MethodDefinition("ApplyReceivedCharPart", MethodAttributes.Private | MethodAttributes.Static,
        module.TypeSystem.Void);
    apply.Parameters.Add(new ParameterDefinition("kind", ParameterAttributes.None, module.TypeSystem.SByte));
    apply.Parameters.Add(new ParameterDefinition("id", ParameterAttributes.None, module.TypeSystem.Int16));
    var bytes = new ArrayType(module.TypeSystem.SByte);
    apply.Parameters.Add(new ParameterDefinition("png", ParameterAttributes.None, bytes));
    apply.Parameters.Add(new ParameterDefinition("metadata", ParameterAttributes.None, bytes));
    Type("ReadMessenge").Methods.Add(apply);
    apply.Body.InitLocals = true;
    var key = new VariableDefinition(module.TypeSystem.String);
    var part = new VariableDefinition(Type("CharPartInfo"));
    apply.Body.Variables.Add(key);
    apply.Body.Variables.Add(part);
    var p = apply.Body.GetILProcessor();
    var end = p.Create(OpCodes.Ret);
    foreach (var bound in new[] { (OpCodes.Ldarg_0, 0, OpCodes.Blt), (OpCodes.Ldarg_0, 6, OpCodes.Bgt),
                                (OpCodes.Ldarg_1, 0, OpCodes.Blt), (OpCodes.Ldarg_1, 255, OpCodes.Bgt) })
    {
        p.Emit(bound.Item1);
        p.Emit(OpCodes.Ldc_I4, bound.Item2);
        p.Emit(bound.Item3, end);
}
    var partKeyConcat = new MethodReference("Concat", module.TypeSystem.String, module.TypeSystem.String);
    for (int i = 0; i < 3; i++) partKeyConcat.Parameters.Add(new ParameterDefinition(module.TypeSystem.Object));
    p.Emit(OpCodes.Ldarg_0); p.Emit(OpCodes.Box, module.TypeSystem.SByte);
    p.Emit(OpCodes.Ldstr, "_");
    p.Emit(OpCodes.Ldarg_1); p.Emit(OpCodes.Box, module.TypeSystem.Int16);
    p.Emit(OpCodes.Call, partKeyConcat); p.Emit(OpCodes.Stloc, key);
    p.Emit(OpCodes.Ldsfld, Field("CharPartInfo", "hashImagePartChar"));
    p.Emit(OpCodes.Ldloc, key);
    p.Emit(OpCodes.Ldarg_2); p.Emit(OpCodes.Ldc_I4_0); p.Emit(OpCodes.Ldc_I4_0); p.Emit(OpCodes.Ldloc, key);
    p.Emit(OpCodes.Call, Type("mImage").Methods.Single(m => m.Name == "createImage" && m.Parameters.Count == 4));
    p.Emit(OpCodes.Ldarg_3);
    p.Emit(OpCodes.Newobj, Type("MainImageDataPartChar").Methods.Single(m => m.IsConstructor && m.Parameters.Count == 2));
    p.Emit(OpCodes.Callvirt, Method("mHashTable", "put"));
    p.Emit(OpCodes.Ldsfld, Field("CRes", "charPartInfo")); p.Emit(OpCodes.Ldarg_0); p.Emit(OpCodes.Ldelem_Ref);
    p.Emit(OpCodes.Ldarg_1); p.Emit(OpCodes.Ldelem_Ref); p.Emit(OpCodes.Stloc, part);
    p.Emit(OpCodes.Ldloc, part); p.Emit(OpCodes.Brfalse, end);
    p.Emit(OpCodes.Ldloc, part); p.Emit(OpCodes.Ldarg_0); p.Emit(OpCodes.Ldarg_1);
    p.Emit(OpCodes.Callvirt, Method("CharPartInfo", "loadNew")); p.Append(end);

    var variables = receiver.Body.Variables;
    var kind = variables.First(v => v.VariableType.MetadataType == MetadataType.SByte);
    var id = variables.First(v => v.VariableType.MetadataType == MetadataType.Int16);
    var arrays = variables.Where(v => v.VariableType.FullName == "System.SByte[]").Take(2).ToArray();
    if (arrays.Length != 2) throw new InvalidOperationException("Unexpected packet parser locals.");
    var anchor = receiver.Body.Instructions.Single(i => i.OpCode == OpCodes.Ldsfld &&
        i.Operand is FieldReference f && f.DeclaringType.Name == "MsgDialog" && f.Name == "curupdate");
    var r = receiver.Body.GetILProcessor();
    var insert = new[] { r.Create(OpCodes.Ldloc, kind), r.Create(OpCodes.Ldloc, id),
        r.Create(OpCodes.Ldloc, arrays[0]), r.Create(OpCodes.Ldloc, arrays[1]), r.Create(OpCodes.Call, apply) };
    foreach (var i in receiver.Body.Instructions)
    {
        if (i.Operand == anchor) i.Operand = insert[0];
}
    foreach (var i in insert) r.InsertBefore(anchor, i);
}


// Animated weapon skins bypass the normal weapon renderer that draws socket gems.
var paintPlayer = Method("MainObject", "paintPlayer");
var paintGem = Method("MainObject", "paintEffectWeapon");
var animatedWeaponLayers = paintPlayer.Body.Instructions
    .Where(i => i.Operand is MethodReference m && m.Name == "paintTopWeaPon").ToArray();
if (animatedWeaponLayers.Length != 2) throw new InvalidOperationException("Unexpected animated weapon renderer");
var painter = paintPlayer.Body.GetILProcessor();
foreach (var layer in animatedWeaponLayers)
{
    var actor = painter.Create(OpCodes.Ldarg_0);
    var graphics = painter.Create(OpCodes.Ldarg_1);
    painter.InsertAfter(layer, actor);
    painter.InsertAfter(actor, graphics);
    painter.InsertAfter(graphics, painter.Create(OpCodes.Call, paintGem));
}

// Repeated equipment refreshes replace the local follower instead of adding a second copy.
{
    var wearing = Method("ReadMessenge", "charWearing");
    var assign = wearing.Body.Instructions.Single(i => i.OpCode == OpCodes.Stsfld
        && i.Operand is FieldReference f && f.DeclaringType.Name == "GameScreen" && f.Name == "pet");
    var oldPet = (FieldReference)assign.Operand;
    var players = Type("GameScreen").Fields.Single(f => f.Name == "Vecplayers");
    var removePet = Type("mVector").Methods.Single(m => m.Name == "removeElement" && m.Parameters.Count == 1);
    var replacePet = wearing.Body.GetILProcessor();
    var previous = replacePet.Create(OpCodes.Ldsfld, oldPet);
    var loadPlayers = replacePet.Create(OpCodes.Ldsfld, players);
    foreach (var instruction in wearing.Body.Instructions)
        if (instruction.Operand == assign) instruction.Operand = previous;
    replacePet.InsertBefore(assign, previous);
    replacePet.InsertBefore(assign, replacePet.Create(OpCodes.Brfalse, assign));
    replacePet.InsertBefore(assign, loadPlayers);
    replacePet.InsertBefore(assign, replacePet.Create(OpCodes.Ldsfld, oldPet));
    replacePet.InsertBefore(assign, replacePet.Create(OpCodes.Callvirt, removePet));
}

// Provide a shared setting for the local game tick and the offline server's timers.
{
    var tab = Type("TabConfig");
    var fast = new FieldDefinition("OfflineFast", FieldAttributes.Assembly | FieldAttributes.Static, module.TypeSystem.Boolean);
    tab.Fields.Add(fast);
    var init = Method("TabConfig", "init");
    var payment = init.Body.Instructions.Single(i => i.OpCode == OpCodes.Ldfld && IsField(i, "cmdDiamond"));
    if (payment.Next.Operand is not MethodReference addPayment || addPayment.Name != "addElement")
        throw new InvalidOperationException("Unexpected top-up menu entry");
    foreach (var instruction in new[] { payment.Previous.Previous, payment.Previous, payment, payment.Next })
    {
        instruction.OpCode = OpCodes.Nop;
        instruction.Operand = null;
    }
    var vector = tab.Fields.Single(f => f.Name == "vecConfig");
    var command = Type("iCommand").Methods.Single(m => m.IsConstructor && m.Parameters.Count == 3
        && m.Parameters[0].ParameterType.MetadataType == MetadataType.String
        && m.Parameters[1].ParameterType.MetadataType == MetadataType.Int32
        && m.Parameters[2].ParameterType.Name == "AvMain");
    var add = Method("mVector", "insertElementAt");
    var global = Method("GlobalService", "gI");
    var chat = Method("GlobalService", "chatPopup");
    var install = init.Body.GetILProcessor();
    var anchor = init.Body.Instructions.Single(i => i.OpCode == OpCodes.Stfld && IsField(i, "vecConfig")).Next;
    var fastLabel = install.Create(OpCodes.Ldstr, "Tốc độ game x2");
    var makeCommand = install.Create(OpCodes.Ldc_I4, 99);
    foreach (var instruction in new[] { install.Create(OpCodes.Ldarg_0), install.Create(OpCodes.Ldfld, vector),
        install.Create(OpCodes.Ldsfld, fast), install.Create(OpCodes.Brtrue, fastLabel),
        install.Create(OpCodes.Ldstr, "Tốc độ game x1"), install.Create(OpCodes.Br, makeCommand), fastLabel, makeCommand,
        install.Create(OpCodes.Ldarg_0), install.Create(OpCodes.Newobj, command), install.Create(OpCodes.Ldc_I4_0),
        install.Create(OpCodes.Callvirt, add) }) install.InsertBefore(anchor, instruction);
    foreach (var instruction in new[] { install.Create(OpCodes.Ldarg_0), install.Create(OpCodes.Ldfld, vector),
        install.Create(OpCodes.Ldstr, "Sao lưu và cập nhật"), install.Create(OpCodes.Ldc_I4, 100),
        install.Create(OpCodes.Ldarg_0), install.Create(OpCodes.Newobj, command), install.Create(OpCodes.Ldc_I4_0),
        install.Create(OpCodes.Callvirt, add) }) install.InsertBefore(anchor, instruction);
    var handler = Method("TabConfig", "commandPointer");
    var action = handler.Body.GetILProcessor();
    var normal = handler.Body.Instructions[0];
    var application = module.AssemblyReferences.Single(a => a.Name == "UnityEngine");
    var applicationType = new TypeReference("UnityEngine", "Application", module, application);
    var openTools = new MethodReference("OpenURL", module.TypeSystem.Void, applicationType);
    openTools.Parameters.Add(new ParameterDefinition(module.TypeSystem.String));
    var toolsStart = action.Create(OpCodes.Ldarg_1);
    foreach (var instruction in new[] { toolsStart, action.Create(OpCodes.Ldc_I4, 100),
        action.Create(OpCodes.Bne_Un, normal), action.Create(OpCodes.Ldstr, "http://127.0.0.1:" + (port == 19140 ? 19141 : 19140) + "/"),
        action.Create(OpCodes.Call, openTools), action.Create(OpCodes.Ret) }) action.InsertBefore(normal, instruction);
    var fastChat = action.Create(OpCodes.Ldstr, "/offline-speed-2");
    var send = action.Create(OpCodes.Callvirt, chat);
    foreach (var instruction in new[] { action.Create(OpCodes.Ldarg_1), action.Create(OpCodes.Ldc_I4, 99),
        action.Create(OpCodes.Bne_Un, toolsStart), action.Create(OpCodes.Ldsfld, fast), action.Create(OpCodes.Ldc_I4_0),
        action.Create(OpCodes.Ceq), action.Create(OpCodes.Stsfld, fast), action.Create(OpCodes.Call, global),
        action.Create(OpCodes.Ldsfld, fast), action.Create(OpCodes.Brtrue, fastChat),
        action.Create(OpCodes.Ldstr, "/offline-speed-1"), action.Create(OpCodes.Br, send), fastChat, send,
        action.Create(OpCodes.Ldarg_0), action.Create(OpCodes.Call, init), action.Create(OpCodes.Ret) })
        action.InsertBefore(toolsStart, instruction);
    var updateLoop = Method("Main", "FixedUpdate");
    var tick = updateLoop.Body.Instructions.Single(i => i.Operand is MethodReference m
        && m.Name == "update" && m.DeclaringType.Name == "TemCanvas");
    var tickIl = updateLoop.Body.GetILProcessor();
    var afterTick = tick.Next;
    var screen = Type("GameCanvas").Fields.Single(f => f.Name == "currentScreen");
    foreach (var instruction in new[] { tickIl.Create(OpCodes.Ldsfld, fast), tickIl.Create(OpCodes.Brfalse, afterTick),
        tickIl.Create(OpCodes.Ldsfld, screen), tickIl.Create(OpCodes.Isinst, Type("GameScreen")),
        tickIl.Create(OpCodes.Brfalse, afterTick), tickIl.Create(tick.Previous.OpCode, (FieldReference)tick.Previous.Operand),
        tickIl.Create(tick.OpCode, (MethodReference)tick.Operand) }) tickIl.InsertBefore(afterTick, instruction);
}

// Use the visible mount frame to select the rider's side-view seat height.
{
    var actor = Type("MainObject");
    var mountUpdate = Method("MainObject", "updateMount");
    var mountType = actor.Fields.Single(f => f.Name == "typeMount");
    var visibleFrame = actor.Fields.Single(f => f.Name == "Fhorse");
    var sideFrameStores = mountUpdate.Body.Instructions
        .Where(i => i.OpCode == OpCodes.Ldsfld && IsField(i, "FRAME_MOVE_LR"))
        .Select(i => mountUpdate.Body.Instructions.SkipWhile(j => j != i)
            .First(j => j.OpCode == OpCodes.Stfld && IsField(j, "frameMount")))
        .Distinct().ToArray();
    if (sideFrameStores.Length != 2)
        throw new InvalidOperationException("Expected exactly two side-view mount frames");
    var mountIl = mountUpdate.Body.GetILProcessor();
    foreach (var store in sideFrameStores)
    {
        var resume = store.Next;
        var frameField = (FieldReference)store.Operand;
        foreach (var instruction in new[]
        {
            mountIl.Create(OpCodes.Ldarg_0), mountIl.Create(OpCodes.Ldfld, mountType),
            mountIl.Create(OpCodes.Ldc_I4_S, (sbyte)24), mountIl.Create(OpCodes.Blt, resume),
            mountIl.Create(OpCodes.Ldarg_0), mountIl.Create(OpCodes.Ldarg_0),
            mountIl.Create(OpCodes.Ldfld, visibleFrame), mountIl.Create(OpCodes.Conv_I1),
            mountIl.Create(OpCodes.Stfld, frameField)
        }) mountIl.InsertBefore(resume, instruction);
    }
}

// Render the native mộng mơ sequence in place of the normal actor layers.
{
    var actor = Type("MainObject");
    var world = Method("MainObject", "paintPlayer");
    var helper = new MethodDefinition("OfflineDream", MethodAttributes.Private, module.TypeSystem.Boolean);
    var time = new FieldDefinition("offlineDreamTime", FieldAttributes.Private, module.TypeSystem.Int64);
    actor.Fields.Add(time);
    actor.Methods.Add(helper);
    helper.Parameters.Add(new ParameterDefinition(world.Parameters[0].ParameterType));
    helper.Body.InitLocals = true;
    var id = new VariableDefinition(module.TypeSystem.Int32);
    var now = new VariableDefinition(module.TypeSystem.Int64);
    var elapsed = new VariableDefinition(module.TypeSystem.Int64);
    var effect = new VariableDefinition(Type("DataSkillEff"));
    foreach (var local in new[] { id, now, elapsed, effect }) helper.Body.Variables.Add(local);
    var h = helper.Body.GetILProcessor();
    var reset = h.Create(OpCodes.Ldarg_0);
    var no = h.Create(OpCodes.Ldc_I4_0);
    var outfit = h.Create(OpCodes.Ldarg_0);
    var measure = h.Create(OpCodes.Ldloc, now);
    FieldDefinition F(string name) => actor.Fields.Single(f => f.Name == name);
    void Field(ILProcessor p, string name) { p.Emit(OpCodes.Ldarg_0); p.Emit(OpCodes.Ldfld, F(name)); }
    var get = Method("MainObject", "getEffMatNa");
    var lookup = get.Body.GetILProcessor();
    var nativeLookup = get.Body.Instructions[0];
    var noHairOverlay = lookup.Create(OpCodes.Ldnull);
    foreach (var i in new[] { lookup.Create(OpCodes.Ldarg_0), lookup.Create(OpCodes.Ldc_I4, 159),
        lookup.Create(OpCodes.Beq, noHairOverlay), lookup.Create(OpCodes.Ldarg_0),
        lookup.Create(OpCodes.Ldc_I4, 160), lookup.Create(OpCodes.Bne_Un, nativeLookup),
        noHairOverlay, lookup.Create(OpCodes.Ret) }) lookup.InsertBefore(nativeLookup, i);
    var draw = Method("DataSkillEff", "paintBottomAll");
    var hidden = Method("MainObject", "checktanghinh");

    Field(h, "idHair"); h.Emit(OpCodes.Stloc, id);
    h.Emit(OpCodes.Ldloc, id); h.Emit(OpCodes.Ldc_I4, 159); h.Emit(OpCodes.Beq, outfit);
    h.Emit(OpCodes.Ldloc, id); h.Emit(OpCodes.Ldc_I4, 160); h.Emit(OpCodes.Bne_Un, reset);
    h.Append(outfit); h.Emit(OpCodes.Ldfld, F("Action")); h.Emit(OpCodes.Brtrue, reset);
    var checkVisibility = h.Create(OpCodes.Ldarg_0);
    Field(h, "typeMount"); h.Emit(OpCodes.Ldc_I4_0); h.Emit(OpCodes.Blt, checkVisibility);
    Field(h, "typeMount"); h.Emit(OpCodes.Ldc_I4, 24); h.Emit(OpCodes.Blt, reset);
    h.Append(checkVisibility); h.Emit(OpCodes.Pop);
    Field(h, "isTanHinh"); h.Emit(OpCodes.Brtrue, reset);
    h.Emit(OpCodes.Ldarg_0); h.Emit(OpCodes.Call, hidden); h.Emit(OpCodes.Brtrue, reset);
    h.Emit(OpCodes.Ldloc, id); h.Emit(OpCodes.Ldc_I4, 91); h.Emit(OpCodes.Add);
    h.Emit(OpCodes.Call, get); h.Emit(OpCodes.Stloc, effect);
    h.Emit(OpCodes.Ldloc, effect); h.Emit(OpCodes.Callvirt, Method("DataSkillEff", "isHavedata"));
    h.Emit(OpCodes.Brfalse, reset);
    h.Emit(OpCodes.Call, Method("mSystem", "currentTimeMillis")); h.Emit(OpCodes.Stloc, now);
    Field(h, time.Name); h.Emit(OpCodes.Brtrue, measure);
    h.Emit(OpCodes.Ldarg_0); h.Emit(OpCodes.Ldloc, now); h.Emit(OpCodes.Stfld, time); h.Emit(OpCodes.Br, no);
    h.Append(measure); Field(h, time.Name); h.Emit(OpCodes.Sub); h.Emit(OpCodes.Stloc, elapsed);
    h.Emit(OpCodes.Ldloc, elapsed); h.Emit(OpCodes.Ldc_I8, 10000L); h.Emit(OpCodes.Blt, no);
    h.Emit(OpCodes.Ldloc, elapsed); h.Emit(OpCodes.Ldc_I8, 13696L); h.Emit(OpCodes.Bge, reset);
    h.Emit(OpCodes.Ldloc, effect); h.Emit(OpCodes.Ldarg_1);
    Field(h, "x"); Field(h, "y");
    h.Emit(OpCodes.Ldloc, elapsed); h.Emit(OpCodes.Ldc_I8, 10000L); h.Emit(OpCodes.Sub);
    h.Emit(OpCodes.Ldc_I8, 33L); h.Emit(OpCodes.Div); h.Emit(OpCodes.Conv_I4);
    h.Emit(OpCodes.Ldc_I4_0); h.Emit(OpCodes.Callvirt, draw);
    h.Emit(OpCodes.Ldc_I4_1); h.Emit(OpCodes.Ret);
    h.Append(reset); h.Emit(OpCodes.Ldc_I8, 0L); h.Emit(OpCodes.Stfld, time);
    h.Append(no); h.Emit(OpCodes.Ret);

    // The full-body outfit includes its own face and eyes.
    var part = Method("MainObject", "getTypePart");
    var eye = part.Body.Instructions.Single(i => i.OpCode == OpCodes.Ldfld && IsField(i, "eye"));
    var partsIl = part.Body.GetILProcessor();
    var hideEye = partsIl.Create(OpCodes.Pop);
    foreach (var i in new[] {
        partsIl.Create(OpCodes.Dup), partsIl.Create(OpCodes.Ldfld, F("idBody")),
        partsIl.Create(OpCodes.Ldc_I4, 253), partsIl.Create(OpCodes.Beq, hideEye),
        partsIl.Create(OpCodes.Dup), partsIl.Create(OpCodes.Ldfld, F("idBody")),
        partsIl.Create(OpCodes.Ldc_I4, 254), partsIl.Create(OpCodes.Bne_Un, eye),
        hideEye, partsIl.Create(OpCodes.Ldc_I4_M1), partsIl.Create(OpCodes.Ret)
    }) partsIl.InsertBefore(eye, i);

    var bodyFrame = Method("MainObject", "getFrameBody");
    var frames = bodyFrame.Body.GetILProcessor();
    var nativeFrame = bodyFrame.Body.Instructions[0];
    var directionFrame = frames.Create(OpCodes.Ldarg_0);
    var sideFrame = frames.Create(OpCodes.Ldc_I4, 12);
    var frontFrame = frames.Create(OpCodes.Ldc_I4_0);
    var addPose = frames.Create(OpCodes.Ldarg_0);
    foreach (var instruction in new[] {
        frames.Create(OpCodes.Ldarg_0), frames.Create(OpCodes.Ldfld, F("idBody")), frames.Create(OpCodes.Ldc_I4, 253), frames.Create(OpCodes.Beq, directionFrame),
        frames.Create(OpCodes.Ldarg_0), frames.Create(OpCodes.Ldfld, F("idBody")), frames.Create(OpCodes.Ldc_I4, 254), frames.Create(OpCodes.Bne_Un, nativeFrame),
        directionFrame, frames.Create(OpCodes.Ldfld, F("Direction")), frames.Create(OpCodes.Brfalse, frontFrame),
        frames.Create(OpCodes.Ldarg_0), frames.Create(OpCodes.Ldfld, F("Direction")), frames.Create(OpCodes.Ldc_I4_1), frames.Create(OpCodes.Bne_Un, sideFrame),
        frames.Create(OpCodes.Ldc_I4_6), frames.Create(OpCodes.Br, addPose), sideFrame, frames.Create(OpCodes.Br, addPose), frontFrame,
        addPose, frames.Create(OpCodes.Ldfld, F("frame")), frames.Create(OpCodes.Conv_U4), frames.Create(OpCodes.Ldc_I4_6), frames.Create(OpCodes.Rem_Un),
        frames.Create(OpCodes.Add), frames.Create(OpCodes.Ret)
    }) frames.InsertBefore(nativeFrame, instruction);

    var rabbit = new MethodDefinition("OfflineRabbit", MethodAttributes.Private, module.TypeSystem.Void);
    actor.Methods.Add(rabbit);
    rabbit.Parameters.Add(new ParameterDefinition(world.Parameters[0].ParameterType));
    var b = rabbit.Body.GetILProcessor();
    var done = b.Create(OpCodes.Ret);
    Field(b, "idMatna"); b.Emit(OpCodes.Ldc_I4, 249); b.Emit(OpCodes.Bne_Un, done);
    Field(b, "Action"); b.Emit(OpCodes.Ldc_I4_4); b.Emit(OpCodes.Beq, done);
    b.Emit(OpCodes.Ldarg_0); b.Emit(OpCodes.Call, hidden); b.Emit(OpCodes.Brtrue, done);
    b.Emit(OpCodes.Ldc_I4, 252); b.Emit(OpCodes.Call, get); b.Emit(OpCodes.Ldarg_1);
    Field(b, "x"); Field(b, "y");
    foreach (var name in new[] { "dyMount", "dy", "ysai", "yjum" }) { Field(b, name); b.Emit(OpCodes.Sub); }
    Field(b, "dyWater"); b.Emit(OpCodes.Add);
    Field(b, "Direction"); b.Emit(OpCodes.Ldc_I4_0); b.Emit(OpCodes.Callvirt, draw); b.Append(done);

    var p = world.Body.GetILProcessor();
    var start = world.Body.Instructions[0];
    var mask = world.Body.Instructions.Single(i => i.OpCode == OpCodes.Ldfld && IsField(i, "idMatna")).Next;
    var tail = world.Body.Instructions.Single(i => i.Operand is MethodReference m && m.Name == "canpaintDataSkillEff").Previous;
    var rabbitStart = p.Create(OpCodes.Ldarg_0);
    foreach (var i in world.Body.Instructions)
        if (i.Operand == tail) i.Operand = rabbitStart;
    foreach (var i in new[] { rabbitStart, p.Create(OpCodes.Ldarg_1), p.Create(OpCodes.Call, rabbit) }) p.InsertBefore(tail,i);
    foreach (var i in new[] { p.Create(OpCodes.Dup), p.Create(OpCodes.Ldc_I4,249), p.Create(OpCodes.Bne_Un,mask),
        p.Create(OpCodes.Pop), p.Create(OpCodes.Ldc_I4_M1) }) p.InsertBefore(mask,i);
    foreach (var i in new[] { p.Create(OpCodes.Ldarg_0), p.Create(OpCodes.Ldarg_1), p.Create(OpCodes.Call,helper),
        p.Create(OpCodes.Brfalse,start), p.Create(OpCodes.Ret) }) p.InsertBefore(start,i);
}

module.Write(output);
if (!originalHash.SequenceEqual(SHA256.HashData(File.ReadAllBytes(input))))
    throw new InvalidOperationException("Input changed");
using var check = ModuleDefinition.ReadModule(output);
var patchedHttp = check.Types.Single(t => t.Name == "Net").Methods.Single(m => m.Name == "connectHTTP");
if (patchedHttp.Body.Instructions.Any(i => i.OpCode == OpCodes.Newobj))
    throw new InvalidOperationException("Unexpected HTTP constructor");
Console.WriteLine("Patched Session_ME.connect, Net.connectHTTP, Rms.GetiPhoneDocumentsPath");
Console.WriteLine("Input unchanged: " + Convert.ToHexString(originalHash).ToLowerInvariant());
Console.WriteLine("Output: " + Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(output))).ToLowerInvariant());
