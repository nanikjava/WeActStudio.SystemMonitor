@echo off
echo Python Module 安装

@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python"

:restart
set /p var="python -m pip install "
cls
echo 开始安装

python -m pip install %var% --target .\Python\Lib\site-packages

goto restart