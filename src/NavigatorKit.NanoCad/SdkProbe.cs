#nullable enable
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;

namespace NavigatorKit.NanoCad;

/// <summary>
/// Host-independent reflection probe. It does not reference any unverified CAD type.
/// Load the assembly into nanoCAD and call SdkProbe.Run() from a verified command.
/// </summary>
public static class SdkProbe
{
    private static readonly string[] Keywords =
    {
        "Sheet", "Layout", "Attribute", "Block", "Database", "Dst", "Document", "Transaction"
    };

    public static string Run(string outputPath)
    {
        var sb = new StringBuilder();
        sb.AppendLine("Navigator Kit SDK probe");
        sb.AppendLine("GeneratedAtUtc: " + DateTime.UtcNow.ToString("O"));
        sb.AppendLine("Runtime: " + System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription);
        sb.AppendLine("WARNING: this is a discovery dump, not an API contract.");
        sb.AppendLine();

        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies()
                     .OrderBy(a => a.GetName().Name, StringComparer.OrdinalIgnoreCase))
        {
            Type[] types;
            try { types = asm.GetTypes(); }
            catch (ReflectionTypeLoadException ex) { types = ex.Types.Where(t => t != null).Cast<Type>().ToArray(); }
            catch { continue; }

            foreach (var type in types.Where(t => t != null && t.IsPublic)
                         .OrderBy(t => t.FullName, StringComparer.OrdinalIgnoreCase))
            {
                var lines = new List<string>();
                try
                {
                    foreach (var method in type.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static))
                    {
                        if (!Keywords.Any(k => method.Name.IndexOf(k, StringComparison.OrdinalIgnoreCase) >= 0)) continue;
                        var parameters = string.Join(", ", method.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name));
                        lines.Add("    METHOD " + method.ReturnType.Name + " " + method.Name + "(" + parameters + ")");
                    }
                    foreach (var property in type.GetProperties(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static))
                    {
                        if (!Keywords.Any(k => property.Name.IndexOf(k, StringComparison.OrdinalIgnoreCase) >= 0)) continue;
                        lines.Add("    PROPERTY " + property.PropertyType.Name + " " + property.Name);
                    }
                }
                catch { continue; }
                if (lines.Count == 0) continue;
                sb.AppendLine("ASSEMBLY " + asm.GetName().Name);
                sb.AppendLine("  TYPE " + type.FullName);
                foreach (var line in lines.Take(200)) sb.AppendLine(line);
                sb.AppendLine();
            }
        }
        File.WriteAllText(outputPath, sb.ToString(), Encoding.UTF8);
        return outputPath;
    }
}
