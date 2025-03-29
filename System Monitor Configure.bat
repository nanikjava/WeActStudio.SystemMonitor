cd /d %~dp0
@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python;"
start "System Monitor Configure" "%~dp0Python\WeActStudioSystemMonitor_w.exe" ".\configure.py"