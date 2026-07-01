@echo off
cd /d "%~dp0"
echo בונה מפה מחדש...
python scripts\build.py
if errorlevel 1 pause & exit /b 1
cd /d "%~dp0..\תיק עבודות\portfolio-git-temp"
netlify status 2>&1 | findstr /i "storied-alfajores-6f10d2" >nul
if errorlevel 1 (
  echo.
  echo שגיאה: Netlify לא מקושר ל-storied-alfajores-6f10d2
  echo הרץ מתוך portfolio-git-temp: netlify link
  pause & exit /b 1
)
git add status-dashboard.html
git commit -m "update status dashboard"
git push origin main
netlify deploy --prod --dir . --site 3276a480-932a-403f-8abe-07f7c9bfb3b0
echo.
echo פורסם: https://storied-alfajores-6f10d2.netlify.app/status-dashboard.html
pause