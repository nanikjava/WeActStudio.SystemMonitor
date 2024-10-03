@echo off
echo Python Module Uninstall

cd /d %~dp0
@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python"

:restart
set /p var="python -m pip uninstall "
cls
echo Start Uninstall

python -m pip uninstall %var%

goto restart