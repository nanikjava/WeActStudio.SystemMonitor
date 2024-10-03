@echo off
echo pip cache purge

cd /d %~dp0
@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python"

python -m pip cache purge

pause