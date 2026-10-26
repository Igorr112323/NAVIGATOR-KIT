#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Encodings.Web;
using System.Text.Json;
using NavigatorKit.Core;

namespace NavigatorKit.Cli;

public static class Program
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };

    public static int Main(string[] args)
    {
        if (args.Length == 0 || args[0] == "all")
        {
            try
            {
                RunAll(ParseOptions(args));
                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("FATAL: " + ex);
                Console.Error.WriteLine("Задача помечена как ГИПОТЕЗА/ПРОВЕРИТЬ; проверьте входные данные.");
                return 1;
            }
        }
        if (args[0] == "hello")
        {
            Console.WriteLine("Navigator Kit C# Core: Hello World (no CAD host required)");
            Console.WriteLine("WARNING: MultiCAD .NET SDK 26 integration is not compiled unless NANOCAD_SDK is defined.");
            return 0;
        }
        Console.Error.WriteLine("Usage: navigator-kit [all|hello] [--root DIR] [--input DIR] [--samples DIR] [--mapping FILE] [--output DIR]");
        return 2;
    }

    private static Dictionary<string, string> ParseOptions(string[] args)
    {
        var options = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        for (var i = 0; i < args.Length; i++)
        {
            if (!args[i].StartsWith("--", StringComparison.Ordinal) || i + 1 >= args.Length) continue;
            options[args[i][2..]] = args[i + 1];
            i++;
        }
        return options;
    }

    private static void RunAll(Dictionary<string, string> options)
    {
        var root = options.TryGetValue("root", out var r) ? r : FindRoot();
        var input = options.TryGetValue("input", out var i) ? i : Path.Combine(root, "samples", "synthetic_sets");
        var samples = options.TryGetValue("samples", out var s) ? s : Path.Combine(root, "samples");
        var mapping = options.TryGetValue("mapping", out var m) ? m : Path.Combine(root, "delivery", "xml", "stamp_mapping.xml");
        var output = options.TryGetValue("output", out var o) ? o : Path.Combine(root, "delivery", "data", "csharp-preview");
        Directory.CreateDirectory(output);

        var templates = MappingProfile.Load(mapping);
        var sheets = new SheetScanner(root, templates).Scan(input);
        var issues = new CompletenessValidator(root, samples).Validate(sheets);
        var numbering = NumberingPolicy.Build(sheets);

        ReportWriters.WriteRegistry(sheets, output);
        ReportWriters.WriteCompleteness(issues, output);
        var form1 = ReportWriters.WriteForm1(sheets, issues, output);
        var form2 = ReportWriters.WriteForm2(samples, output);
        ReportWriters.WriteNumbering(numbering, output);
        ReportWriters.WritePrintOrder(sheets, form1, samples, output);
        ChangeTableWriter.Write(output, samples);
        var stamp = StampTransaction.Run(root, samples, output);

        var summary = new
        {
            format = "navigator-kit.csharp-summary/v1",
            status = "CSharp-Core-Run",
            sheets = sheets.Count,
            completenessIssues = issues.Count,
            duplicateGroups = numbering.Duplicates.Count,
            form1Rows = form1.Count,
            form2Rows = form2.Count,
            numberingPlanRows = numbering.Plan.Count,
            stampApplyVerified = stamp.ApplyVerified,
            stampRollbackVerified = stamp.RollbackVerified,
            nanoCADSdkUsed = false,
            warning = "DXF fixtures only; production DWG reading requires a verified MultiCAD .NET adapter."
        };
        File.WriteAllText(Path.Combine(output, "csharp_summary.json"), JsonSerializer.Serialize(summary, JsonOptions));
        Console.WriteLine(JsonSerializer.Serialize(summary, JsonOptions));
    }

    private static string FindRoot()
    {
        var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "tools", "navigator_kit.py"))) return dir.FullName;
            dir = dir.Parent;
        }
        return Directory.GetCurrentDirectory();
    }
}
