# =============================================================================
# TripScripter — prepara e liga o sistema em modo de demonstração
#
# Chamado pelo INICIAR_DEMONSTRACAO.bat, na raiz do projeto. Não precisa de
# PostgreSQL nem de permissão de administrador. Pode ser executado mais de uma
# vez: o que já estiver pronto é pulado.
#
#   1. encontra o Python (3.12 ou mais novo)
#   2. cria o ambiente virtual em backend\.venv
#   3. instala as dependências (da pasta pacotes, sem internet, se existir)
#   4. cria backend\.env a partir de backend\.env.demo e pede a chave do Groq
#   5. cria o banco de demonstração (backend\demo.sqlite3)
#   6. abre o front-end no navegador e liga o servidor
# =============================================================================

# "Continue", e não "Stop": no Windows PowerShell, um aviso que o Python ou o
# pip escrevam na saída de erro interromperia o script com "Stop", mesmo com o
# comando bem-sucedido. Cada etapa confere o código de saída ($LASTEXITCODE).
$ErrorActionPreference = "Continue"
$raiz = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $raiz "backend"
$pacotes = Join-Path $raiz "pacotes"

function Etapa($texto) { Write-Host ""; Write-Host "==> $texto" -ForegroundColor Cyan }
function Falha($texto) { Write-Host ""; Write-Host "ERRO: $texto" -ForegroundColor Red; exit 1 }

Write-Host "TripScripter — preparação da demonstração" -ForegroundColor Green

# --- 1. Python -----------------------------------------------------------------
Etapa "Procurando o Python"

# "py -3" é o lançador oficial do Python no Windows; "python" pode ser o
# atalho da Microsoft Store, que não executa nada — por isso a versão é conferida.
$pythonExe = $null
$pythonArgs = @()
foreach ($candidato in @("py -3", "python", "python3")) {
    $partes = $candidato -split " "
    $argumentos = @($partes | Select-Object -Skip 1)
    try {
        $saida = & $partes[0] @argumentos --version 2>&1 | Out-String
    } catch { continue }
    if ($saida -match "Python (\d+)\.(\d+)") {
        if ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 12) {
            $pythonExe = $partes[0]
            $pythonArgs = $argumentos
            Write-Host "Encontrado: $($saida.Trim())"
            break
        }
        Write-Host "Encontrado $($saida.Trim()), mas o Django 6 exige Python 3.12 ou mais novo."
    }
}
if (-not $pythonExe) {
    Falha ("Python 3.12 ou mais novo não encontrado.`n" +
           "Instale em python.org/downloads, marcando 'Add python.exe to PATH'.`n" +
           "Sem permissão de administrador, escolha 'Install for me only'. Depois rode este arquivo de novo.")
}

# --- 2. Ambiente virtual -----------------------------------------------------------
# No Windows o Python do ambiente virtual fica em Scripts; no Linux e no
# macOS, em bin (só para testar este script fora do Windows).
if ($PSVersionTable.Platform -eq "Unix") {
    $venvPython = Join-Path $backend ".venv/bin/python"
} else {
    $venvPython = Join-Path $backend ".venv/Scripts/python.exe"
}
if (Test-Path $venvPython) {
    Etapa "Ambiente virtual já existe"
} else {
    Etapa "Criando o ambiente virtual"
    & $pythonExe @pythonArgs -m venv (Join-Path $backend ".venv")
    if (-not (Test-Path $venvPython)) { Falha "Não foi possível criar o ambiente virtual." }
}

# --- 3. Dependências ---------------------------------------------------------------
& $venvPython -c "import django, rest_framework, corsheaders, dotenv" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Etapa "Dependências já instaladas"
} else {
    $requisitos = Join-Path $backend "requirements-demo.txt"
    if (Test-Path $pacotes) {
        Etapa "Instalando as dependências da pasta pacotes (sem internet)"
        & $venvPython -m pip install --no-index --find-links $pacotes -r $requisitos
    } else {
        Etapa "Instalando as dependências pela internet"
        & $venvPython -m pip install -r $requisitos
    }
    if ($LASTEXITCODE -ne 0) { Falha "A instalação das dependências falhou. Veja a mensagem acima." }
}

# --- 4. Configuração --------------------------------------------------------------
$arquivoEnv = Join-Path $backend ".env"
if (Test-Path $arquivoEnv) {
    Etapa "Usando o backend\.env que já existe"
    if (-not (Select-String -Path $arquivoEnv -Pattern "^DB_MOTOR=sqlite" -Quiet)) {
        Write-Host "Atenção: esse .env não tem DB_MOTOR=sqlite, então o sistema vai tentar usar o PostgreSQL." -ForegroundColor Yellow
        Write-Host "Para o modo de demonstração, apague o backend\.env e rode este arquivo de novo." -ForegroundColor Yellow
    }
} else {
    Etapa "Criando o backend\.env"
    $conteudo = Get-Content (Join-Path $backend ".env.demo") -Raw -Encoding UTF8
    $chave = ""
    # Sem teclado (execução automatizada), a pergunta travaria: pula direto.
    if (-not [Console]::IsInputRedirected) {
        Write-Host "Cole a chave do Groq com o botão direito e aperte Enter (ela não aparece na tela)."
        Write-Host "Para usar só o modo simulado, sem internet, apenas aperte Enter."
        $segura = Read-Host -AsSecureString "Chave"
        $chave = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura)).Trim()
    }
    if ($chave) {
        $conteudo = $conteudo -replace "(?m)^GROQ_API_KEY=.*$", "GROQ_API_KEY=$chave"
        $conteudo = $conteudo -replace "(?m)^IA_PROVEDOR=.*$", "IA_PROVEDOR=groq"
        Write-Host "Chave gravada. A IA usada será o Groq, com o modo simulado de reserva."
    } else {
        Write-Host "Sem chave: os roteiros serão montados pelo modo simulado."
    }
    [IO.File]::WriteAllText($arquivoEnv, $conteudo, (New-Object Text.UTF8Encoding $false))
}

# --- 5. Banco de demonstração -------------------------------------------------------
Etapa "Preparando o banco de demonstração"
Push-Location $backend
try {
    & $venvPython manage.py criar_banco_demo
    if ($LASTEXITCODE -ne 0) { Falha "Não foi possível criar o banco de demonstração." }

    # --- 6. Navegador e servidor ----------------------------------------------------
    Etapa "Abrindo o TripScripter no navegador"
    $pagina = Join-Path $raiz "frontend/index.html"
    try { Start-Process $pagina } catch { Write-Host "Abra no navegador: $pagina" }
    Write-Host ""
    Write-Host "Login: marina@email.com   Senha: demonstracao" -ForegroundColor Green
    Write-Host "DEIXE ESTA JANELA ABERTA durante a apresentação: ela é o servidor." -ForegroundColor Yellow
    Write-Host "Para desligar, feche a janela ou aperte Ctrl+C."
    Write-Host ""
    & $venvPython manage.py runserver 127.0.0.1:8000 --noreload
} finally {
    Pop-Location
}
