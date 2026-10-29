# Portable C# ASCII-DXF parser (not a MultiCAD adapter)

Target: .NET 8; no CAD SDK references. This starts the Python-to-C# port.

```sh
dotnet build src/CSharpAdapter/CSharpAdapter.csproj -c Release
dotnet test src/CSharpAdapter/Tests/CSharpAdapter.Tests.csproj -c Release
dotnet run --project src/CSharpAdapter -- delivery/linux-stand/samples/stamp_01.dxf
```

`ParseFile(path)` and `ParseText(text)` are separate: a path must never be confused
with raw text. ATTRIB group 2 is the tag, 1 is value; group 9 is NOT sheet number.
12 fixture theory cases use the exact same DXF as Python, plus 16 semantic/negative
cases = 28 xUnit cases. This is not a claim that the 28 Python tests have all been ported.
Fixtures copy into test output through the test csproj; package restore needs NuGet.

Supports ENTITIES INSERT/ATTRIB and first top-level LWPOLYLINE bounds, layer names,
UTF-8 values. Rejects duplicate tags within an INSERT, unsupported rotated/scaled
INSERT, and bulged first polyline. No DWG, nested blocks, old code-page decoding,
full DXF validation, required-field norm control, rollback or CAD transactions.
Bounds are a controlled fixture rectangle, not arbitrary drawing extents.
Missing MARK remains null, never inferred from DESIGNATION.

Local Linux sandbox has no dotnet: compilation/execution is delegated to the
`Portable CSharp DXF parser` GitHub Actions workflow (.NET 8 Ubuntu).
Consult actual CI logs/TRX before calling this compiled/tested. Windows/nanoCAD
host execution is still ГИПОТЕЗА/ПРОВЕРИТЬ.
SDK bindings belong in NavigatorKit.NanoCad after verifying SDK 26 TFM/DLL/API;
do not add a guessed MultiCAD26.dll reference to this portable project.
