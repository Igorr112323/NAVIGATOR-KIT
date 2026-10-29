#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Encodings.Web;
using System.Text.Json;

namespace NavigatorKit.Core;

public static class ReportWriters
{
    private static readonly string[] MarkOrder = { "АР", "КР", "ОВ" };
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };

    private static int MarkIndex(string mark)
    {
        var idx = Array.IndexOf(MarkOrder, mark);
        return idx < 0 ? 999 : idx;
    }

    private static IOrderedEnumerable<SheetRecord> Ordered(IEnumerable<SheetRecord> sheets) =>
        sheets.OrderBy(s => MarkIndex(s.Mark))
              .ThenBy(s => s.SheetNoNumeric ?? int.MaxValue)
              .ThenBy(s => s.Sequence)
              .ThenBy(s => s.File, StringComparer.Ordinal);

    public static void WriteRegistry(IReadOnlyList<SheetRecord> sheets, string outputDir)
    {
        var headers = new[] { "file", "mark", "doc_designation", "sheet_no", "sheet_name", "format", "revision", "layout", "profile_id", "source_sha256" };
        var rows = sheets.Select(s => new Dictionary<string, object?>
        {
            ["file"] = s.File, ["mark"] = s.Mark, ["doc_designation"] = s.DocDesignation,
            ["sheet_no"] = s.SheetNo, ["sheet_name"] = s.SheetName, ["format"] = s.Format,
            ["revision"] = s.Revision, ["layout"] = s.Layout, ["profile_id"] = s.ProfileId,
            ["source_sha256"] = s.SourceSha256
        });
        CsvUtil.Write(Path.Combine(outputDir, "csharp_sheets_registry.csv"), headers, rows);
        File.WriteAllText(Path.Combine(outputDir, "csharp_sheets_registry.json"),
            JsonSerializer.Serialize(new { status = "CSharp-Core-Preview", sheets }, JsonOptions));
    }

    public static void WriteCompleteness(IReadOnlyList<ValidationIssue> issues, string outputDir)
    {
        var headers = new[] { "issue_id", "code", "severity", "mark", "sheet_no", "file", "field", "message", "suggestion" };
        var rows = issues.Select(i => new Dictionary<string, object?>
        {
            ["issue_id"] = i.IssueId, ["code"] = i.Code, ["severity"] = i.Severity,
            ["mark"] = i.Mark, ["sheet_no"] = i.SheetNo, ["file"] = i.File,
            ["field"] = i.Field, ["message"] = i.Message, ["suggestion"] = i.Suggestion
        });
        CsvUtil.Write(Path.Combine(outputDir, "csharp_completeness_report.csv"), headers, rows);
    }

    public static List<Dictionary<string, object?>> WriteForm1(IReadOnlyList<SheetRecord> sheets,
        IReadOnlyList<ValidationIssue> issues, string outputDir)
    {
        // TODO: проверка по ГОСТ Р 21.101-2026, обязательное приложение Б:
        // CSV содержит данные формы 1, но не сертифицированную геометрию таблицы.
        var notes = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
        foreach (var issue in issues)
        {
            foreach (var part in issue.File.Split(';', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries))
            {
                if (!notes.TryGetValue(part, out var list)) notes[part] = list = new List<string>();
                list.Add(issue.Code);
            }
        }
        var headers = new[] { "Марка", "Лист", "Наименование", "Примечание", "Файл", "Формат", "Профиль" };
        var rows = new List<Dictionary<string, object?>>();
        foreach (var s in Ordered(sheets))
        {
            var codeNote = notes.TryGetValue(s.File, out var list) ? string.Join("; ", list.Distinct().OrderBy(x => x)) : string.Empty;
            rows.Add(new Dictionary<string, object?>
            {
                ["Марка"] = s.Mark,
                ["Лист"] = string.IsNullOrEmpty(s.SheetNo) ? "?" : s.SheetNo,
                ["Наименование"] = string.IsNullOrEmpty(s.SheetName) ? "[НЕ ЗАПОЛНЕНО]" : s.SheetName,
                ["Примечание"] = codeNote,
                ["Файл"] = s.File,
                ["Формат"] = s.Format,
                ["Профиль"] = s.ProfileId
            });
        }
        CsvUtil.Write(Path.Combine(outputDir, "csharp_form1_vedomost.csv"), headers, rows);
        return rows;
    }

    public static List<Dictionary<string, object?>> WriteForm2(string samplesDir, string outputDir)
    {
        // TODO: проверка по ГОСТ Р 21.101-2026, приложение Б: заголовки разделов подчеркивают
        // в графе «Наименование»; точные ширины граф в чертеже не воспроизводятся.
        var headers = new[] { "Раздел", "Обозначение", "Наименование", "Примечание", "Файл", "НормативныйСтатус" };
        var rows = new List<Dictionary<string, object?>>();
        var docsPath = Path.Combine(samplesDir, "reference_documents.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(docsPath));
        var docs = doc.RootElement.GetProperty("documents").EnumerateArray().ToList();
        foreach (var section in new[] { "Ссылочные документы", "Прилагаемые документы" })
        {
            rows.Add(new Dictionary<string, object?>
            {
                ["Раздел"] = section, ["Обозначение"] = "", ["Наименование"] = section,
                ["Примечание"] = "ЗАГОЛОВОК РАЗДЕЛА — ПОДЧЕРКНУТЬ", ["Файл"] = "",
                ["НормативныйСтатус"] = "ФОРМА 2 / ПРИЛОЖЕНИЕ Б-2026"
            });
            foreach (var d in docs)
            {
                if (Get(d, "section") != section) continue;
                var version = Get(d, "version");
                var note = Get(d, "note");
                var file = Get(d, "file");
                var parts = new List<string>();
                if (!string.IsNullOrEmpty(note)) parts.Add(note);
                if (!string.IsNullOrEmpty(version)) parts.Add("версия/изм. ДЭ: " + version);
                if (!string.IsNullOrEmpty(file)) parts.Add("файл: " + Path.GetFileName(file));
                rows.Add(new Dictionary<string, object?>
                {
                    ["Раздел"] = section, ["Обозначение"] = Get(d, "designation"),
                    ["Наименование"] = Get(d, "name"), ["Примечание"] = string.Join("; ", parts),
                    ["Файл"] = file, ["НормативныйСтатус"] = "ДАННЫЕ; ГЕОМЕТРИЯ — ГИПОТЕЗА/ПРОВЕРИТЬ"
                });
            }
        }
        CsvUtil.Write(Path.Combine(outputDir, "csharp_form2_vedomost.csv"), headers, rows);
        return rows;
    }

    public static void WriteNumbering(NumberingResult numbering, string outputDir)
    {
        CsvUtil.Write(Path.Combine(outputDir, "csharp_duplicate_report.csv"),
            new[] { "mark", "sheet_no", "count", "keeper", "files", "to_change", "recommendation" },
            numbering.Duplicates.Select(d => new Dictionary<string, object?>
            {
                ["mark"] = d.Mark, ["sheet_no"] = d.SheetNo, ["count"] = d.Count,
                ["keeper"] = d.Keeper, ["files"] = d.Files, ["to_change"] = d.ToChange,
                ["recommendation"] = d.Recommendation
            }));
        CsvUtil.Write(Path.Combine(outputDir, "csharp_numbering_plan.csv"),
            new[] { "mark", "file", "old_sheet_no", "minimal_new_no", "full_shift_new_no", "action", "requires_approval", "recommendation" },
            numbering.Plan.Select(p => new Dictionary<string, object?>
            {
                ["mark"] = p.Mark, ["file"] = p.File, ["old_sheet_no"] = p.OldSheetNo,
                ["minimal_new_no"] = p.MinimalNewNo, ["full_shift_new_no"] = p.FullShiftNewNo,
                ["action"] = p.Action, ["requires_approval"] = p.RequiresApproval,
                ["recommendation"] = p.Recommendation
            }));
    }

    public static void WritePrintOrder(IReadOnlyList<SheetRecord> sheets,
        IReadOnlyList<Dictionary<string, object?>> form1Rows, string samplesDir, string outputDir)
    {
        var profilePath = Path.Combine(samplesDir, "print_profile.json");
        var copies = 1;
        if (File.Exists(profilePath))
        {
            using var p = JsonDocument.Parse(File.ReadAllText(profilePath));
            if (p.RootElement.TryGetProperty("copies", out var c)) copies = c.GetInt32();
        }
        var headers = new[] { "sequence", "mark", "sheet_no", "sheet_name", "file", "layout", "format", "copies", "source_hash" };
        var rows = new List<Dictionary<string, object?>>();
        var sequence = 0;
        foreach (var s in Ordered(sheets))
        {
            sequence++;
            rows.Add(new Dictionary<string, object?>
            {
                ["sequence"] = sequence, ["mark"] = s.Mark,
                ["sheet_no"] = string.IsNullOrEmpty(s.SheetNo) ? "?" : s.SheetNo,
                ["sheet_name"] = s.SheetName, ["file"] = s.File, ["layout"] = s.Layout,
                ["format"] = s.Format, ["copies"] = copies, ["source_hash"] = s.SourceSha256
            });
        }
        CsvUtil.Write(Path.Combine(outputDir, "csharp_print_order.csv"), headers, rows);
        var job = new
        {
            format = "navigator-kit.print-order/v1",
            target = "manual-sheetsethandoff",
            dst_export = false,
            status = "ORDER-VERIFIED-LOCALLY;NANOCAD-DST-EXPORT-HYPOTHESIS",
            items = rows
        };
        File.WriteAllText(Path.Combine(outputDir, "csharp_print_order.json"),
            JsonSerializer.Serialize(job, JsonOptions));
        var formKeys = form1Rows.Select(r => string.Join("|", r["Марка"], r["Лист"], r["Файл"])).ToList();
        var printKeys = rows.Select(r => string.Join("|", r["mark"], r["sheet_no"], r["file"])).ToList();
        var consistent = formKeys.SequenceEqual(printKeys);
        File.WriteAllText(Path.Combine(outputDir, "csharp_print_order_consistency.json"),
            JsonSerializer.Serialize(new { consistent, form1Rows = formKeys.Count, printOrderItems = printKeys.Count }, JsonOptions));
    }

    private static string Get(JsonElement e, string name) =>
        e.TryGetProperty(name, out var v) ? v.GetString() ?? string.Empty : string.Empty;
}
