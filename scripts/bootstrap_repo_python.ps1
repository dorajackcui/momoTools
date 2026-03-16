[CmdletBinding()]
param(
    [string]$BasePython,
    [switch]$InstallRequirements
)

$ErrorActionPreference = "Stop"

function Resolve-BasePythonPath {
    param(
        [string]$RequestedPath
    )

    if ($RequestedPath) {
        if (-not (Test-Path -LiteralPath $RequestedPath -PathType Leaf)) {
            throw "Base Python was not found at '$RequestedPath'."
        }
        return (Resolve-Path -LiteralPath $RequestedPath).Path
    }

    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
        return $command.Source
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher -and $pyLauncher.Source) {
        $resolved = & $pyLauncher.Source -3.11 -c "import sys; print(sys.executable)"
        if ($LASTEXITCODE -eq 0 -and $resolved) {
            return $resolved[-1].Trim()
        }
    }

    $knownLocations = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
        "C:\Python311\python.exe",
        "C:\Program Files\Python311\python.exe"
    )

    foreach ($knownLocation in $knownLocations) {
        if (Test-Path -LiteralPath $knownLocation -PathType Leaf) {
            return $knownLocation
        }
    }

    throw "Could not locate a usable base Python. Re-run with -BasePython <path-to-python.exe>."
}

function Remove-DirectoryIfPresent {
    param(
        [string]$Path
    )

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$repoPythonDir = Join-Path $repoRoot ".python"
$repoPythonExe = Join-Path $repoPythonDir "python.exe"
$venvDir = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$requirementsFile = Join-Path $repoRoot "requirements.txt"

$resolvedBasePython = Resolve-BasePythonPath -RequestedPath $BasePython
$basePythonDir = Split-Path -Parent $resolvedBasePython

Write-Host "Using base Python: $resolvedBasePython"
Write-Host "Refreshing repo-local interpreter at: $repoPythonDir"

Remove-DirectoryIfPresent -Path $repoPythonDir
New-Item -ItemType Directory -Path $repoPythonDir | Out-Null

$null = robocopy $basePythonDir $repoPythonDir /E /R:2 /W:1 /NFL /NDL /NJH /NJS /NC /NS
if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed while copying '$basePythonDir' to '$repoPythonDir' (exit code $LASTEXITCODE)."
}

if (-not (Test-Path -LiteralPath $repoPythonExe -PathType Leaf)) {
    throw "Repo-local python.exe was not created at '$repoPythonExe'."
}

Write-Host "Recreating virtual environment at: $venvDir"
Remove-DirectoryIfPresent -Path $venvDir

& $repoPythonExe -m venv $venvDir
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create virtual environment at '$venvDir'."
}

if ($InstallRequirements) {
    if (-not (Test-Path -LiteralPath $requirementsFile -PathType Leaf)) {
        throw "requirements.txt was not found at '$requirementsFile'."
    }

    Write-Host "Installing requirements into: $venvPython"
    & $venvPython -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed."
    }
}

Write-Host ""
Write-Host "Repo-local Python is ready."
Write-Host "Use it through: .\scripts\python.cmd --version"
if (-not $InstallRequirements) {
    Write-Host "Install dependencies with: .\scripts\python.cmd -m pip install -r requirements.txt"
}
