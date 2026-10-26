#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace NavigatorKit.Core;

public sealed class CompletenessValidator
{
    private static readonly HashSet<string> BasicFormats =
        new(new[] { "A0", "A1", "A2", "A3", "A4", "A5" }, StringComparer.OrdinalIgnoreCase);
    private static readonly Dictionary<string, HashSet<int>> Derived = new(StringComparer.OrdinalIgnoreCase)
    {
        ["A0"] = new HashSet<int> { 2, 3 },
        ["A1"] = new HashSet<int> { 3, 4 },
        ["A2"] = new HashSet<int> { 3, 4, 5 },
        ["A3"] = new HashSet<int> { 3, 4, 5, 6, 7 },
        ["A4"] = new HashSet<int> { 3, 4, 5, 6, 7, 8, 9 }
    };

    private readonly string _root;
    private readonly string _samples;

    public CompletenessValidator(string root, string samples)
    {
        _root = root;
        _samples = samples;
    }

    public List<ValidationIssue> Validate(IReadOnlyList<SheetRecord> sheets)
    {
        var issues = new List<ValidationIssue>();
        foreach (var s in sheets)
        {
            CheckRequired(s, "mark", issues);
            CheckRequired(s, "doc_designation", issues);
            CheckRequired(s, "sheet_no", issues);
            CheckRequired(s, "sheet_name", issues);
            CheckRequired(s, "format", issues);

            // TODO: проверка по ГОСТ 2.301-68 — сверить фактические размеры внешней рамки в CAD,
            // а не только строковое обозначение формата в штампе.
            if (!IsAllowedFormat(s.Format))
                Add(issues, "INVALID_FORMAT", "ERROR",
                    $"Обозначение формата «{s.Format}» не соответствует проверяемому перечню.",
                    s.Mark, s.SheetNo, s.File, "format", "Проверить ГОСТ 2.301-68 и фактический размер рамки.");

            if (string.IsNullOrWhiteSpace(s.ProfileId))
                Add(issues, "MAPPING_MISMATCH", "ERROR", "Не найден XML-профиль штампа.",
                    s.Mark, s.SheetNo, s.File, "profile_id", "Добавить реальные теги атрибутов в mapping.");
        }

        foreach (var group in sheets.Where(x => x.SheetNoNumeric.HasValue)
                     .GroupBy(x => new { x.Mark, Number = x.SheetNoNumeric!.Value })
                     .Where(g => g.Count() > 1))
        {
            Add(issues, "DUPLICATE_SHEET_NUMBER", "ERROR",
                $"Номер листа {group.Key.Number} используется {group.Count()} разами.",
                group.Key.Mark, group.Key.Number.ToString(), string.Join("; ", group.Select(x => x.File)),
                "sheet_no", "Утвердить сдвиг нумерации.");
        }

        foreach (var markGroup in sheets.GroupBy(x => x.Mark))
        {
            var nums = markGroup.Where(x => x.SheetNoNumeric.HasValue).Select(x => x.SheetNoNumeric!.Value).ToList();
            if (nums.Count == 0) continue;
            var missing = Enumerable.Range(1, nums.Max()).Except(nums).ToList();
            if (missing.Count > 0)
                Add(issues, "SEQUENCE_GAP", "WARN", "Нарушена последовательность номеров листов.",
                    markGroup.Key, "", "", "sheet_no", "Отсутствуют: " + string.Join(", ", missing));
        }

        var expected = CsvUtil.Read(Path.Combine(_samples, "expected_registry.csv"));
        var expectedFiles = expected.Select(r => r["file"]).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var actualFiles = sheets.Select(s => s.File).ToHashSet(StringComparer.OrdinalIgnoreCase);
        foreach (var r in expected)
        {
            if (!actualFiles.Contains(r["file"]))
                Add(issues, "IN_REGISTRY_NO_FILE", "ERROR", "Есть запись в реестре, нет файла листа.",
                    r.GetValueOrDefault("mark"), r.GetValueOrDefault("sheet_no"), r["file"], "file",
                    "Найти файл или удалить запись.");
        }
        foreach (var s in sheets)
        {
            if (!expectedFiles.Contains(s.File))
                Add(issues, "FILE_NOT_IN_REGISTRY", "ERROR", "Есть файл листа, нет записи в реестре.",
                    s.Mark, s.SheetNo, s.File, "file", "Добавить лист в ведомость.");
        }

        var docsPath = Path.Combine(_samples, "reference_documents.json");
        if (File.Exists(docsPath))
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(docsPath));
            var listed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var d in doc.RootElement.GetProperty("documents").EnumerateArray())
            {
                var rel = d.TryGetProperty("file", out var f) ? f.GetString() ?? string.Empty : string.Empty;
                if (!string.IsNullOrEmpty(rel)) listed.Add(rel);
                if (!string.IsNullOrEmpty(rel) && !File.Exists(Path.Combine(_root, rel)))
                    Add(issues, "DOC_IN_REGISTRY_NO_FILE", "ERROR", "Документ есть в ведомости, файл отсутствует.",
                        "", "", rel, "file", "Вложить документ или исправить ведомость.");
            }
            var refDir = Path.Combine(_samples, "reference_docs");
            if (Directory.Exists(refDir))
            {
                foreach (var file in Directory.GetFiles(refDir))
                {
                    var rel = Path.GetRelativePath(_root, file).Replace('\\', '/');
                    if (!listed.Contains(rel))
                        Add(issues, "DOC_FILE_NOT_IN_REGISTRY", "WARN", "Файл документа не внесён в ведомость ф.2.",
                            "", "", rel, "file", "Добавить в раздел ссылочных/прилагаемых документов.");
                }
            }
        }
        return issues;
    }

    private static void CheckRequired(SheetRecord s, string field, List<ValidationIssue> issues)
    {
        var value = field switch
        {
            "mark" => s.Mark,
            "doc_designation" => s.DocDesignation,
            "sheet_no" => s.SheetNo,
            "sheet_name" => s.SheetName,
            "format" => s.Format,
            _ => string.Empty
        };
        if (string.IsNullOrWhiteSpace(value))
            Add(issues, "EMPTY_STAMP_FIELD", "ERROR", $"Пустая обязательная графа штампа «{field}».",
                s.Mark, s.SheetNo, s.File, field, "Заполнить атрибут основной надписи.");
    }

    private static void Add(List<ValidationIssue> issues, string code, string severity, string message,
        string mark = "", string sheetNo = "", string file = "", string field = "", string suggestion = "")
    {
        issues.Add(new ValidationIssue
        {
            IssueId = $"ISS-{issues.Count + 1:0000}",
            Code = code,
            Severity = severity,
            Mark = mark,
            SheetNo = sheetNo,
            File = file,
            Field = field,
            Message = message,
            Suggestion = suggestion
        });
    }

    public static bool IsAllowedFormat(string value)
    {
        var fmt = value.Trim().ToUpperInvariant().Replace("А", "A").Replace("×", "X");
        if (BasicFormats.Contains(fmt)) return true;
        var m = Regex.Match(fmt, @"^A([0-4])X(\d+)$");
        return m.Success && Derived.TryGetValue("A" + m.Groups[1].Value, out var allowed)
            && allowed.Contains(int.Parse(m.Groups[2].Value));
    }
}
