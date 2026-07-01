# מפת סטטוס פרויקטים — Patlas Project Status Map

לוח בקרה שבודק את הזמינות של כל האתרים בתיק העבודות ומציג באנר כשמשהו נשבר.

## עברית

מפת HTML שסורקת את `portfolio.html` ובודקת עבור כל פרויקט אם ה-URL שלו מחזיר קוד HTTP תקין (200) או שגיאה (4xx/5xx). פרויקטים שנשברו מסומנים בבאנר אדום ובתג "חדש!".

**קבצים עיקריים:**
- `מפת סטטוס פרויקטים.html` — הדשבורד עצמו
- `scripts/build.py` — בונה את הדף מתוך portfolio.html
- `scripts/watch.py` — סנכרון אוטומטי בזמן עריכה
- `status-state.json` — מצב אחרון של כל פרויקט (לזיהוי שינויים)

**שימוש:** `פתח.bat` לפתיחה, `רענן.bat` לבנייה מחדש, `סנכרון אוטומטי.bat` להאזנה לשינויים.

## English

A dashboard that scans all projects listed in `portfolio.html` and checks each project's live URL for HTTP errors (4xx/5xx) or unreachable sites. Broken projects get flagged with a red banner and a "new" badge since the last build.

**Key files:**
- `מפת סטטוס פרויקטים.html` — the dashboard itself
- `scripts/build.py` — builds the page from portfolio.html
- `scripts/watch.py` — auto-rebuild on file changes
- `status-state.json` — last known state per project (for change detection)

## License

MIT
