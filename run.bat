@echo off
title Prava Test Boti
echo ==============================================
echo        Prava Test Boti ishga tushirilmoqda...
echo ==============================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py
pause
