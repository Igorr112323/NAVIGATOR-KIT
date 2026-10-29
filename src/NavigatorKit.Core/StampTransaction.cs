#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace NavigatorKit.Core;

public sealed class StampPatchRequest
{
    [JsonPropertyName("patches")] public List<StampPatchItem> Patches { get; set; } = new();
}

public sealed class StampPatchItem
{
    [JsonPropertyName("file")] public string File { get; set; } = string.Empty;
    [JsonPropertyName("tag")] public string Tag { get; set; } = string.Empty;
    [JsonPropertyName("old_value")] public string OldValue { get; set; } = string.Empty;
    [JsonPropertyName("new_value")] public string NewValue { get; set; } = string.Empty;
}

public sealed class StampTransactionReport
{
    public bool ApplyVerified { get; set; }
    public bool RollbackVerified { get; set; }
    public bool OriginalFilesModified { get; set; }
    public string Carrier { get; set; } = "synthetic DXF text fixtures";
    public string DwgWriteStatus { get; set; } = "ГИПОТЕЗА/ПРОВЕРИТЬ — нужен MultiCAD .NET adapter";
    public List<Dictionary<string, object?>> Patches { get; set; } = new();
}

public static class StampTransaction
{
    public static StampTransactionReport Run(string root, string samplesDir, string outputDir)
    {
        var workspace = Path.Combine(outputDir, "csharp_stamp_workspace");
        if (Directory.Exists(workspace)) Directory.Delete(workspace, true);
        Directory.CreateDirectory(workspace);
        var requestPath = Path.Combine(samplesDir, "stamp_patch_request.json");
        var request = JsonSerializer.Deserialize<StampPatchRequest>(File.ReadAllText(requestPath))
                      ?? new StampPatchRequest();
        var report = new StampTransactionReport();
        var allApply = true;
        var allRollback = true;

        foreach (var patch in request.Patches)
        {
            var source = Path.Combine(root, patch.File);
            var target = Path.Combine(workspace, Path.GetFileName(source));
            var backup = target + ".bak";
            var before = File.ReadAllText(source);
            var beforeHash = Sha(before);
            File.Copy(source, target, true);
            File.WriteAllText(backup, before);
            var oldActual = DxfAttributeReader.Read(target).TryGetValue(patch.Tag, out var v) ? v : string.Empty;
            var replaced = ReplaceAttribute(before, patch.Tag, patch.NewValue, out var replacedOld);
            File.WriteAllText(target, replaced);
            var afterHash = Sha(File.ReadAllText(target));
            var afterValue = DxfAttributeReader.Read(target).TryGetValue(patch.Tag, out var av) ? av : string.Empty;
            var applyOk = afterValue == patch.NewValue && replacedOld == patch.OldValue && oldActual == patch.OldValue;
            File.Copy(backup, target, true);
            var rollbackHash = Sha(File.ReadAllText(target));
            var rollbackOk = rollbackHash == beforeHash;
            allApply &= applyOk;
            allRollback &= rollbackOk;

            // TODO: проверка по ГОСТ — после любой правки штампа повторно контролировать
            // обязательные графы и состав ведомости перед записью в реальный DWG.
            report.Patches.Add(new Dictionary<string, object?>
            {
                ["file"] = patch.File,
                ["tag"] = patch.Tag,
                ["old_value"] = patch.OldValue,
                ["new_value"] = patch.NewValue,
                ["before_sha256"] = beforeHash,
                ["after_sha256"] = afterHash,
                ["rollback_sha256"] = rollbackHash,
                ["apply_verified"] = applyOk,
                ["rollback_verified"] = rollbackOk
            });
        }
        report.ApplyVerified = allApply;
        report.RollbackVerified = allRollback;
        report.OriginalFilesModified = false;
        var options = new JsonSerializerOptions { WriteIndented = true };
        File.WriteAllText(Path.Combine(outputDir, "csharp_stamp_patch_report.json"),
            JsonSerializer.Serialize(report, options));
        CsvUtil.Write(Path.Combine(outputDir, "csharp_stamp_patch_plan.csv"),
            new[] { "file", "tag", "old_value", "new_value", "before_sha256", "after_sha256", "rollback_sha256", "apply_verified", "rollback_verified" },
            report.Patches);
        return report;
    }

    private static string ReplaceAttribute(string text, string tag, string newValue, out string? oldValue)
    {
        // DXF writers may emit code 1 (value) before code 2 (tag).
        // Buffer the entire ATTRIB entity before replacing its value.
        var replacedOldLocal = (string?)null;
        var lines = text.Replace("\r\n", "\n").Split('\n');
        string? entity = null;
        var pairs = new List<(string Code, string Value, int Index)>();

        void Flush()
        {
            if (entity != "ATTRIB" || pairs.Count == 0) return;
            var entityTag = pairs.FirstOrDefault(p => p.Code == "2").Value;
            if (!string.Equals(entityTag, tag, StringComparison.OrdinalIgnoreCase)) return;
            foreach (var p in pairs)
            {
                if (p.Code != "1") continue;
                replacedOldLocal = p.Value;
                lines[p.Index] = newValue;
                break;
            }
        }

        for (var i = 0; i + 1 < lines.Length; i += 2)
        {
            var code = lines[i].Trim();
            var value = lines[i + 1];
            if (code == "0")
            {
                Flush();
                entity = value.Trim();
                pairs.Clear();
            }
            else
            {
                pairs.Add((code, value, i + 1));
            }
        }
        Flush();
        oldValue = replacedOldLocal;
        return string.Join("\n", lines);
    }

    private static string Sha(string text) => Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(text)));
}
