using Mono.Cecil;
using Mono.Cecil.Cil;
if (args.Length is < 2 or > 3 || Path.GetFullPath(args[0]) == Path.GetFullPath(args[1])) throw new ArgumentException("input output [--inventory]");
using var module = ModuleDefinition.ReadModule(args[0]);
TypeDefinition T(string name) => module.Types.Single(t => t.Name == name);
if (args.Length == 3)
{
    if (args[2] != "--inventory") throw new ArgumentException("Expected --inventory");
    var tab = T("TabShopNew");
    var pointer = tab.Methods.Single(m => m.Name == "updatePointer");
    var pointerIl = pointer.Body.GetILProcessor();
    var selected = tab.Fields.Single(f => f.Name == "idSelect");
    var page = tab.Fields.Single(f => f.Name == "currentTab");
    var compare = pointer.Body.Instructions.First(i => i.OpCode == OpCodes.Ldfld && i.Operand == selected).Next;
    if (compare.OpCode != OpCodes.Bne_Un) throw new InvalidOperationException("Unexpected touch comparison");
    foreach (var instruction in new[] {
        pointerIl.Create(OpCodes.Ldarg_0), pointerIl.Create(OpCodes.Ldfld, page),
        pointerIl.Create(OpCodes.Ldc_I4_S, (sbyte)42), pointerIl.Create(OpCodes.Mul), pointerIl.Create(OpCodes.Sub)
    }) pointerIl.InsertBefore(compare, instruction);
    var invalidSlot = pointer.Body.Instructions.Single(i => i.OpCode == OpCodes.Ldc_I4_S && (sbyte)i.Operand == 126);
    invalidSlot.OpCode = OpCodes.Ldc_I4_M1;
    invalidSlot.Operand = null;
    module.Write(args[1]);
    return;
}
var player = T("Player");
var changeMap = T("ReadMessenge").Methods.Single(m => m.Name == "changeMap");
var il = changeMap.Body.GetILProcessor();
var start = changeMap.Body.Instructions[0];
foreach (var instruction in new[] {
    il.Create(OpCodes.Ldc_I4_0), il.Create(OpCodes.Stsfld, player.Fields.Single(f => f.Name == "isLockKey")),
    il.Create(OpCodes.Ldc_I4_1), il.Create(OpCodes.Stsfld, player.Fields.Single(f => f.Name == "isSendMove"))
}) il.InsertBefore(start, instruction);
var actor = T("MainObject");
var bodyFrame = actor.Methods.Single(m => m.Name == "getFrameBody");
var originalFrame = bodyFrame.Body.Instructions.First(i => i.OpCode == OpCodes.Bne_Un).Operand as Instruction
    ?? throw new InvalidOperationException("Missing native body frame branch");
while (bodyFrame.Body.Instructions[0] != originalFrame)
    bodyFrame.Body.Instructions.RemoveAt(0);
// Use the original renderer's phase counter for all 72 costume frames.
var idle = actor.Methods.Single(m => m.Name == "OfflineDream");
var idleIl = idle.Body.GetILProcessor();
var idleStart = idle.Body.Instructions[0];
var idleReturn = idle.Body.Instructions.Last(i => i.OpCode == OpCodes.Ret).Previous;
var mount = actor.Fields.Single(f => f.Name == "typeMount");
foreach (var i in new[] { idleIl.Create(OpCodes.Ldarg_0), idleIl.Create(OpCodes.Ldfld, mount),
    idleIl.Create(OpCodes.Ldc_I4_0), idleIl.Create(OpCodes.Bge, idleReturn) }) idleIl.InsertBefore(idleStart, i);
