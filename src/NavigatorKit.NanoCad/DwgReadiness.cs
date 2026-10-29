#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;

namespace NavigatorKit.NanoCad;

/// <summary>
/// Честный чек-лист готовности к чтению production DWG.
/// Намеренно НЕ вызывает Database/Transaction/BlockReference: их сигнатуры в
/// MultiCAD .NET SDK 26 не подтверждены. Класс компилируется без CAD-ссылок.
/// </summary>
public static class DwgReadiness
{
    public static IReadOnlyList<string> RequiredApiChecks => new[]
    {
        "Подтвердить TargetFramework и разрядность SDK 26",
        "Подтвердить фактические DLL: mapimgd/hostmgd/hostdbmgd или их аналоги",
        "Проверить фоновое открытие Database без открытия документа в редакторе",
        "Проверить Transaction и чтение BlockReference/AttributeReference",
        "Проверить запись атрибутов штампа и rollback через .bak + SHA-256",
        "Проверить Tables API и документированный доступ к SHEETSET/.dst"
    };

    public static IReadOnlyList<string> RequiredDataChecks => new[]
    {
        "3 × 40 реальных DWG с известными блоками основной надписи",
        "Два реальных XML-профиля маппинга атрибутов",
        "Реестр листов с SHA-256 исходных файлов",
        "Контроль комплектности: пустые поля, форматы, дубли, пропуски",
        "Обратимая правка штампа на копиях и проверка rollback",
        "Синхронизация print_order.json с layouts"
    };

    public static DwgReadinessReport CreateReport(bool sdkProbeCompleted, bool realDwgAvailable)
    {
        var verified = sdkProbeCompleted && realDwgAvailable;
        return new DwgReadinessReport
        {
            SessionId = "night-session-20261028",
            Status = verified ? "READY_FOR_PILOT" : "EXTERNAL_DEPENDENCY",
            SdkProbeCompleted = sdkProbeCompleted,
            RealDwgAvailable = realDwgAvailable,
            NanoCadApiCalled = false,
            HypothesisMarker = "ГИПОТЕЗА/ПРОВЕРИТЬ",
            RequiredApiChecks = RequiredApiChecks.ToArray(),
            RequiredDataChecks = RequiredDataChecks.ToArray(),
            Note = verified
                ? "Пилот можно начинать только после нормоконтроля и бэкапа."
                : "Нет Windows/nanoCAD 26/SDK/license/реальных DWG; фоновое чтение не выполнялось."
        };
    }
}

public sealed class DwgReadinessReport
{
    public string SessionId { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public bool SdkProbeCompleted { get; set; }
    public bool RealDwgAvailable { get; set; }
    public bool NanoCadApiCalled { get; set; }
    public string HypothesisMarker { get; set; } = string.Empty;
    public string[] RequiredApiChecks { get; set; } = Array.Empty<string>();
    public string[] RequiredDataChecks { get; set; } = Array.Empty<string>();
    public string Note { get; set; } = string.Empty;
}
