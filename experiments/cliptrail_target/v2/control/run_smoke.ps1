[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$limitSeconds = 600
$authorizationId = 'cliptrail-htp-v2-asus-x2e88100-one-attempt'
$startedUtc = [DateTime]::UtcNow
$watch = [Diagnostics.Stopwatch]::StartNew()
$root = $PSScriptRoot
$stamp = $startedUtc.ToString('yyyyMMddTHHmmssfffZ')
$token = [Guid]::NewGuid().ToString('N')
$run = Join-Path $root ('evidence\smoke-v2-' + $stamp + '-' + $token.Substring(0,8))
New-Item -ItemType Directory -Path $run | Out-Null
$logPath = Join-Path $run 'supervisor.log'
function Log-Line([string]$Message) {
    $line = [DateTime]::UtcNow.ToString('o') + ' ' + $Message
    Add-Content -Encoding UTF8 -LiteralPath $logPath -Value $line
    Write-Output $line
}
$process = $null
$terminationSent = $false
$exitCode = 2
$outcome = [ordered]@{ schema=2; version='v2'; authorization_id=$authorizationId;
    explicit_extension_after_v1_cutoff=$true; started_utc=$startedUtc.ToString('o');
    status='PREPARING'; timeout_seconds=$limitSeconds; max_attempts=1;
    automatic_retries=$false; attempt_claimed=$false; child_started=$false;
    timed_out=$false; child_exit_code=$null; child_exit_code_hex=$null;
    native_exit_code=$null; native_exit_code_hex=$null;
    termination_requested=$false; termination_confirmed=$null;
    native_execution_status='unknown'; htp_verification='unverified'; npu_verified=$false;
    embedding_parity=$null; stage_results=@{}; runtime_observed=@{};
    systems_benchmark_started=$false; review_required=$true }
function Stop-Attempt {
    if ($null -eq $process -or $process.HasExited -or $script:terminationSent) { return }
    $script:terminationSent = $true
    $outcome.termination_requested = $true
    $outcome.termination_requested_utc = [DateTime]::UtcNow.ToString('o')
    # End only this attempt's PowerShell/Python process tree. Never restart it.
    & (Join-Path $env:SystemRoot 'System32\taskkill.exe') /PID $process.Id /T /F *> (Join-Path $run 'termination.log')
    $outcome.termination_command_exit_code = $LASTEXITCODE
    $outcome.termination_confirmed = $process.WaitForExit(5000)
}
try {
    Log-Line 'v2: exactly one attempt, ten-minute cap including inventory and native initialization. No automatic retries.'
    $manifestPath = Join-Path $root 'bundle-manifest.json'
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    $auth = $manifest.authorization
    if ($manifest.schema -ne 2 -or $auth.authorization_id -ne $authorizationId -or
        $auth.max_native_attempts -ne 1 -or $auth.attempt_wall_timeout_seconds -ne 600 -or
        $auth.automatic_retries -ne $false -or $auth.explicit_extension_after_v1_cutoff -ne $true) {
        throw 'Manifest does not authorize this exact v2 one-attempt protocol.'
    }
    $outcome.manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash.ToLowerInvariant()
    $guardDirectory = Join-Path $env:LOCALAPPDATA ('ClipTrail\' + $authorizationId)
    [IO.Directory]::CreateDirectory($guardDirectory) | Out-Null
    $guardPath = Join-Path $guardDirectory 'attempt.json'
    $ticket = [ordered]@{ schema=2; authorization_id=$authorizationId; token=$token;
        started_utc=$startedUtc.ToString('o'); timeout_seconds=600;
        bundle_directory=$root; output_directory=$run; supervisor_pid=$PID;
        manifest_sha256=$outcome.manifest_sha256 }
    $ticketJson = $ticket | ConvertTo-Json -Depth 5
    $bytes = [Text.Encoding]::UTF8.GetBytes($ticketJson)
    # CreateNew is atomic. This marker is never removed on success/failure/timeout.
    try {
        $guardFile = [IO.File]::Open($guardPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    } catch {
        if (Test-Path -LiteralPath $guardPath) {
            $outcome.status = 'ATTEMPT_ALREADY_CONSUMED'
            $exitCode = 9
        }
        throw
    }
    try { $guardFile.Write($bytes,0,$bytes.Length) } finally { $guardFile.Dispose() }
    $outcome.attempt_claimed = $true
    $localGuard = [IO.File]::Open((Join-Path $root 'attempt-used-v2.json'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $localGuard.Write($bytes,0,$bytes.Length) } finally { $localGuard.Dispose() }
    [IO.File]::WriteAllBytes((Join-Path $run 'attempt-ticket.json'),$bytes)
    Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $run 'bundle-manifest-v2.json')
    Copy-Item -LiteralPath (Join-Path $root 'authorization-v2.json') -Destination $run
    $outcome.status = 'ATTEMPT_RUNNING'
    $outcome | ConvertTo-Json -Depth 16 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $run 'smoke-outcome-v2.json')
    if ($watch.Elapsed.TotalSeconds -ge $limitSeconds) { throw 'Attempt budget exhausted before child launch.' }
    $powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = @('-NoProfile','-NonInteractive','-File','"invoke_attempt_v2.ps1"', '-RunDirectory', ('"{0}"' -f $run))
    $process = Start-Process -FilePath $powershell -ArgumentList $arguments -WorkingDirectory $root -PassThru -NoNewWindow `
        -RedirectStandardOutput (Join-Path $run 'attempt.stdout.log') `
        -RedirectStandardError (Join-Path $run 'attempt.stderr.log')
    $null = $process.Handle
    $outcome.child_started = $true
    $outcome.child_pid = $process.Id
    Log-Line 'Attempt claimed. Collecting inventory and running the fixed CPU check plus one QNN inference; please wait.'
    $remainingMs = [Math]::Max(0,[Math]::Floor(($limitSeconds - $watch.Elapsed.TotalSeconds)*1000))
    if (-not $process.WaitForExit([int]$remainingMs)) {
        $outcome.timed_out = $true
        Stop-Attempt
        $outcome.status = 'TIMED_OUT'
        $exitCode = 124
    } else {
        $exitCode = [int]$process.ExitCode
        $outcome.status = 'CHILD_EXITED'
    }
} catch {
    $outcome.supervisor_error = ($_ | Out-String)
    if ($outcome.status -ne 'ATTEMPT_ALREADY_CONSUMED') { $outcome.status = 'SUPERVISOR_FAILED' }
    Log-Line $outcome.supervisor_error
} finally {
    if ($null -ne $process) {
        try {
            Stop-Attempt
            if ($process.HasExited) {
                # Process execution has ended. Drain async redirected output before
                # hashing/packing logs; this is evidence capture, not another attempt.
                $process.WaitForExit()
                $outcome.child_exit_code = [int]$process.ExitCode
                $outcome.child_exit_code_hex = ([int]$process.ExitCode).ToString('X8')
            }
        } catch { $outcome.termination_error = ($_ | Out-String) }
    }
    $watch.Stop()
    $outcome.attempt_finished_utc = [DateTime]::UtcNow.ToString('o')
    $outcome.attempt_elapsed_ms = $watch.Elapsed.TotalMilliseconds
    try {
        $nativePath = Join-Path $run 'native-child.json'
        if (Test-Path -LiteralPath $nativePath) {
            $child = Get-Content -Raw -LiteralPath $nativePath | ConvertFrom-Json
            $outcome.native_exit_code = $child.native_exit_code
            $outcome.native_exit_code_hex = $child.native_exit_code_hex
            $outcome.last_child_stage = $child.stage
        }
        $smokePath = Join-Path $run 'smoke.json'
        if (Test-Path -LiteralPath $smokePath) {
            $smoke = Get-Content -Raw -LiteralPath $smokePath | ConvertFrom-Json
            $outcome.native_execution_status = $smoke.status
            $outcome.last_native_stage = $smoke.stage
            $outcome.failed_native_stage = $smoke.failed_stage
            $outcome.stage_results = $smoke.stage_results
            $outcome.runtime_observed = $smoke.runtime
            $outcome.embedding_parity = $smoke.qnn_vs_frozen
            $outcome.reported_provider_information = $smoke.session_providers
            $outcome.qnn_embedding_sha256 = $smoke.qnn_embedding_sha256
            $outcome.automated_evidence_checks = $smoke.verification
            if ($outcome.status -eq 'CHILD_EXITED') { $outcome.status = $smoke.status }
        }
    } catch { $outcome.report_read_error = ($_ | Out-String) }
    # Evidence capture is allowed after compute termination; it never starts inference.
    $outcome.return_code = $exitCode
    $outcome | ConvertTo-Json -Depth 24 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $run 'smoke-outcome-v2.json')
    Log-Line ('Stopped: ' + $outcome.status + '. Do not run again. HTP evidence requires review.')
    try {
        $hashes = [ordered]@{}
        Get-ChildItem -LiteralPath $run -Recurse -File | ForEach-Object {
            $relative = $_.FullName.Substring($run.Length).TrimStart('\')
            $hashes[$relative] = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
        }
        $hashes | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $run 'evidence-hashes-v2.json')
        $resultZip = $run + '.zip'
        Compress-Archive -Path (Join-Path $run '*') -DestinationPath $resultZip
        Write-Output ('Return this evidence ZIP, including any failure: ' + $resultZip)
    } catch {
        ($_ | Out-String) | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $run 'packaging-error.txt')
        Write-Output ('Evidence packaging failed. Return this folder; do not rerun inference: ' + $run)
    }
}
exit $exitCode
