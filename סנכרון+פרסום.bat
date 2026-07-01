@echo off
chcp 65001 >nul
cd /d "%~dp0"
title מפת סטטוס — סנכרון + פרסום Netlify
echo.
echo מאזין לשינויים + פרסום אוטומטי ל-Netlify אחרי כל בנייה
echo דורש: git + netlify CLI מחוברים
echo Ctrl+C לעצירה
echo.
python scripts\watch.py --initial --deploy
if errorlevel 1 pause