param([string]$OutputDirectory = (Join-Path $PSScriptRoot 'evidence'))
$ErrorActionPreference = 'Stop'
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$runDirectory = Join-Path $OutputDirectory ('inventory-' + $stamp)
New-Item -ItemType Directory -Force -Path $runDirectory | Out-Null
$issues = New-Object System.Collections.Generic.List[string]
function Read-Cim($ClassName) {
    try { return Get-CimInstance -ClassName $ClassName } catch {
        $issues.Add($ClassName + ': ' + $_.Exception.Message)
        return $null
    }
}
$computer = Read-Cim 'Win32_ComputerSystem'
$osInfo = Read-Cim 'Win32_OperatingSystem'
$processors = @(Read-Cim 'Win32_Processor' | Select-Object Name, Architecture, NumberOfCores, NumberOfLogicalProcessors)
$drivers = @(Read-Cim 'Win32_PnPSignedDriver' |
    Where-Object { $_.DeviceName -match 'Hexagon|Qualcomm|NPU|HTP|Neural' } |
    Select-Object DeviceName, Manufacturer, DriverVersion, DriverDate, InfName)
$display = @(Read-Cim 'Win32_VideoController' | Select-Object Name, DriverVersion)
$build = $null
try { $build = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' |
    Select-Object DisplayVersion, CurrentBuild, UBR } catch { $issues.Add('Windows build registry unavailable') }
$powerScheme = $null
try { $powerScheme = ((& powercfg.exe /GETACTIVESCHEME) -join '\n') } catch { $issues.Add('powercfg query unavailable') }
$pythonCommands = @(Get-Command python.exe, python3.exe, py.exe -All -ErrorAction SilentlyContinue |
    ForEach-Object { [ordered]@{ name=$_.Name; path=$_.Source.Replace($env:USERPROFILE, '%USERPROFILE%') } })
$runtimeFiles = @()
$localRuntime = Join-Path $PSScriptRoot 'runtime'
if (Test-Path $localRuntime) {
    $runtimeFiles = @(Get-ChildItem $localRuntime -Recurse -File |
        Where-Object { $_.Name -match '^(python.*\.(exe|dll)|Qnn.*\.dll|onnxruntime.*\.(dll|pyd))$' } |
        ForEach-Object { [ordered]@{
            path=$_.FullName.Substring($PSScriptRoot.Length).TrimStart('\');
            sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();
            file_version=$_.VersionInfo.FileVersion
        } })
}
$report = [ordered]@{
    schema=1; collected_utc=[DateTime]::UtcNow.ToString('o');
    manufacturer=$computer.Manufacturer; model=$computer.Model;
    system_type=$computer.SystemType; ram_bytes=$computer.TotalPhysicalMemory;
    windows=[ordered]@{ caption=$osInfo.Caption; version=$osInfo.Version; build=$osInfo.BuildNumber;
        os_architecture=$osInfo.OSArchitecture; release=$build };
    processors=$processors; accelerator_related_drivers=$drivers; graphics=$display;
    powershell_version=$PSVersionTable.PSVersion.ToString();
    process_architecture=$env:PROCESSOR_ARCHITECTURE;
    native_architecture_hint=$env:PROCESSOR_ARCHITEW6432;
    power_scheme=$powerScheme; python_commands=$pythonCommands; local_runtime_files=$runtimeFiles;
    errors=@($issues.ToArray()); inference_performed=$false; npu_verified=$false;
    scope='Read-only inventory apart from this output folder. No serial, hostname, account, network, screen, camera or microphone collection. No installs, downloads or policy changes.'
}
$report | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $runDirectory 'inventory.json')
Write-Output ('Saved ' + $runDirectory + '\inventory.json')
Write-Output 'Return inventory.json to the participant. No inference or NPU verification occurred.'
