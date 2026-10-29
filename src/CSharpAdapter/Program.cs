using System.Text.Json;
using CSharpAdapter;
if (args.Length != 1) { Console.Error.WriteLine("Usage: CSharpAdapter <ascii-dxf-path>"); return 2; }
try { Console.WriteLine(JsonSerializer.Serialize(DxfParser.ParseFile(args[0]), new JsonSerializerOptions { WriteIndented = true })); return 0; }
catch (Exception ex) { Console.Error.WriteLine(ex.Message); return 1; }
