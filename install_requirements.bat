@echo off
cd /d "%~dp0"
py -m pip install --upgrade pip
py -m pip install MetaTrader5 matplotlib pyinstaller
if errorlevel 1 (
 echo Installation failed. Check Python version and internet connection.
 pause
 exit /b 1
)
echo Dependencies installed.
pause
