@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --onedir --name ForexAI_PRO --icon ForexAI_PRO.ico --add-data "ForexAI_PRO.ico;." --collect-all MetaTrader5 --collect-all matplotlib forex_ai_pro.py
if errorlevel 1 (
 echo Build failed. Please check the error above.
 pause
 exit /b 1
)
py -m PyInstaller --noconfirm --clean --onefile --console --name ForexAI_Updater updater.py
if errorlevel 1 (echo Updater build failed.& pause & exit /b 1)
copy /Y dist\ForexAI_Updater.exe dist\ForexAI_PRO\ForexAI_Updater.exe >nul
echo.
echo Build complete: dist\ForexAI_PRO\ForexAI_PRO.exe
echo Copy the entire dist\ForexAI_PRO folder when sharing the app.
pause
