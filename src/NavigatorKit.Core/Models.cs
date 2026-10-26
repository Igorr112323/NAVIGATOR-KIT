#nullable enable
using System;
using System.Collections.Generic;

namespace NavigatorKit.Core;

public sealed class SheetRecord
{
    public string File { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public string SourceFormat { get; set; } = "DXF R2010";
    public string SourceType { get; set; } = "SYNTHETIC_FIXTURE_NOT_DWG";
    public string SourceSha256 { get; set; } = string.Empty;
    public int Sequence { get; set; }
    public string Mark { get; set; } = string.Empty;
    public string DocDesignation { get; set; } = string.Empty;
    public string SheetNo { get; set; } = string.Empty;
    public int? SheetNoNumeric { get; set; }
    public string SheetName { get; set; } = string.Empty;
    public string Format { get; set; } = string.Empty;
    public string Revision { get; set; } = string.Empty;
    public string Layout { get; set; } = string.Empty;
    public string ProfileId { get; set; } = string.Empty;
    public string BlockName { get; set; } = string.Empty;
    public string ProfileStatus { get; set; } = string.Empty;
    public Dictionary<string, string> StampAttributes { get; set; } = new(StringComparer.OrdinalIgnoreCase);
}

public sealed class StampTemplate
{
    public string Id { get; set; } = string.Empty;
    public string BlockName { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public Dictionary<string, string> TagToField { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public List<string> RequiredFields { get; set; } = new();
}

public sealed class ValidationIssue
{
    public string IssueId { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
    public string Severity { get; set; } = string.Empty;
    public string Mark { get; set; } = string.Empty;
    public string SheetNo { get; set; } = string.Empty;
    public string File { get; set; } = string.Empty;
    public string Field { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string Suggestion { get; set; } = string.Empty;
}

public sealed class DuplicateRecord
{
    public string Mark { get; set; } = string.Empty;
    public int SheetNo { get; set; }
    public int Count { get; set; }
    public string Files { get; set; } = string.Empty;
    public string Keeper { get; set; } = string.Empty;
    public string ToChange { get; set; } = string.Empty;
    public string Recommendation { get; set; } = string.Empty;
}

public sealed class NumberingAction
{
    public string Mark { get; set; } = string.Empty;
    public string File { get; set; } = string.Empty;
    public string OldSheetNo { get; set; } = string.Empty;
    public string MinimalNewNo { get; set; } = string.Empty;
    public string FullShiftNewNo { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string RequiresApproval { get; set; } = string.Empty;
    public string Recommendation { get; set; } = string.Empty;
}

public sealed class NumberingResult
{
    public List<DuplicateRecord> Duplicates { get; set; } = new();
    public List<NumberingAction> Plan { get; set; } = new();
}
