#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace NavigatorKit.Core;

public static class ChangeTableWriter
{
    public static List<Dictionary<string, object?>> BuildEmpty(int rows = 10)
    {
        var columns = new[] { "Изм.", "Лист", "№ докум.", "Подп.", "Дата" };
        var result = new List<Dictionary<string, object?>>(rows);
        for (var i = 0; i < rows; i++)
        {
            var row = new Dictionary<string, object?>();
            foreach (var c in columns) row[c] = string.Empty;
            result.Add(row);
        }
        return result;
    }

    public static void Write(string outputDir, string samplesDir)
    {
        // TODO: проверка по ГОСТ Р 2.503-2023 п. 5.12 и разделу 7 ГОСТ Р 21.101-2026:
        // состав граф подтверждён по тексту, но геометрия таблицы и приоритет для СПДС требуют нормоконтроля.
        var columns = new[] { "Изм.", "Лист", "№ докум.", "Подп.", "Дата" };
        CsvUtil.Write(Path.Combine(outputDir, "csharp_change_table_template.csv"), columns, BuildEmpty());
        var rows = new List<Dictionary<string, object?>>();
        var path = Path.Combine(samplesDir, "change_events.json");
        if (File.Exists(path))
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            foreach (var e in doc.RootElement.EnumerateArray())
            {
                rows.Add(new Dictionary<string, object?>
                {
                    ["change_id"] = e.GetProperty("change_id").GetString(),
                    ["operation"] = e.GetProperty("operation").GetString(),
                    ["list_marker"] = e.GetProperty("list_marker").GetString(),
                    ["document"] = e.GetProperty("document").GetString(),
                    ["signature"] = e.GetProperty("signature").GetString(),
                    ["date"] = e.GetProperty("date").GetString(),
                    ["note"] = e.GetProperty("note").GetString(),
                    ["normative_status"] = "ГИПОТЕЗА/ПРОВЕРИТЬ"
                });
            }
        }
        CsvUtil.Write(Path.Combine(outputDir, "csharp_change_register.csv"),
            new[] { "change_id", "operation", "list_marker", "document", "signature", "date", "note", "normative_status" }, rows);
    }
}
