#nullable enable
using System;
using System.IO;
#if NANOCAD_SDK
using Multicad.Runtime;
#endif

namespace NavigatorKit.NanoCad;

public static class HostInfo
{
    public const string Hello = "Комплект-Навигатор: Hello World. MultiCAD SDK integration is a hypothesis until verified.";
    public const string IntegrationStatus = "ГИПОТЕЗА/ПРОВЕРИТЬ";
}

#if NANOCAD_SDK
/// <summary>
/// ГИПОТЕЗА/ПРОВЕРИТЬ: пространство имён Multicad.Runtime и атрибут CommandMethod
/// основаны на публичных примерах более ранних версий. Для SDK 26 подтвердить через SdkProbe.
/// </summary>
public static class NanoCadCommands
{
    [CommandMethod("NK_HELLO")]
    public static void HelloWorld()
    {
        Console.WriteLine(HostInfo.Hello);
    }

    [CommandMethod("NK_SDK_PROBE")]
    public static void Probe()
    {
        var path = Path.Combine(Path.GetTempPath(), "navigator-kit-sdk-probe.txt");
        SdkProbe.Run(path);
        Console.WriteLine("Navigator Kit SDK probe: " + path);
    }
}
#else
public static class NanoCadCommandsStub
{
    public static string BuildWithoutSdk() => HostInfo.IntegrationStatus + ": compile with NANOCAD_SDK_PATH and NanoCadSdkReferences.props.";
}
#endif
