[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PythonArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$bootstrapScript = Join-Path $scriptDir "bootstrap_repo_python.ps1"

$candidates = @(
    @{
        Label = "repo virtual environment"
        Path = Join-Path $repoRoot ".venv\Scripts\python.exe"
    },
    @{
        Label = "repo-local base interpreter"
        Path = Join-Path $repoRoot ".python\python.exe"
    }
)

foreach ($candidate in $candidates) {
    if (-not (Test-Path -LiteralPath $candidate.Path -PathType Leaf)) {
        continue
    }

    $canRun = $false
    try {
        & $candidate.Path --version *> $null
        $canRun = ($LASTEXITCODE -eq 0)
    }
    catch {
        $canRun = $false
    }

    if ($canRun) {
        & $candidate.Path @PythonArgs
        exit $LASTEXITCODE
    }
}

$message = @"
No runnable repo-local Python was found.

This repository's current .venv likely points to a host Python install outside the workspace.
That works in a normal shell, but sandboxed runs cannot access that base interpreter.

Bootstrap a repo-local Python copy first:
  powershell -NoProfile -ExecutionPolicy Bypass -File "$bootstrapScript" -BasePython "<path-to-python.exe>"

After that, run Python through:
  .\scripts\python.cmd <args>
"@

Write-Error $message
exit 1
