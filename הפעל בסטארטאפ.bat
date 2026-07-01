@echo off
chcp 65001 >nul
copy /Y "%USERPROFILE%\status-watch-startup.bat" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\status-watch-startup.bat" >nul
echo.
echo ✓ מפת סטטוס — סנכרון אוטומטי הופעל בסטארטאפ
echo   ירוץ ברקע אחרי כל הפעלה של Windows
echo   לוג: %~dp0סנכרון.log
echo.
pause