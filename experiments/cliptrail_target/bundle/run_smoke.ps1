param([int]$TimeoutSeconds = 600)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$run = Join-Path $root ('evidence\smoke-' + $stamp)
New-Item -ItemType Directory -Force -Path $run | Out-Null
& (Join-Path $root 'collect_inventory.ps1') -OutputDirectory $run
$python = Join-Path $root 'runtime\python.exe'
if (-not (Test-Path $python)) { throw 'Missing private ARM64 runtime; return this error and the inventory.' }
$arguments = @('"run_smoke.py"', '--bundle', ('"{0}"' -f $root), '--output', ('"{0}"' -f $run))
$process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $root -PassThru `
    -RedirectStandardOutput (Join-Path $run 'stdout.log') -RedirectStandardError (Join-Path $run 'stderr.log')
$timedOut = -not $process.WaitForExit($TimeoutSeconds * 1000)
if ($timedOut) { $process.Kill(); $process.WaitForExit() }
$outer = [ordered]@{ schema=1; timeout_seconds=$TimeoutSeconds; timed_out=$timedOut;
    exit_code=$process.ExitCode; npu_verified=$false; note='Inspect raw evidence; exit code/provider registration alone is not NPU proof.' }
$outer | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $run 'launcher.json')
$resultZip = $run + '.zip'
Compress-Archive -Path (Join-Path $run '*') -DestinationPath $resultZip
Write-Output ('Return evidence zip: ' + $resultZip)
Write-Output 'No system software, execution policy, driver or account settings were changed.'
Write-Output 'This is a one-image diagnostic. No indexing benchmark has run.'
