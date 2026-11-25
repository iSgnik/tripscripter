@echo off
rem TripScripter - prepara e liga o sistema em modo de demonstracao.
rem De dois cliques neste arquivo. As etapas estao em ferramentas\iniciar-demonstracao.ps1.
rem ExecutionPolicy Bypass vale so para esta execucao; nao altera a configuracao do Windows.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ferramentas\iniciar-demonstracao.ps1"
echo.
pause
