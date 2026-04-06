param(
    [string]$RepoPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$resolvedRepoPath = (Resolve-Path $RepoPath).Path
$venvPath = Join-Path $resolvedRepoPath ".venv_desktop"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$requirementsPath = Join-Path $resolvedRepoPath "requirements.txt"

function Resolve-BootstrapPython {
    $preferredWindowsPythons = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe")
    )

    foreach ($candidatePath in $preferredWindowsPythons) {
        if ($candidatePath -and (Test-Path $candidatePath)) {
            return $candidatePath
        }
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        try {
            $resolvedPyExe = (& py -c "import sys; print(sys.executable)" 2>$null).Trim()
            if ($LASTEXITCODE -eq 0 -and $resolvedPyExe -and (Test-Path $resolvedPyExe)) {
                return $resolvedPyExe
            }
        } catch {
        }
    }

    foreach ($candidate in @("python", "python3")) {
        $resolvedCommand = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($resolvedCommand) {
            return $resolvedCommand.Source
        }
    }

    throw "Nenhum interpretador Python disponivel para criar o ambiente virtual desktop."
}

if (-not (Test-Path $requirementsPath)) {
    $requirementsPath = Join-Path $resolvedRepoPath "requirements-desktop.txt"
}

if (-not (Test-Path $requirementsPath)) {
    throw "Arquivo de dependencias nao encontrado em '$resolvedRepoPath'."
}

$unixPythonExe = Join-Path $venvPath "bin\python.exe"
if ((Test-Path $venvPath) -and -not (Test-Path $pythonExe) -and (Test-Path $unixPythonExe)) {
    $resolvedVenvPath = (Resolve-Path $venvPath).Path
    if (-not $resolvedVenvPath.StartsWith($resolvedRepoPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Abortado: o ambiente virtual encontrado esta fora do repositorio esperado."
    }

    Write-Host "Removendo ambiente virtual invalido criado em formato nao-Windows..."
    Remove-Item -LiteralPath $resolvedVenvPath -Recurse -Force
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "Criando ambiente virtual desktop em $venvPath ..."
    $bootstrapPython = Resolve-BootstrapPython
    & $bootstrapPython -m venv $venvPath
}

if (-not (Test-Path $pythonExe)) {
    throw "Falha ao criar o ambiente virtual desktop em formato Windows. Verifique o Python utilizado para o build."
}

Write-Host "Atualizando pip..."
& $pythonExe -m pip install --upgrade pip

Write-Host "Instalando dependencias desktop..."
& $pythonExe -m pip install -r $requirementsPath pyinstaller

Write-Host "Gerando build com PyInstaller..."
& $pythonExe -m PyInstaller (Join-Path $resolvedRepoPath "main.spec") --clean

Write-Host ""
Write-Host "Build concluido. Verifique a pasta 'dist' em $resolvedRepoPath"
