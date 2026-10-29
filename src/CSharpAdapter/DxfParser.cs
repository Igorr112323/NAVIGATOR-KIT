using System.Globalization;
namespace CSharpAdapter;

public sealed class StampBlock
{
    public string Name { get; init; } = "";
    public Dictionary<string, string> Attributes { get; } = new(StringComparer.Ordinal);
    public string? Sheet => Attributes.GetValueOrDefault("SHEET");
    public string? Format => Attributes.GetValueOrDefault("FORMAT");
    public string? Mark => Attributes.GetValueOrDefault("MARK");
}
public sealed class DxfResult
{
    public List<StampBlock> Blocks { get; } = new();
    public SortedSet<string> Layers { get; } = new(StringComparer.Ordinal);
    public Dictionary<string, int> Counts { get; } = new();
    public double[]? FrameBounds { get; set; }
}
/// <summary>Controlled ASCII DXF only. ATTRIB tag=2, value=1. HEADER code 9 is not a sheet number.
/// No CAD references; no DWG, nested block resolution or transformed INSERT support.</summary>
public static class DxfParser
{
    private sealed record Record(string Kind, List<(int Code, string Value)> Pairs);
    public static DxfResult ParseFile(string path) => ParseText(File.ReadAllText(path, System.Text.Encoding.UTF8));
    public static DxfResult ParseText(string text)
    {
        var lines = new List<string>();
        using (var reader = new StringReader(text)) { string? line; while ((line = reader.ReadLine()) != null) lines.Add(line); }
        if (lines.Count == 0 || lines.Count % 2 != 0) throw new FormatException("Empty or odd group-code stream");
        var records = new List<Record>(); Record? current = null;
        for (int i = 0; i < lines.Count; i += 2)
        {
            if (!int.TryParse(lines[i].Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out var code))
                throw new FormatException("Invalid group code");
            if (code == 0) { current = new Record(lines[i + 1].Trim(), new()); records.Add(current); }
            else { if (current == null) throw new FormatException("Code before first entity"); current.Pairs.Add((code, lines[i + 1])); }
        }
        var result = new DxfResult(); bool inEntities = false; StampBlock? block = null;
        foreach (var record in records)
        {
            string? Value(int code) => record.Pairs.FirstOrDefault(p => p.Code == code).Value;
            double Number(string value) => double.Parse(value, CultureInfo.InvariantCulture);
            if (record.Kind == "SECTION") { inEntities = Value(2) == "ENTITIES"; continue; }
            if (record.Kind == "ENDSEC") { inEntities = false; block = null; continue; }
            if (!inEntities) continue;
            result.Counts[record.Kind] = result.Counts.GetValueOrDefault(record.Kind) + 1;
            if (Value(8) is string layer) result.Layers.Add(layer);
            if (record.Kind == "INSERT")
            {
                foreach (int scale in new[] {41,42,43}) if (Value(scale) is string v && Number(v) != 1) throw new NotSupportedException("Scaled INSERT");
                if (Value(50) is string angle && Number(angle) != 0) throw new NotSupportedException("Rotated INSERT");
                block = new StampBlock { Name = Value(2) ?? "" }; result.Blocks.Add(block);
            }
            else if (record.Kind == "ATTRIB")
            {
                if (block == null) throw new FormatException("Orphan ATTRIB");
                string tag = Value(2) ?? throw new FormatException("Missing attribute tag");
                if (!block.Attributes.TryAdd(tag, Value(1) ?? "")) throw new FormatException("Duplicate attribute: " + tag);
            }
            else if (record.Kind == "SEQEND") block = null;
            else if (record.Kind == "LWPOLYLINE" && result.FrameBounds == null)
            {
                var xs = record.Pairs.Where(p => p.Code == 10).Select(p => Number(p.Value)).ToArray();
                var ys = record.Pairs.Where(p => p.Code == 20).Select(p => Number(p.Value)).ToArray();
                if (xs.Length == 0 || xs.Length != ys.Length) throw new FormatException("Invalid polyline coordinates");
                if (record.Pairs.Any(p => p.Code == 42 && Number(p.Value) != 0)) throw new NotSupportedException("Bulged polyline");
                result.FrameBounds = new[] { xs.Min(), ys.Min(), xs.Max(), ys.Max() };
            }
        }
        return result;
    }
}
