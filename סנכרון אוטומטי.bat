@echo off
chcp 65001 >nul
cd /d "%~dp0"
title מפת סטטוס — סנכרון אוטומטי
echo.
echo מאזין לשינויים ב-portfolio.html
echo כל שמירה ^> בנייה אוטומטית של מפת הסטטוס
echo Ctrl+C לעצירה
echo.
python scripts\watch.py --initial
if errorlevel 1 pause