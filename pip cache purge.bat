@echo off
echo pip cache purge

cd /d %~dp0
@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python"

WeActStudioSystemMonitor -m pip cache purge

pause