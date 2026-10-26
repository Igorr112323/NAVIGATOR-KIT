#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace NavigatorKit.Core;

/// <summary>
/// Minimal DXF group-code reader. It extracts ATTRIB code-2 tags and code-1 values.
/// This is intentionally independent from any CAD host and does not parse full DWG.
/// </summary>
public static class DxfAttributeReader
{
    public static Dictionary<string, string> Read(string path)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var lines = File.ReadAllLines(path, Encoding.UTF8);
        string? entityType = null;
        string? tag = null;
        string? value = null;

        void Flush()
        {
            if (!string.IsNullOrEmpty(tag) && value != null)
                result[tag] = value.Trim();
            tag = null;
            value = null;
        }

        for (var i = 0; i + 1 < lines.Length; i += 2)
        {
            if (!int.TryParse(lines[i].Trim(), out var code)) continue;
            var raw = lines[i + 1];
            if (code == 0)
            {
                Flush();
                entityType = raw.Trim();
            }
            else if (entityType == "ATTRIB" && code == 2)
            {
                tag = raw.Trim();
            }
            else if (entityType == "ATTRIB" && code == 1)
            {
                value = raw;
            }
        }
        Flush();
        return result;
    }
}
