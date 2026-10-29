#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace NavigatorKit.Core;

public sealed class SheetScanner
{
    private readonly string _root;
    private readonly IReadOnlyList<StampTemplate> _templates;

    public SheetScanner(string root, IReadOnlyList<StampTemplate> templates)
    {
        _root = root;
        _templates = templates;
    }

    public List<SheetRecord> Scan(string inputDirectory)
    {
        var files = Directory.GetFiles(inputDirectory, "*.dxf", SearchOption.AllDirectories)
            .OrderBy(x => x, StringComparer.Ordinal).ToArray();
        var result = new List<SheetRecord>(files.Length);
        foreach (var file in files)
        {
            var attrs = DxfAttributeReader.Read(file);
            var template = MappingProfile.Select(attrs, _templates);
            var mapped = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            if (template != null)
            {
                foreach (var pair in template.TagToField)
                    mapped[pair.Value] = attrs.TryGetValue(pair.Key, out var v) ? v.Trim() : string.Empty;
            }

            string Get(string field) => mapped.TryGetValue(field, out var v) ? v : string.Empty;
            var rel = Path.GetRelativePath(_root, file).Replace('\\', '/');
            var sheetNo = Get("sheet_no");
            result.Add(new SheetRecord
            {
                File = rel,
                FileName = Path.GetFileName(file),
                SourceSha256 = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(file))),
                Sequence = SequenceFromName(file),
                Mark = !string.IsNullOrWhiteSpace(Get("mark")) ? Get("mark") : new DirectoryInfo(Path.GetDirectoryName(file)!).Name,
                DocDesignation = Get("doc_designation"),
                SheetNo = sheetNo,
                SheetNoNumeric = int.TryParse(sheetNo, out var n) ? n : null,
                SheetName = Get("sheet_name"),
                Format = Get("format"),
                Revision = Get("revision"),
                Layout = Get("layout"),
                ProfileId = template?.Id ?? string.Empty,
                BlockName = template?.BlockName ?? string.Empty,
                ProfileStatus = template?.Status ?? "UNKNOWN",
                StampAttributes = attrs
            });
        }
        return result;
    }

    private static int SequenceFromName(string path)
    {
        var m = Regex.Match(Path.GetFileNameWithoutExtension(path), @"_(\d+)$");
        return m.Success && int.TryParse(m.Groups[1].Value, out var n) ? n : 0;
    }
}
