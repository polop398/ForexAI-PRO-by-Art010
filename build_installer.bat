@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" if not exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
 echo Inno Setup 6 not found. Please install it from https://jrsoftware.org/isinfo.php
 pause
 exit /b 1
)
call build_exe.bat
if errorlevel 1 exit /b 1
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
 "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ForexAI_PRO_Setup.iss
) else (
 "C:\Program Files\Inno Setup 6\ISCC.exe" ForexAI_PRO_Setup.iss
)
if errorlevel 1 (echo Installer build failed.& pause & exit /b 1)
echo Installer created in installer_output.
pause
