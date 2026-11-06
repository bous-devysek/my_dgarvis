#requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Step([string]$text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Fail([string]$text) { Write-Host "`nERROR: $text" -ForegroundColor Red; throw $text }

# --- 1. Python 3.12-3.14 ------------------------------------------------
Step 'Looking for Python 3.12-3.14'
$pyExe  = $null
$pyArgs = @()

# py -3.12 при отсутствии версии пишет в stderr. В PowerShell 5.1 при
# $ErrorActionPreference='Stop' это превращается в исключение и обрывает
# скрипт до проверки следующей версии, поэтому проверяем через cmd:
# его stderr не попадает в поток ошибок PowerShell.
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in @('3.12', '3.13', '3.14')) {
        cmd /c "py -$v -c ""import sys"" >nul 2>nul"
        if ($LASTEXITCODE -eq 0) { $pyExe = 'py'; $pyArgs = @("-$v"); break }
    }
}

if (-not $pyExe -and (Get-Command python -ErrorAction SilentlyContinue)) {
    cmd /c "python -c ""import sys; raise SystemExit(0 if (3, 12) <= sys.version_info[:2] <= (3, 14) else 1)"" >nul 2>nul"
    if ($LASTEXITCODE -eq 0) { $pyExe = 'python'; $pyArgs = @() }
}

if (-not $pyExe) {
    Fail 'Python 3.12-3.14 not found. Run: winget install -e --id Python.Python.3.14'
}
Write-Host "Using: $pyExe $($pyArgs -join ' ')"
& $pyExe @pyArgs --version

# --- 2. venv ------------------------------------------------------------
$venvPy = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$venvCreated = $false
if (-not (Test-Path -LiteralPath $venvPy)) {
    Step 'Creating virtual environment (.venv)'
    & $pyExe @pyArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { Fail 'Could not create .venv' }
    $venvCreated = $true
} else {
    Write-Host '.venv already exists'
}

# --- 3. зависимости -----------------------------------------------------
# pip обновляем только для нового venv: при повторном запуске установщик
# не должен зависеть от сети, если всё уже стоит.
if ($venvCreated) {
    Step 'Updating pip'
    & $venvPy -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Fail 'pip upgrade failed' }
}

Step 'Installing requirements (may take 10-30 minutes)'
& $venvPy -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Fail 'pip install failed' }

# --- 4. модель Whisper --------------------------------------------------
$modelFile = Join-Path $PSScriptRoot 'models\faster-whisper-large-v3-turbo-ct2\model.bin'
if (Test-Path -LiteralPath $modelFile) {
    Write-Host 'Whisper model already downloaded'
} else {
    Step 'Downloading Whisper model (~1.6 GB)'
    & $venvPy (Join-Path $PSScriptRoot 'download_model.py')
    if ($LASTEXITCODE -ne 0) { Fail 'Model download failed' }
    if (-not (Test-Path -LiteralPath $modelFile)) {
        Fail 'Whisper model not found after download'
    }
}

# --- 5. папка настроек ---------------------------------------------------
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'config') | Out-Null

# --- 6. ярлык на рабочем столе -----------------------------------------
Step 'Creating desktop shortcut'
$desktop = [Environment]::GetFolderPath('Desktop')
$ws  = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut((Join-Path $desktop 'garvis.lnk'))
$lnk.TargetPath       = Join-Path $PSScriptRoot 'run_console.bat'
$lnk.WorkingDirectory = $PSScriptRoot
$lnk.IconLocation     = "$venvPy,0"
$lnk.Description      = 'garvis voice assistant'
$lnk.Save()

Write-Host "`nDone. Launch 'garvis' from the desktop." -ForegroundColor Green