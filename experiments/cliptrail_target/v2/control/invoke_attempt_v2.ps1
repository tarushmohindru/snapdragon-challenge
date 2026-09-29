param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$exitCode = 2
$record = [ordered]@{ schema=2; started_utc=[DateTime]::UtcNow.ToString('o');
    stage='inventory'; native_process_started=$false; native_exit_code=$null;
    native_exit_code_hex=$null; automatic_retries=$false; npu_verified=$false }
$recordFile = Join-Path $RunDirectory 'native-child.json'
function Save-Record {
    $record | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -LiteralPath $recordFile
}
try {
    Save-Record
    & (Join-Path $root 'collect_inventory.ps1') -OutputDirectory $RunDirectory
    $record.stage = 'native_python_launch'
    Save-Record
    $python = Join-Path $root 'runtime\python.exe'
    $arguments = @('-u', '-X', 'faulthandler', '"run_smoke.py"', '--bundle', ('"{0}"' -f $root),
        '--output', ('"{0}"' -f $RunDirectory), '--ticket', ('"{0}"' -f (Join-Path $RunDirectory 'attempt-ticket.json')))
    $native = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $root -PassThru -NoNewWindow `
        -RedirectStandardOutput (Join-Path $RunDirectory 'python.stdout.log') `
        -RedirectStandardError (Join-Path $RunDirectory 'python.stderr.log')
    $null = $native.Handle
    $record.native_process_started = $true
    $record.native_pid = $native.Id
    $record.stage = 'native_python_running'
    Save-Record
    # The parent supervisor caps this whole process tree, including inventory.
    $native.WaitForExit()
    $exitCode = [int]$native.ExitCode
    $record.native_exit_code = $exitCode
    $record.native_exit_code_hex = $exitCode.ToString('X8')
    $record.stage = 'native_python_exited'
} catch {
    $record.error = ($_ | Out-String)
    $record.failed_stage = $record.stage
    Write-Output $record.error
} finally {
    $record.finished_utc = [DateTime]::UtcNow.ToString('o')
    Save-Record
}
exit $exitCode
