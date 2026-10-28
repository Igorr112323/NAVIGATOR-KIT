# Windows stand readiness check for Navigator Kit.
# Does NOT install nanoCAD, bypass licensing, or call unverified SDK APIs.
param(
    [string]$NanoCadPath = "C:\Program Files\Nanosoft\nanoCAD x64 26",
    [string]$SdkPath = "C:\SDK\nanoCAD26",
    [string]$LicenseStatus = "UNKNOWN",
    [string]$Output = "delivery/data/windows_stand_check.json"
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $root

function Test-PathSafe([string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return $false }
    return Test-Path -LiteralPath $p
}

function Get-CommandVersion([string]$name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { return "MISSING" }
    try {
        return (& $name --version 2>&1 | Select-Object -First 1).ToString()
    } catch {
        return $cmd.Source
    }
}

$nanoCadExe = Join-Path $NanoCadPath "nanoCAD.exe"
$sdkDllCandidates = @(
    (Join-Path $SdkPath "bin\mapimgd.dll"),
    (Join-Path $SdkPath "bin\hostmgd.dll"),
    (Join-Path $SdkPath "bin\hostdbmgd.dll")
)
$foundDlls = @($sdkDllCandidates | Where-Object { Test-PathSafe $_ })
$licenseOk = $LicenseStatus.ToUpperInvariant() -eq "ACTIVE"

$report = [ordered]@{
    format = "navigator-kit.windows-stand-check/v1"
    sessionId = "night-session-20261028"
    generatedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    hostOS = [System.Environment]::OSVersion.VersionString
    nanoCAD26Installed = (Test-PathSafe $nanoCadExe)
    nanoCADPath = $NanoCadPath
    nanoCADExeFound = (Test-PathSafe $nanoCadExe)
    licenseStatus = $LicenseStatus
    licenseActive = $licenseOk
    sdkPath = $SdkPath
    sdkPathFound = (Test-PathSafe $SdkPath)
    sdkDllsFound = $foundDlls
    sdkDllNamesAreHypothesis = $true
    dotnet = (Get-CommandVersion "dotnet")
    git = (Get-CommandVersion "git")
    gh = (Get-CommandVersion "gh")
    workflow = ".github/workflows/windows-build.yml"
    nextCommands = @(
        "dotnet build src/NavigatorKit.NanoCad/NavigatorKit.NanoCad.csproj -c Release -p:NANOCAD_SDK_PATH=<SDK>",
        "NETLOAD NavigatorKit.NanoCad.dll",
        "NK_HELLO",
        "SDK_PROBE"
    )
    nanoCADExecuted = $false
    screenshotsCaptured = $false
    status = "PREPARED_NOT_EXECUTED"
    note = "This script only checks paths. Real SDK API names and TFM remain ГИПОТЕЗА/ПРОВЕРИТЬ."
}

$outPath = Join-Path $root $Output
$outDir = Split-Path -Parent $outPath
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $outPath -Encoding UTF8

Pop-Location
Write-Host "Windows stand check written to $outPath"
if (-not $report.nanoCAD26Installed -or -not $licenseOk -or $foundDlls.Count -eq 0) {
    Write-Warning "Stand is not ready: nanoCAD/license/SDK DLLs missing. Mark as ГИПОТЕЗА/ПРОВЕРИТЬ."
    exit 2
}
Write-Host "Stand paths look ready. Run NK_HELLO and SDK_PROBE inside nanoCAD to verify APIs."
exit 0
