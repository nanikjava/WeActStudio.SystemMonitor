@echo off
echo Python Module п╤ть

@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python"

:restart
set /p var="python -m pip uninstall "
cls
echo ©╙й╪п╤ть

python -m pip uninstall %var%

goto restart