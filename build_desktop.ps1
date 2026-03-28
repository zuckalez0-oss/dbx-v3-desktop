param(
    [string]$RepoPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$resolvedRepoPath = (Resolve-Path $RepoPath).Path
$venvPath = Join-Path $resolvedRepoPath ".venv_desktop"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$requirementsPath = Join-Path $resolvedRepoPath "requirements.txt"

if (-not (Test-Path $requirementsPath)) {
    $requirementsPath = Join-Path $resolvedRepoPath "requirements-desktop.txt"
}

if (-not (Test-Path $requirementsPath)) {
    throw "Arquivo de dependencias nao encontrado em '$resolvedRepoPath'."
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "Criando ambiente virtual desktop em $venvPath ..."
    py -m venv $venvPath
}

Write-Host "Atualizando pip..."
& $pythonExe -m pip install --upgrade pip

Write-Host "Instalando dependencias desktop..."
& $pythonExe -m pip install -r $requirementsPath pyinstaller

Write-Host "Gerando build com PyInstaller..."
& $pythonExe -m PyInstaller (Join-Path $resolvedRepoPath "main.spec") --clean

Write-Host ""
Write-Host "Build concluido. Verifique a pasta 'dist' em $resolvedRepoPath"
