@echo off
chcp 65001 >nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\status-watch-startup.bat" >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\מפת סטטוס סנכרון.vbs" >nul 2>&1
if exist "%~dp0.watch.pid" del "%~dp0.watch.pid"
for /f "tokens=2" %%p in ('wmic process where "commandline like '%%watch.py%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do taskkill /PID %%p /F >nul 2>&1
echo.
echo ✓ סנכרון אוטומטי הוסר מסטארטאפ
echo.
pause