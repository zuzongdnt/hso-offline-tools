using Mono.Cecil;
using Mono.Cecil.Cil;
using System.Security.Cryptography;

if (args.Length != 2)
    throw new ArgumentException("input.dll output.dll");
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
il.InsertBefore(first, il.Create(OpCodes.Ldc_I4, 19139));
il.InsertBefore(first, il.Create(OpCodes.Starg, connect.Parameters[1]));

var http = Method("Net", "connectHTTP");
var perform = Type("iCommand").Methods.Single(m => m.Name == "perform" && m.Parameters.Count == 1);
Replace(http, p =>
{
    var end = p.Create(OpCodes.Ret);
    p.Emit(OpCodes.Ldarg_1);
    p.Emit(OpCodes.Brfalse, end);
    p.Emit(OpCodes.Ldarg_1);
    p.Emit(OpCodes.Ldstr, "Offline:127.0.0.1:19139:0");
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

Directory.CreateDirectory(Path.GetDirectoryName(output)!);
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
