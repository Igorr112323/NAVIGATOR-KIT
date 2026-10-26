#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

namespace NavigatorKit.Core;

public static class CsvUtil
{
    public static string Escape(object? value)
    {
        var s = value?.ToString() ?? string.Empty;
        if (s.Contains(';') || s.Contains('"') || s.Contains('\r') || s.Contains('\n'))
            return "\"" + s.Replace("\"", "\"\"") + "\"";
        return s;
    }

    public static void Write(string path, string[] headers, IEnumerable<Dictionary<string, object?>> rows)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        using var sw = new StreamWriter(path, false, new UTF8Encoding(true));
        sw.WriteLine(string.Join(";", headers.Select(Escape)));
        foreach (var row in rows)
            sw.WriteLine(string.Join(";", headers.Select(h => Escape(row.TryGetValue(h, out var v) ? v : null))));
    }

    public static List<Dictionary<string, string>> Read(string path)
    {
        var text = File.ReadAllText(path, Encoding.UTF8).TrimStart('\uFEFF');
        var rows = new List<Dictionary<string, string>>();
        var cells = new List<string>();
        var current = new StringBuilder();
        bool quoted = false;
        string[]? headers = null;

        void FlushCell()
        {
            cells.Add(current.ToString());
            current.Clear();
        }

        void FlushRow()
        {
            FlushCell();
            if (headers == null)
            {
                headers = cells.ToArray();
            }
            else
            {
                var row = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                for (var i = 0; i < headers.Length; i++)
                    row[headers[i]] = i < cells.Count ? cells[i] : string.Empty;
                rows.Add(row);
            }
            cells.Clear();
        }

        for (var i = 0; i < text.Length; i++)
        {
            var c = text[i];
            if (quoted)
            {
                if (c == '"')
                {
                    if (i + 1 < text.Length && text[i + 1] == '"') { current.Append('"'); i++; }
                    else quoted = false;
                }
                else current.Append(c);
            }
            else if (c == '"') quoted = true;
            else if (c == ';') FlushCell();
            else if (c == '\n') { if (current.Length > 0 || cells.Count > 0) FlushRow(); }
            else if (c != '\r') current.Append(c);
        }
        if (current.Length > 0 || cells.Count > 0) FlushRow();
        return rows;
    }
}
