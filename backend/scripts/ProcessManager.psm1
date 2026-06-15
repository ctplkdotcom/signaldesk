# ProcessManager.psm1
#
# Reusable module for safe server lifecycle management on Windows.
#
# Defences:
#   D1. Port-based kill before start — free target port before binding
#   D2. PID tracking — capture process object, validate immediately
#   D3. Health-check loop with deadline — poll URL, don't assume
#   D4. Finally-block cleanup — always kill, never leak
#   D5. Single-server invariant — kill all matching processes before start
#   D6. Stderr log inspection — print logs on failure, not just "timeout"

$Script:Processes = @{}  # tag -> @{proc; outFile; errFile}

function Set-CleanPort {
    <#
    .SYNOPSIS
    Kill any process with a TCP connection (any state) on the given port.
    Handles Listen, Established, FinWait2, TimeWait, CloseWait, etc.
    #>
    param([int]$Port)
    try {
        Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique |
            Where-Object { $_ -gt 0 } |
            ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
    } catch {}
}

function Start-ManagedProcess {
    <#
    .SYNOPSIS
    Start a process, track it, and wait for a health-check URL to respond.
    .PARAMETER Tag
    Unique label (e.g. "backend", "frontend").
    .PARAMETER FilePath
    Full path to executable (e.g. "python", "C:\path\to\npx.cmd").
    .PARAMETER ArgumentList
    Arguments as an array.
    .PARAMETER WorkingDirectory
    Working directory for the process.
    .PARAMETER Port
    Port to free before starting.
    .PARAMETER HealthUrl
    URL to poll for readiness.
    .PARAMETER HealthTimeoutSec
    Maximum seconds to wait for health check.
    .OUTPUTS
    System.Diagnostics.Process object. Throws on failure.
    #>
    param(
        [string]$Tag,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [int]$Port,
        [string]$HealthUrl,
        [int]$HealthTimeoutSec = 30
    )

    # D1: Free the target port
    Set-CleanPort -Port $Port
    Start-Sleep -Seconds 1

    $outFile = Join-Path $env:TEMP "sd_${Tag}_out.log"
    $errFile = Join-Path $env:TEMP "sd_${Tag}_err.log"
    Remove-Item $outFile, $errFile -Force -ErrorAction SilentlyContinue

    $proc = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory -PassThru -NoNewWindow `
        -RedirectStandardOutput $outFile -RedirectStandardError $errFile

    # D2: Validate process started
    if (-not $proc -or $proc.HasExited -or $proc.Id -le 0) {
        $log = "no process object"
        if (Test-Path $errFile) { $log = Get-Content $errFile -Tail 10 -ErrorAction SilentlyContinue }
        throw "Start-ManagedProcess: '$Tag' failed to start. STDERR: $log"
    }

    $Script:Processes[$Tag] = @{ proc = $proc; outFile = $outFile; errFile = $errFile }

    # D3: Health-check loop
    $deadline = (Get-Date).AddSeconds($HealthTimeoutSec)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-RestMethod -Uri $HealthUrl -ErrorAction Stop
            $ready = $true
            break
        } catch {
            if ($proc.HasExited) {
                $log = Get-Content $errFile -Tail 20 -ErrorAction SilentlyContinue
                throw "Start-ManagedProcess: '$Tag' (PID $($proc.Id)) exited before ready. STDERR: $log"
            }
            Start-Sleep -Milliseconds 500
        }
    }

    if (-not $ready) {
        Write-ProcessLogs -Tag $Tag
        throw "Start-ManagedProcess: '$Tag' (PID $($proc.Id)) not ready within ${HealthTimeoutSec}s."
    }

    return $proc
}

function Wait-HttpReady {
    <#
    .SYNOPSIS
    Poll a URL until it responds or timeout is reached.
    .OUTPUTS
    bool — $true if the URL responded within the timeout.
    #>
    param(
        [string]$Url,
        [int]$TimeoutSec = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $null = Invoke-RestMethod -Uri $Url -ErrorAction Stop
            return $true
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    return $false
}

function Stop-ManagedProcess {
    <#
    .SYNOPSIS
    Kill a tracked process by tag. Recursively terminates children.
    #>
    param([string]$Tag)
    $entry = $Script:Processes[$Tag]
    if (-not $entry) { return }
    try {
        $children = Get-CimInstance -ClassName Win32_Process -Filter "ParentProcessId=$($entry.proc.Id)" -ErrorAction SilentlyContinue
        foreach ($c in $children) {
            Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue
        }
        Stop-Process -Id $entry.proc.Id -Force -ErrorAction SilentlyContinue
    } catch {}
    $Script:Processes.Remove($Tag)
}

function Stop-AllProcesses {
    <#
    .SYNOPSIS
    Kill every tracked process. Then clean up any remaining python/node processes
    (frontend can spawn child node processes not caught by parent-child tree kill).
    #>
    $tags = @($Script:Processes.Keys)
    foreach ($t in $tags) { Stop-ManagedProcess -Tag $t }

    # Safety net: kill any orphaned node/python processes
    Start-Sleep -Milliseconds 500
    Get-Process -Name "node","python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

function Write-ProcessLogs {
    <#
    .SYNOPSIS
    Print stdout and stderr for a tracked process.
    #>
    param([string]$Tag, [int]$Lines = 80)
    $entry = $Script:Processes[$Tag]
    if (-not $entry) {
        Write-Output "===== $Tag LOGS (not tracked) ====="
        return
    }
    Write-Output "===== $Tag STDOUT ====="
    if (Test-Path $entry.outFile) { Get-Content $entry.outFile -Tail $Lines -ErrorAction SilentlyContinue } else { Write-Output "(no stdout file)" }
    Write-Output "===== $Tag STDERR ====="
    if (Test-Path $entry.errFile) { Get-Content $entry.errFile -Tail $Lines -ErrorAction SilentlyContinue } else { Write-Output "(no stderr file)" }
}

function Assert-ProcessStarted {
    <#
    .SYNOPSIS
    Validate a process object is alive and has a valid PID. Throws on failure.
    #>
    param([System.Diagnostics.Process]$Process, [string]$Label)
    if (-not $Process) { throw "Assert-ProcessStarted: $Label — process object is null" }
    if ($Process.HasExited) { throw "Assert-ProcessStarted: $Label (PID $($Process.Id)) has already exited" }
    if ($Process.Id -le 0) { throw "Assert-ProcessStarted: $Label — invalid PID ($($Process.Id))" }
}

Export-ModuleMember -Function Set-CleanPort, Start-ManagedProcess, Wait-HttpReady, Stop-ManagedProcess, Stop-AllProcesses, Write-ProcessLogs, Assert-ProcessStarted
