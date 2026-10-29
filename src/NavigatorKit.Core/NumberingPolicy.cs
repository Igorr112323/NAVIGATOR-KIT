#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;

namespace NavigatorKit.Core;

public static class NumberingPolicy
{
    private static readonly string[] MarkOrder = { "АР", "КР", "ОВ" };

    public static NumberingResult Build(IReadOnlyList<SheetRecord> sheets)
    {
        var result = new NumberingResult();
        var duplicateGroups = sheets.Where(s => s.SheetNoNumeric.HasValue)
            .GroupBy(s => (s.Mark, Number: s.SheetNoNumeric!.Value))
            .Where(g => g.Count() > 1)
            .OrderBy(g => g.Key.Mark).ThenBy(g => g.Key.Number)
            .ToList();
        var changeFiles = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var g in duplicateGroups)
        {
            var group = g.OrderBy(x => x.Sequence).ThenBy(x => x.File, StringComparer.Ordinal).ToList();
            var keeper = group[0];
            var toChange = group.Skip(1).ToList();
            foreach (var s in toChange) changeFiles.Add(s.File);
            result.Duplicates.Add(new DuplicateRecord
            {
                Mark = g.Key.Mark,
                SheetNo = g.Key.Number,
                Count = group.Count,
                Files = string.Join("; ", group.Select(x => x.File)),
                Keeper = keeper.File,
                ToChange = string.Join("; ", toChange.Select(x => x.File)),
                Recommendation = "Рекомендуется full_shift; minimal patch оставляет пропуски."
            });
        }

        foreach (var mark in MarkOrder.Concat(sheets.Select(s => s.Mark).Distinct().Except(MarkOrder)))
        {
            var group = sheets.Where(s => s.Mark == mark)
                .OrderBy(s => s.Sequence).ThenBy(s => s.File, StringComparer.Ordinal).ToList();
            if (group.Count == 0) continue;
            var numeric = group.Where(s => s.SheetNoNumeric.HasValue).Select(s => s.SheetNoNumeric!.Value).ToHashSet();
            var used = new HashSet<int>(numeric);
            var tail = (numeric.Count > 0 ? numeric.Max() : 0) + 1;
            var index = 0;
            foreach (var s in group)
            {
                index++;
                var full = index.ToString();
                string minimal;
                if (changeFiles.Contains(s.File))
                {
                    while (used.Contains(tail)) tail++;
                    minimal = tail.ToString();
                    used.Add(tail);
                    tail++;
                }
                else
                {
                    minimal = int.TryParse(s.SheetNo, out _) ? s.SheetNo : string.Empty;
                }
                var action = minimal == s.SheetNo && full == s.SheetNo ? "KEEP" : "CHANGE_REQUIRED";
                result.Plan.Add(new NumberingAction
                {
                    Mark = mark,
                    File = s.File,
                    OldSheetNo = s.SheetNo,
                    MinimalNewNo = minimal,
                    FullShiftNewNo = full,
                    Action = action,
                    RequiresApproval = action == "KEEP" ? "NO" : "YES",
                    Recommendation = result.Duplicates.Count > 0 ? "FULL_SHIFT" : "NO_CHANGE"
                });
            }
        }
        return result;
    }
}