var paint = actor.Methods.Single(m => m.Name == "paintPlayer");
var paintIl = paint.Body.GetILProcessor();
var paintStart = paint.Body.Instructions[0];
var body = actor.Fields.Single(f => f.Name == "idBody");
var unmounted = paintIl.Create(OpCodes.Ldarg_0);
var mounted = paintIl.Create(OpCodes.Ldarg_0);
foreach (var i in new[] {
    paintIl.Create(OpCodes.Ldarg_0), paintIl.Create(OpCodes.Ldfld, mount), paintIl.Create(OpCodes.Ldc_I4_0), paintIl.Create(OpCodes.Blt, unmounted),
    paintIl.Create(OpCodes.Ldarg_0), paintIl.Create(OpCodes.Ldfld, body), paintIl.Create(OpCodes.Ldc_I4,253), paintIl.Create(OpCodes.Blt,paintStart),
    paintIl.Create(OpCodes.Ldarg_0), paintIl.Create(OpCodes.Ldfld, body), paintIl.Create(OpCodes.Ldc_I4,254), paintIl.Create(OpCodes.Bgt,paintStart),
    mounted, paintIl.Create(OpCodes.Ldarg_0), paintIl.Create(OpCodes.Ldfld,body), paintIl.Create(OpCodes.Ldc_I4_2), paintIl.Create(OpCodes.Add), paintIl.Create(OpCodes.Conv_I2), paintIl.Create(OpCodes.Stfld,body), paintIl.Create(OpCodes.Br,paintStart),
    unmounted, paintIl.Create(OpCodes.Ldfld,body), paintIl.Create(OpCodes.Ldc_I4,255), paintIl.Create(OpCodes.Blt,paintStart),
    paintIl.Create(OpCodes.Ldarg_0), paintIl.Create(OpCodes.Ldfld,body), paintIl.Create(OpCodes.Ldc_I4,256), paintIl.Create(OpCodes.Bgt,paintStart),
    paintIl.Create(OpCodes.Ldarg_0), paintIl.Create(OpCodes.Ldarg_0), paintIl.Create(OpCodes.Ldfld,body), paintIl.Create(OpCodes.Ldc_I4_2), paintIl.Create(OpCodes.Sub), paintIl.Create(OpCodes.Conv_I2), paintIl.Create(OpCodes.Stfld,body)
}) paintIl.InsertBefore(paintStart,i);
var part = actor.Methods.Single(m => m.Name == "getTypePart");
var partIl = part.Body.GetILProcessor(); var partStart = part.Body.Instructions[0];
var hideParts = partIl.Create(OpCodes.Ldc_I4_M1);
foreach(var i in new[] {
    partIl.Create(OpCodes.Ldarg_0),partIl.Create(OpCodes.Ldfld,body),partIl.Create(OpCodes.Ldc_I4,255),partIl.Create(OpCodes.Blt,partStart),
    partIl.Create(OpCodes.Ldarg_0),partIl.Create(OpCodes.Ldfld,body),partIl.Create(OpCodes.Ldc_I4,256),partIl.Create(OpCodes.Bgt,partStart),
    partIl.Create(OpCodes.Ldarg_1),partIl.Create(OpCodes.Ldc_I4_1),partIl.Create(OpCodes.Bne_Un,hideParts),
    partIl.Create(OpCodes.Ldc_I4_0),partIl.Create(OpCodes.Ret),
    hideParts,partIl.Create(OpCodes.Ret)
}) partIl.InsertBefore(partStart,i);
int fps = 0;
foreach (var type in module.Types)
foreach (var method in type.Methods.Where(m => m.HasBody)) {
    foreach (var instruction in method.Body.Instructions.ToArray()) {
        if (instruction.Operand is MethodReference call && call.Name == "set_targetFrameRate") {
            var p = method.Body.GetILProcessor();
            p.InsertBefore(instruction, p.Create(OpCodes.Pop));
            p.InsertBefore(instruction, p.Create(OpCodes.Ldc_I4_M1));
            fps++;
        }
    }
}
if (fps == 0) throw new InvalidOperationException("No FPS setting found");
module.Write(args[1]);
Console.WriteLine($"Map input reset installed; unlimited FPS setters: {fps}");
