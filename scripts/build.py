# -*- coding: utf-8 -*-
"""Build desktop project status dashboard with cover art and live URL checks."""
import re, json, os, urllib.request, urllib.parse, base64, ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
PORTFOLIO_DIR = os.path.join(os.path.expanduser('~'), 'Desktop', 'פרויקטים', 'תיק עבודות')
PORTFOLIO = os.path.join(PORTFOLIO_DIR, 'portfolio.html')
OUT_HTML = os.path.join(PROJECT_DIR, 'מפת סטטוס פרויקטים.html')
OUT_NETLIFY = os.path.join(PORTFOLIO_DIR, 'portfolio-git-temp', 'status-dashboard.html')
STATE_FILE = os.path.join(PROJECT_DIR, 'status-state.json')
BASE_NETLIFY = 'https://storied-alfajores-6f10d2.netlify.app/'

# Manual quality tier (truth on the ground)
TIER = {
    'math': 'full', 'maslul': 'full', 'teshuva': 'full', 'signallab': 'full',
    'hashem': 'full',  # real PWA on genuine-cobbler
    'idcheck': 'works', 'dapor': 'works', 'trends': 'works', 'polygraph': 'works',
    'money': 'works', 'rct': 'works', 'patlasgames': 'works', 'kidsgames': 'works',
    'shofar': 'works', 'greenhouse': 'works', 'pizza': 'works', 'palette': 'works',
    'cyberos': 'works', 'bridgeos': 'works', 'recentfiles': 'works',
    'csslib': 'works', 'codemap': 'works', 'echo': 'works', 'phish': 'works',
    'codesplit': 'works', 'codeauth': 'works', 'cyberos': 'works', 'cablevitality': 'works',
    'yomi': 'works', 'leads': 'works',
    'etrog': 'works', 'emotion': 'works', 'cables': 'works', 'breath': 'works',
    'dapor-schedule': 'works', 'codekids': 'works', 'crmgen': 'works', 'emailplus': 'works',
    'mltrain': 'works', 'digibook': 'works', 'budget': 'works', 'etrog-studio': 'works',
    'green-farm': 'works', 'diykids': 'works', 'mahat': 'works',
    'mishnat': 'wip',
}

TIER_META = {
    'full':  {'label': 'עובד מלא', 'color': '#22c55e', 'icon': '🟢', 'order': 0},
    'works': {'label': 'עובד',     'color': '#4ade80', 'icon': '✅', 'order': 1},
    'demo':  {'label': 'דמו / נראה', 'color': '#f5c842', 'icon': '🟡', 'order': 2},
    'wip':   {'label': 'בפיתוח',   'color': '#60a5fa', 'icon': '🔵', 'order': 3},
    'broken':{'label': 'שבור',     'color': '#f87171', 'icon': '🔴', 'order': 4},
}

THEMES = {
    'math':(42,28,78),'maslul':(205,225,72),'teshuva':(265,290,70),'yomi':(38,52,68),
    'dapor':(215,195,65),'idcheck':(195,220,74),'trends':(280,310,68),'etrog':(48,35,76),
    'emotion':(330,350,72),'polygraph':(250,270,66),'mltrain':(275,295,70),'money':(45,30,80),
    'rct':(315,335,74),'patlasgames':(260,285,72),'kidsgames':(340,320,68),'cables':(200,180,70),
    'shofar':(32,45,72),'hashem':(40,55,65),'breath':(175,195,68),'greenhouse':(125,145,72),
    'dapor-schedule':(355,330,70),'digibook':(38,55,65),'budget':(30,42,66),'leads':(145,165,74),
    'crmgen':(210,230,68),'emailplus':(220,240,70),'pizza':(8,25,78),'palette':(300,320,76),
    'csslib':(285,305,72),'codemap':(165,185,70),'echo':(240,260,68),'phish':(350,330,66),
    'codesplit':(230,250,72),'codeauth':(255,275,70),'codekids':(320,300,68),'cyberos':(245,265,74),
    'bridgeos':(42,58,72),'recentfiles':(248,268,70),
    'etrog-studio':(52,38,76),'green-farm':(128,148,78),'cablevitality':(198,218,72),
    'diykids':(22,45,78),'mahat':(215,235,70),'signallab':(255,275,70),
    'mishnat':(28,42,74),
}

CAT_HUE = {'flag':42,'edu':210,'ai':270,'jewish':38,'games':320,'biz':160,'dev':250,'live':42}

CAT_LABELS = {
    'flag': 'דגל', 'edu': 'חינוך', 'ai': 'AI', 'jewish': 'יהדות',
    'games': 'משחקים', 'biz': 'עסקים', 'dev': 'פיתוח', 'live': 'חי',
}

PREVIEWS = {
    'math': 'https://math-haredim.netlify.app/banners/banner-2.png',
    'maslul': 'https://maslul-rechev-2026.netlify.app/assets/hero-command-center-2026.png',
    'teshuva': 'https://teshuva-algorithm.netlify.app/og-image.png',
    'greenhouse': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format&fit=crop&w=900&q=80',
    'yomi': 'https://images.unsplash.com/photo-1518709268805-4e9042af9b83?auto=format&fit=crop&w=900&q=80',
    'shofar': 'https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=900&q=80',
    'hashem': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=900&q=80',
    'pizza': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=900&q=80',
    'rct': 'https://images.unsplash.com/photo-1594784313914-84a3812623f4?auto=format&fit=crop&w=900&q=80',
    'cablevitality': 'https://images.unsplash.com/photo-1473968512647-3e447244af8f?auto=format&fit=crop&w=900&q=80',
    'cyberos': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=900&q=80',
    'trends': 'https://images.unsplash.com/photo-1611162616475-46b635cb6868?auto=format&fit=crop&w=900&q=80',
    'polygraph': 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=900&q=80',
    'idcheck': 'https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=900&q=80',
    'signallab': 'https://images.unsplash.com/photo-1516116216624-53e697fedbea?auto=format&fit=crop&w=900&q=80',
    'money': 'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=900&q=80',
    'patlasgames': 'https://images.unsplash.com/photo-1552820728-8b83bb6b773f?auto=format&fit=crop&w=900&q=80',
    'csslib': 'https://images.unsplash.com/photo-1507727300440-9e5a8b565c1b?auto=format&fit=crop&w=900&q=80',
    'leads': 'https://images.unsplash.com/photo-1611605698335-8b1569810432?auto=format&fit=crop&w=900&q=80',
}

LIVE_URL = {
    'hashem': 'https://genuine-cobbler-8783c8.netlify.app/',
    'recentfiles': 'https://storied-alfajores-6f10d2.netlify.app/RecentFiles/index.html',
    'signallab': 'https://davidpatlas-ai.github.io/signal-lab/',
}


def grab_quoted(text, start):
    chars, i = [], start
    while i < len(text):
        c = text[i]
        if c == '\\' and i + 1 < len(text):
            chars.append(text[i + 1])
            i += 2
        elif c == "'":
            break
        else:
            chars.append(c)
            i += 1
    return ''.join(chars)


def grab_field(block, key):
    marker = f"{key}:'"
    pos = block.find(marker)
    return grab_quoted(block, pos + len(marker)) if pos != -1 else None


def grab_he_field(block, field):
    marker = f"{field}:{{he:'"
    pos = block.find(marker)
    return grab_quoted(block, pos + len(marker)) if pos != -1 else None


def parse_catalog(html):
    items = []
    for block in html.split("{ id:'")[1:]:
        m = re.match(r"([^']+)'", block)
        if not m:
            continue
        pid = m.group(1)
        demo = grab_field(block, 'demo')
        url = grab_field(block, 'url')
        preview = grab_field(block, 'preview')
        icon = grab_field(block, 'icon') or '📦'
        status = grab_field(block, 'status') or 'live'
        contact = 'contact:1' in block
        name = grab_he_field(block, 'name') or pid
        desc = grab_he_field(block, 'desc') or ''
        cat_m = re.search(r"cat:\[([^\]]*)\]", block)
        cats = re.findall(r"'([^']+)'", cat_m.group(1)) if cat_m else []
        gh = grab_field(block, 'gh')
        items.append(dict(id=pid, name=name, desc=desc, icon=icon, status=status,
                        contact=contact, demo=demo, url=url, preview=preview, gh=gh, cat=cats))
    return items


def project_url(p):
    if p['id'] in LIVE_URL:
        return LIVE_URL[p['id']]
    if p.get('demo'):
        return p['demo']
    if p.get('url'):
        return BASE_NETLIFY + urllib.parse.quote(p['url'], safe='/')
    return p.get('gh')


def is_dedicated(url):
    if not url:
        return False
    return 'storied-alfajores-6f10d2.netlify.app' not in url


def load_prev_state():
    try:
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_state(rows):
    state = {
        'updated': datetime.now().isoformat(timespec='seconds'),
        'projects': {
            r['id']: {'http': r['http'], 'tier': r['tier'], 'url': r['url'], 'httpErr': r['httpErr']}
            for r in rows
        },
    }
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def is_url_broken(http, err, url, contact):
    if contact or not url:
        return False
    if http and http >= 400:
        return True
    if http is None and err not in ('no-url', 'contact'):
        return True
    return False


def find_newly_broken(rows, prev):
    prev_projects = prev.get('projects', {})
    if not prev_projects:
        return []
    out = []
    for r in rows:
        if r['tier'] != 'broken':
            continue
        if prev_projects.get(r['id'], {}).get('tier') != 'broken':
            out.append(r)
    return out


def check_url(url):
    if not url:
        return None, 'no-url'
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'PatlasDashboard/1.0'})
        with urllib.request.urlopen(req, timeout=14, context=ctx) as r:
            return r.status, 'ok'
    except Exception:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'PatlasDashboard/1.0'})
            with urllib.request.urlopen(req, timeout=14, context=ctx) as r:
                return r.status, 'ok'
        except Exception as e:
            return getattr(e, 'code', None), str(getattr(e, 'reason', e))[:40]


def svg_cover(pid, icon, h, h2, s):
    pat = ''
    if pid in ('math','dapor','idcheck','csslib','cyberos','codemap','crmgen'):
        pat = '<defs><pattern id="g" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M0 24L24 0" stroke="rgba(255,255,255,.09)" stroke-width="1"/></pattern></defs><rect width="100%" height="100%" fill="url(#g)"/>'
    elif pid in ('teshuva','trends','echo','breath','emotion','signallab'):
        pat = '<path d="M0 70 Q90 10 180 70 T360 70" fill="none" stroke="rgba(255,255,255,.14)" stroke-width="2.5"/><path d="M0 110 Q90 50 180 110 T360 110" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="2"/>'
    else:
        pat = '<circle cx="50" cy="35" r="4" fill="rgba(255,255,255,.18)"/><circle cx="310" cy="70" r="6" fill="rgba(255,255,255,.1)"/><circle cx="220" cy="150" r="3" fill="rgba(255,255,255,.14)"/><circle cx="120" cy="90" r="2" fill="rgba(255,255,255,.12)"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 200" width="360" height="200">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="hsl({h},{s}%,46%)"/>
          <stop offset="55%" stop-color="hsl({h2},{s}%,34%)"/>
          <stop offset="100%" stop-color="hsl({h},{s}%,22%)"/>
        </linearGradient>
        <radialGradient id="glow" cx="70%" cy="20%" r="55%">
          <stop offset="0%" stop-color="rgba(255,255,255,.22)"/>
          <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
        </radialGradient>
      </defs>
      <rect width="360" height="200" fill="url(#bg)"/>
      <rect width="360" height="200" fill="url(#glow)"/>
      {pat}
      <rect x="24" y="24" width="312" height="152" rx="18" fill="rgba(255,255,255,.05)" stroke="rgba(255,255,255,.12)" stroke-width="1"/>
      <text x="180" y="108" text-anchor="middle" font-size="56">{icon}</text>
      <text x="180" y="168" text-anchor="middle" fill="rgba(255,255,255,.9)" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="700">{pid}</text>
    </svg>'''
    b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return f'data:image/svg+xml;base64,{b64}'


def theme_for(p):
    if p['id'] in THEMES:
        h, h2, s = THEMES[p['id']]
        return h, h2, s
    cat = next((c for c in p['cat'] if c != 'live'), 'dev')
    h = CAT_HUE.get(cat, 250)
    return h, (h + 35) % 360, 68


def build_rows(catalog):
    prepared = []
    checks = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {}
        for p in catalog:
            url = project_url(p)
            if url and not p.get('contact'):
                futures[pool.submit(check_url, url)] = p['id']
        for fut in as_completed(futures):
            checks[futures[fut]] = fut.result()

    for p in catalog:
        url = project_url(p)
        http, err = checks.get(p['id'], (None, 'contact' if p.get('contact') else 'no-url'))
        tier = TIER.get(p['id'], 'works')
        if is_url_broken(http, err, url, p.get('contact')):
            tier = 'broken'
        elif p.get('contact') or p['status'] == 'wip':
            tier = TIER.get(p['id'], 'wip')
        preview = p.get('preview') or PREVIEWS.get(p['id'])
        h, h2, s = theme_for(p)
        if not preview:
            preview = svg_cover(p['id'], p['icon'], h, h2, s)
        prepared.append({
            'id': p['id'], 'name': p['name'], 'desc': p['desc'], 'icon': p['icon'],
            'tier': tier, 'tierLabel': TIER_META[tier]['label'], 'tierColor': TIER_META[tier]['color'],
            'tierIcon': TIER_META[tier]['icon'], 'tierOrder': TIER_META[tier]['order'],
            'url': url or '', 'http': http, 'httpErr': err,
            'preview': preview, 'gh': p.get('gh') or '', 'cats': p['cat'],
            'dedicated': is_dedicated(url),
        })
    prepared.sort(key=lambda r: (r['tierOrder'], r['name']))
    return prepared


def render_html(rows, generated, newly_broken=None):
    newly_broken = newly_broken or []
    data = json.dumps(rows, ensure_ascii=False)
    newly_json = json.dumps([r['id'] for r in newly_broken], ensure_ascii=False)
    counts = {k: sum(1 for r in rows if r['tier'] == k) for k in TIER_META}
    total = len(rows)
    healthy = counts['full'] + counts['works']
    health_pct = round(healthy / total * 100) if total else 0
    all_cats = sorted({c for r in rows for c in r['cats'] if c != 'live'})

    return f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>מפת סטטוס פרויקטים — Patlas</title>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#06060c;--surface:#12121c;--border:rgba(245,200,66,.16);
  --text:#eceaf8;--muted:#8b89a8;--gold:#f5c842;--accent:#7c6af5;
  --shadow:0 16px 48px rgba(0,0,0,.45);--input-bg:rgba(0,0,0,.35);--toolbar-bg:rgba(18,18,28,.85);
}}
html[data-theme="light"]{{
  --bg:#eef2ff;--surface:#fff;--border:rgba(91,79,207,.18);
  --text:#12111a;--muted:#5c5a72;--gold:#d4a017;--accent:#5b4fcf;
  --shadow:0 14px 40px rgba(91,79,207,.14);--input-bg:rgba(255,255,255,.9);--toolbar-bg:rgba(255,255,255,.92);
  color-scheme:light;
}}
html:not([data-theme="light"]){{color-scheme:dark}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Rubik,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;
  background-image:radial-gradient(ellipse 80% 50% at 50% -20%,rgba(124,106,245,.18),transparent),
                   radial-gradient(ellipse 40% 30% at 90% 90%,rgba(245,200,66,.06),transparent);
  transition:background .3s,color .3s}}
html[data-theme="light"] body{{
  background-image:radial-gradient(ellipse 80% 50% at 50% -20%,rgba(91,79,207,.12),transparent),
                   radial-gradient(ellipse 40% 30% at 90% 90%,rgba(212,160,23,.08),transparent)}}
.wrap{{max-width:1400px;margin:0 auto;padding:24px 20px 60px}}
header{{text-align:center;margin-bottom:28px;position:relative}}
.header-actions{{position:absolute;top:0;left:0;display:flex;gap:8px;flex-wrap:wrap}}
.icon-btn{{padding:8px 12px;border-radius:999px;border:1px solid var(--border);background:var(--surface);
  color:var(--text);cursor:pointer;font-family:inherit;font-size:.78rem;font-weight:600;transition:.2s}}
.icon-btn:hover{{border-color:var(--gold);color:var(--gold)}}
header h1{{font-family:Syne,sans-serif;font-size:clamp(1.8rem,4vw,2.8rem);
  background:linear-gradient(135deg,var(--gold),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;margin-bottom:8px}}
header p{{color:var(--muted);font-size:1rem}}
.health{{max-width:480px;margin:16px auto 0;display:flex;flex-direction:column;gap:6px;align-items:stretch}}
.health-track{{height:8px;background:rgba(255,255,255,.08);border-radius:999px;overflow:hidden;border:1px solid var(--border)}}
.health-fill{{height:100%;background:linear-gradient(90deg,#22c55e,#4ade80);border-radius:999px;transition:width .4s}}
.health-txt{{font-size:.82rem;color:var(--muted);text-align:center}}
.alert-banner{{display:none;margin:0 0 20px;border:1px solid rgba(248,113,113,.45);background:rgba(248,113,113,.1);
  border-radius:16px;padding:14px 16px;animation:alertPulse 2.4s ease-in-out infinite}}
@keyframes alertPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(248,113,113,0)}}50%{{box-shadow:0 0 0 6px rgba(248,113,113,.12)}}}}
.alert-inner{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
.alert-title{{font-weight:800;color:#fecaca;flex:1;min-width:180px}}
.alert-items{{display:flex;flex-wrap:wrap;gap:8px;flex:2}}
.alert-item{{padding:6px 12px;border-radius:999px;border:1px solid rgba(248,113,113,.45);background:rgba(0,0,0,.2);
  color:#fecaca;font-family:inherit;font-size:.78rem;cursor:pointer;transition:.2s}}
.alert-item:hover{{border-color:#f87171;background:rgba(248,113,113,.18)}}
.alert-new{{color:#fde047;font-weight:800;margin-inline-start:4px}}
.alert-actions{{display:flex;gap:8px}}
.alert-btn{{padding:6px 12px;border-radius:999px;border:1px solid rgba(248,113,113,.4);background:transparent;
  color:#fecaca;font-family:inherit;font-size:.78rem;font-weight:600;cursor:pointer}}
.alert-btn:hover{{background:rgba(248,113,113,.15)}}
.stats{{display:flex;flex-wrap:wrap;justify-content:center;gap:12px;margin:22px 0}}
.stat{{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px 22px;min-width:110px;text-align:center}}
.stat b{{display:block;font-size:1.6rem;font-weight:800}}
.stat span{{font-size:.78rem;color:var(--muted)}}
.toolbar{{display:flex;flex-direction:column;gap:12px;margin-bottom:22px;
  background:var(--toolbar-bg);border:1px solid var(--border);border-radius:16px;padding:14px 16px;backdrop-filter:blur(10px);position:sticky;top:10px;z-index:10}}
.toolbar-row{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
.search{{flex:1;min-width:200px;padding:12px 16px;border-radius:999px;border:1px solid var(--border);
  background:var(--input-bg);color:var(--text);font-family:inherit;font-size:.95rem}}
.search:focus{{outline:none;border-color:var(--gold)}}
.sort{{padding:10px 14px;border-radius:999px;border:1px solid var(--border);background:var(--input-bg);
  color:var(--text);font-family:inherit;font-size:.85rem;cursor:pointer}}
.sort:focus{{outline:none;border-color:var(--gold)}}
.chip-row{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.chip-label{{font-size:.75rem;color:var(--muted);font-weight:600;min-width:42px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;flex:1}}
.chip{{padding:8px 16px;border-radius:999px;border:1px solid var(--border);background:transparent;
  color:var(--muted);cursor:pointer;font-family:inherit;font-size:.85rem;font-weight:600;transition:.2s}}
.chip:hover,.chip.on{{border-color:var(--gold);color:var(--text);background:rgba(245,200,66,.1)}}
.chip.cat.on{{border-color:var(--accent);background:rgba(124,106,245,.12);color:#c4b5fd}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}}
.grid.list{{display:flex;flex-direction:column;gap:10px}}
.grid.list .card{{flex-direction:row;align-items:stretch}}
.grid.list .card:hover{{transform:none}}
.grid.list .cover{{width:148px;min-width:148px;height:auto;min-height:108px;flex-shrink:0}}
.grid.list .cover img{{height:100%;min-height:108px}}
.grid.list .body{{padding:12px 16px}}
.grid.list .body p{{-webkit-line-clamp:2;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:18px;overflow:hidden;
  transition:transform .25s,box-shadow .25s;cursor:pointer;display:flex;flex-direction:column}}
.card:hover{{transform:translateY(-4px);box-shadow:var(--shadow);border-color:rgba(245,200,66,.35)}}
.grid.list .card:hover{{box-shadow:var(--shadow);border-color:rgba(245,200,66,.35)}}
.card.broken{{border-color:rgba(248,113,113,.45)}}
.card.broken:hover{{border-color:rgba(248,113,113,.7)}}
.card.full{{box-shadow:0 0 0 1px rgba(34,197,94,.12)}}
.cover{{height:160px;background:#0a0a12;position:relative;overflow:hidden}}
.cover img{{width:100%;height:100%;object-fit:cover;display:block}}
.cover::after{{content:'';position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(6,6,12,.85))}}
.badges{{position:absolute;top:12px;right:12px;z-index:2;display:flex;flex-direction:column;gap:6px;align-items:flex-end}}
.badge{{padding:5px 12px;border-radius:999px;font-size:.75rem;font-weight:700;backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.15)}}
.badge.dedicated{{background:rgba(124,106,245,.25);color:#c4b5fd;border-color:rgba(124,106,245,.4);font-size:.68rem}}
.body{{padding:16px 18px 18px;flex:1;display:flex;flex-direction:column}}
.body h3{{font-size:1.05rem;font-weight:700;margin-bottom:6px;line-height:1.35}}
.body p{{font-size:.82rem;color:var(--muted);line-height:1.5;flex:1;margin-bottom:14px}}
.meta{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}}
.tag{{font-size:.7rem;padding:3px 8px;border-radius:6px;background:rgba(124,106,245,.15);color:#c4b5fd}}
.actions{{display:flex;gap:8px;flex-wrap:wrap}}
.btn{{padding:8px 14px;border-radius:999px;font-size:.8rem;font-weight:600;text-decoration:none;
  border:none;cursor:pointer;font-family:inherit;transition:.2s}}
.btn-primary{{background:linear-gradient(135deg,var(--gold),#e0a820);color:#1a1a2e}}
.btn-primary:hover{{filter:brightness(1.08)}}
.btn-ghost{{background:rgba(255,255,255,.08);color:var(--text);border:1px solid var(--border)}}
.btn-ghost:hover{{border-color:var(--gold)}}
.btn-vers{{background:rgba(245,200,66,.12);color:var(--gold);border:1px solid rgba(245,200,66,.35)}}
.btn-vers:hover{{background:rgba(245,200,66,.22)}}
.http{{font-size:.72rem;color:var(--muted);margin-top:8px}}
.http.err{{color:#f87171}}
.empty{{text-align:center;padding:60px;color:var(--muted);grid-column:1/-1}}
.legend{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:24px}}
.leg{{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px 16px;font-size:.82rem;color:var(--muted);line-height:1.5}}
.leg b{{color:var(--text);display:block;margin-bottom:4px}}
.featured{{margin-bottom:28px}}
.featured h2{{font-family:Syne,sans-serif;font-size:1.2rem;margin-bottom:14px;color:var(--gold)}}
.frow{{display:flex;gap:14px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x mandatory}}
.fcard{{flex:0 0 260px;scroll-snap-align:start;background:var(--surface);border:2px solid rgba(34,197,94,.35);
  border-radius:16px;overflow:hidden;cursor:pointer;transition:.2s}}
.fcard:hover{{transform:scale(1.02);box-shadow:var(--shadow)}}
.fcard img{{width:100%;height:120px;object-fit:cover}}
.fcard .fb{{padding:12px 14px}}
.fcard h4{{font-size:.95rem;margin-bottom:4px}}
.fcard small{{color:var(--muted);font-size:.75rem}}
.footer{{text-align:center;margin-top:32px;color:var(--muted);font-size:.8rem}}
a.portfolio{{display:inline-block;margin-top:12px;color:var(--gold);text-decoration:none;font-weight:600}}
@media(max-width:640px){{
  .header-actions{{position:static;justify-content:center;margin-bottom:14px}}
  .grid.list .card{{flex-direction:column}}
  .grid.list .cover{{width:100%;min-width:0;height:120px}}
}}
</style>
<script>(function(){{const t=localStorage.getItem('patlas-status-theme');if(t==='light')document.documentElement.setAttribute('data-theme','light');}})();</script>
</head>
<body>
<div class="wrap">
  <header>
    <div class="header-actions">
      <button class="icon-btn" id="themeBtn" type="button" title="מצב יום/לילה">🌙</button>
      <button class="icon-btn" id="viewBtn" type="button" title="תצוגת רשימה">☰</button>
      <button class="icon-btn" id="exportBtn" type="button" title="ייצוא JSON">⬇ JSON</button>
    </div>
    <h1>🗺️ מפת סטטוס פרויקטים</h1>
    <p>מה באמת עובד · מה דמו · מה בפיתוח — עודכן {generated}</p>
    <div class="health">
      <div class="health-track"><div class="health-fill" id="healthFill" style="width:{health_pct}%"></div></div>
      <span class="health-txt" id="healthTxt">{health_pct}% פרויקטים פעילים ({healthy}/{total})</span>
    </div>
    <a class="portfolio" href="{BASE_NETLIFY}portfolio.html" target="_blank">← תיק עבודות Patlas</a>
  </header>
  <div class="alert-banner" id="alertBanner" role="alert"></div>
  <div class="stats" id="stats"></div>
  <div class="legend">
    <div class="leg"><b>🟢 עובד מלא</b>אתר ייצור אמיתי — Netlify / GitHub Pages / PWA מלא</div>
    <div class="leg"><b>✅ עובד</b>דמו חי עם פונקציונליות אמיתית ב-Netlify</div>
    <div class="leg"><b>🟡 דמו / נראה</b>עמוד שנוצר/שוחזר — נראה טוב, תוכן מצומצם</div>
    <div class="leg"><b>🔵 בפיתוח</b>רק GitHub / צור קשר — אין דמו חי</div>
    <div class="leg"><b>🔴 שבור</b>URL לא נגיש או HTTP 4xx/5xx — דורש תיקון</div>
  </div>
  <div class="featured" id="featured"></div>
  <div class="toolbar">
    <div class="toolbar-row">
      <input class="search" id="q" type="search" placeholder="🔍 חפש פרויקט... (/)" autocomplete="off">
      <select class="sort" id="sort" aria-label="מיון">
        <option value="tier">מיון: סטטוס</option>
        <option value="name">מיון: שם</option>
        <option value="id">מיון: מזהה</option>
      </select>
    </div>
    <div class="chip-row"><span class="chip-label">סטטוס</span><div class="chips" id="chips"></div></div>
    <div class="chip-row"><span class="chip-label">תחום</span><div class="chips" id="catChips"></div></div>
  </div>
  <div class="grid" id="grid"></div>
  <p class="footer">נוצר אוטומטית מ-portfolio.html · לחיצה על כרטיס = פתיחה</p>
</div>
<script>
const DATA = {data};
const TIER_LABELS = {json.dumps({k:v['label'] for k,v in TIER_META.items()}, ensure_ascii=False)};
const CAT_LABELS = {json.dumps(CAT_LABELS, ensure_ascii=False)};
const ALL_CATS = {json.dumps(all_cats, ensure_ascii=False)};
const GENERATED = {json.dumps(generated, ensure_ascii=False)};
const NEWLY_BROKEN = {newly_json};
let filter = 'all';
let catFilter = 'all';
let viewMode = localStorage.getItem('patlas-status-view') || 'grid';

function esc(s){{ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }}
function catLabel(c){{ return CAT_LABELS[c] || c; }}

function renderStats(list) {{
  const c = {{full:0,works:0,demo:0,wip:0,broken:0}};
  list.forEach(r => c[r.tier]++);
  const healthy = c.full + c.works;
  const pct = list.length ? Math.round(healthy / list.length * 100) : 0;
  document.getElementById('healthFill').style.width = pct + '%';
  document.getElementById('healthTxt').textContent = pct + '% פרויקטים פעילים (' + healthy + '/' + list.length + ')';
  document.getElementById('stats').innerHTML = `
    <div class="stat"><b>${{list.length}}</b><span>סה"כ</span></div>
    <div class="stat"><b style="color:#22c55e">${{c.full}}</b><span>עובד מלא</span></div>
    <div class="stat"><b style="color:#4ade80">${{c.works}}</b><span>עובד</span></div>
    <div class="stat"><b style="color:#f5c842">${{c.demo}}</b><span>דמו / נראה</span></div>
    <div class="stat"><b style="color:#60a5fa">${{c.wip}}</b><span>בפיתוח</span></div>
    <div class="stat"><b style="color:#f87171">${{c.broken}}</b><span>שבור</span></div>`;
}}

function bindChips(sel, active, cls, onPick) {{
  document.querySelectorAll(sel).forEach(el => el.onclick = () => onPick(el.dataset.f));
  document.querySelectorAll(sel).forEach(el => {{
    el.classList.toggle('on', el.dataset.f === active);
    if (cls) el.classList.toggle(cls, el.dataset.f === active);
  }});
}}

function renderChips() {{
  const chips = [{{id:'all',label:'הכל ('+DATA.length+')'}},
    ...Object.entries(TIER_LABELS).map(([id,label]) => ({{id, label: label + ' ('+DATA.filter(r=>r.tier===id).length+')'}}))];
  document.getElementById('chips').innerHTML = chips.map(c =>
    `<button class="chip${{filter===c.id?' on':''}}" data-f="${{c.id}}">${{c.label}}</button>`).join('');
  bindChips('#chips .chip', filter, '', id => {{ filter = id; renderChips(); renderCatChips(); render(); }});
}}

function renderCatChips() {{
  const chips = [{{id:'all',label:'הכל'}}].concat(ALL_CATS.map(id => ({{
    id, label: catLabel(id) + ' (' + DATA.filter(r => r.cats.includes(id)).length + ')'
  }})));
  document.getElementById('catChips').innerHTML = chips.map(c =>
    `<button class="chip cat${{catFilter===c.id?' on':''}}" data-f="${{c.id}}">${{c.label}}</button>`).join('');
  bindChips('#catChips .chip', catFilter, 'cat', id => {{ catFilter = id; renderCatChips(); render(); }});
}}

function filtered() {{
  const q = document.getElementById('q').value.trim().toLowerCase();
  return DATA.filter(r => {{
    if (filter !== 'all' && r.tier !== filter) return false;
    if (catFilter !== 'all' && !r.cats.includes(catFilter)) return false;
    if (!q) return true;
    const hay = (r.name + r.desc + r.id + r.cats.map(catLabel).join(' ')).toLowerCase();
    return hay.includes(q);
  }});
}}

function sorted(list) {{
  const mode = document.getElementById('sort').value;
  const copy = list.slice();
  if (mode === 'name') return copy.sort((a,b) => a.name.localeCompare(b.name, 'he'));
  if (mode === 'id') return copy.sort((a,b) => a.id.localeCompare(b.id));
  return copy.sort((a,b) => a.tierOrder - b.tierOrder || a.name.localeCompare(b.name, 'he'));
}}

function httpLine(r) {{
  if (r.tier === 'broken') {{
    const detail = r.http ? ('HTTP ' + r.http) : (r.httpErr || 'לא נגיש');
    return '<div class="http err">🔴 ' + esc(detail) + '</div>';
  }}
  if (r.http) return '<div class="http">HTTP ' + r.http + '</div>';
  if (r.tier === 'wip') return '<div class="http">אין דמו חי</div>';
  return '';
}}

function renderAlerts() {{
  const el = document.getElementById('alertBanner');
  const broken = DATA.filter(r => r.tier === 'broken');
  if (!broken.length || localStorage.getItem('patlas-alert-dismiss') === GENERATED) {{
    el.style.display = 'none';
    el.innerHTML = '';
    return;
  }}
  el.style.display = 'block';
  const items = broken.map(r => {{
    const isNew = NEWLY_BROKEN.includes(r.id);
    const detail = r.http ? ('HTTP ' + r.http) : (r.httpErr || 'לא נגיש');
    return `<button type="button" class="alert-item" data-id="${{esc(r.id)}}">${{r.icon}} ${{esc(r.name)}} · ${{esc(detail)}}${{isNew ? ' <span class="alert-new">חדש!</span>' : ''}}</button>`;
  }}).join('');
  el.innerHTML = `<div class="alert-inner">
    <div class="alert-title">🔴 ${{broken.length}} פרויקטים שבורים — דורשים תיקון</div>
    <div class="alert-items">${{items}}</div>
    <div class="alert-actions">
      <button type="button" class="alert-btn" id="alertFilterBtn">הצג רק שבורים</button>
      <button type="button" class="alert-btn" id="alertDismissBtn">הסתר</button>
    </div>
  </div>`;
  document.getElementById('alertFilterBtn').onclick = () => {{
    filter = 'broken';
    renderChips();
    renderCatChips();
    render();
    document.getElementById('grid').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }};
  document.getElementById('alertDismissBtn').onclick = () => {{
    localStorage.setItem('patlas-alert-dismiss', GENERATED);
    renderAlerts();
  }};
  el.querySelectorAll('.alert-item').forEach(btn => {{
    btn.onclick = () => {{
      document.getElementById('q').value = btn.dataset.id;
      filter = 'all';
      renderChips();
      renderCatChips();
      render();
    }};
  }});
}}

function setView(mode) {{
  viewMode = mode;
  localStorage.setItem('patlas-status-view', mode);
  const g = document.getElementById('grid');
  g.classList.toggle('list', mode === 'list');
  document.getElementById('viewBtn').textContent = mode === 'list' ? '▦' : '☰';
  document.getElementById('viewBtn').title = mode === 'list' ? 'תצוגת כרטיסים' : 'תצוגת רשימה';
}}

function toggleTheme() {{
  const light = document.documentElement.getAttribute('data-theme') === 'light';
  if (light) {{
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('patlas-status-theme', 'dark');
    document.getElementById('themeBtn').textContent = '🌙';
  }} else {{
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('patlas-status-theme', 'light');
    document.getElementById('themeBtn').textContent = '☀️';
  }}
}}

function initTheme() {{
  const light = document.documentElement.getAttribute('data-theme') === 'light';
  document.getElementById('themeBtn').textContent = light ? '☀️' : '🌙';
}}

function exportJson() {{
  const list = sorted(filtered());
  const payload = {{
    generated: GENERATED,
    exported: new Date().toISOString(),
    filter: {{ tier: filter, category: catFilter, query: document.getElementById('q').value.trim() }},
    stats: {{ total: list.length, full: list.filter(r=>r.tier==='full').length, works: list.filter(r=>r.tier==='works').length }},
    projects: list
  }};
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'patlas-status-' + new Date().toISOString().slice(0, 10) + '.json';
  a.click();
  URL.revokeObjectURL(a.href);
}}

function render() {{
  const list = sorted(filtered());
  renderStats(list);
  renderAlerts();
  const g = document.getElementById('grid');
  g.classList.toggle('list', viewMode === 'list');
  if (!list.length) {{ g.innerHTML = '<div class="empty">לא נמצאו פרויקטים</div>'; return; }}
  g.innerHTML = list.map(r => `
    <article class="card ${{r.tier}}" data-url="${{esc(r.url)}}" tabindex="0">
      <div class="cover">
        <img src="${{esc(r.preview)}}" alt="" loading="lazy" onerror="this.style.display='none';this.parentElement.style.background='linear-gradient(135deg,hsl(${{r.id.length*40}},60%,35%),hsl(${{r.id.length*40+40}},50%,22%)')">
        <div class="badges">
          <span class="badge" style="background:${{r.tierColor}}22;color:${{r.tierColor}};border-color:${{r.tierColor}}44">${{r.tierIcon}} ${{r.tierLabel}}</span>
          ${{r.dedicated ? '<span class="badge dedicated">🌐 ייעודי</span>' : ''}}
        </div>
      </div>
      <div class="body">
        <div class="meta">${{(r.cats||[]).filter(t=>t!=='live').slice(0,4).map(t=>`<span class="tag">${{catLabel(t)}}</span>`).join('')}}</div>
        <h3>${{r.icon}} ${{esc(r.name)}}</h3>
        <p>${{esc(r.desc)}}</p>
        <div class="actions">
          <a class="btn btn-vers" href="{BASE_NETLIFY}portfolio.html?versions=${{encodeURIComponent(r.id)}}" target="_blank" rel="noopener" onclick="event.stopPropagation()">היסטוריית גרסאות</a>
          ${{r.url ? `<a class="btn btn-primary" href="${{esc(r.url)}}" target="_blank" rel="noopener" onclick="event.stopPropagation()">פתח</a>` : ''}}
          ${{r.gh ? `<a class="btn btn-ghost" href="${{esc(r.gh)}}" target="_blank" rel="noopener" onclick="event.stopPropagation()">GitHub</a>` : ''}}
        </div>
        ${{httpLine(r)}}
      </div>
    </article>`).join('');
  g.querySelectorAll('.card').forEach(card => {{
    const open = () => {{ const u = card.dataset.url; if (u) window.open(u,'_blank'); }};
    card.onclick = open;
    card.onkeydown = e => {{ if (e.key==='Enter') open(); }};
  }});
}}

function renderFeatured() {{
  const top = DATA.filter(r => r.tier === 'full').slice(0, 6);
  document.getElementById('featured').innerHTML = top.length ? `
    <h2>⭐ פרויקטים מובילים — עובדים מלא</h2>
    <div class="frow">${{top.map(r => `
      <div class="fcard" data-url="${{esc(r.url)}}" tabindex="0">
        <img src="${{esc(r.preview)}}" alt="" loading="lazy">
        <div class="fb"><h4>${{r.icon}} ${{esc(r.name)}}</h4><small>${{r.tierLabel}}${{r.dedicated ? ' · 🌐' : ''}}</small></div>
      </div>`).join('')}}</div>` : '';
  document.querySelectorAll('.fcard').forEach(c => {{
    const open = () => {{ if (c.dataset.url) window.open(c.dataset.url,'_blank'); }};
    c.onclick = open; c.onkeydown = e => {{ if (e.key==='Enter') open(); }};
  }});
}}

document.getElementById('q').oninput = render;
document.getElementById('sort').onchange = render;
document.getElementById('themeBtn').onclick = toggleTheme;
document.getElementById('viewBtn').onclick = () => setView(viewMode === 'grid' ? 'list' : 'grid');
document.getElementById('exportBtn').onclick = exportJson;
document.addEventListener('keydown', e => {{
  if (e.key === '/' && document.activeElement !== document.getElementById('q')) {{
    e.preventDefault();
    document.getElementById('q').focus();
  }}
}});
initTheme();
setView(viewMode);
renderChips();
renderCatChips();
renderFeatured();
render();
</script>
</body>
</html>'''


def main():
    html = open(PORTFOLIO, encoding='utf-8').read()
    catalog = parse_catalog(html)
    print(f'Parsed {len(catalog)} projects, checking URLs (parallel)...')
    prev = load_prev_state()
    rows = build_rows(catalog)
    newly_broken = find_newly_broken(rows, prev)
    save_state(rows)
    generated = datetime.now().strftime('%d.%m.%Y %H:%M')
    out = render_html(rows, generated, newly_broken)
    for path in (OUT_HTML, OUT_NETLIFY):
        open(path, 'w', encoding='utf-8').write(out)
    dedicated = sum(1 for r in rows if r['dedicated'])
    print('Wrote', OUT_HTML)
    print('Wrote', OUT_NETLIFY)
    print(f'  🌐 דומיין ייעודי: {dedicated}')
    for tier in TIER_META:
        n = sum(1 for r in rows if r['tier'] == tier)
        print(f'  {TIER_META[tier]["icon"]} {TIER_META[tier]["label"]}: {n}')
    if newly_broken:
        print('  ⚠️  נשברו עכשיו:', ', '.join(f"{r['id']} ({r['name']})" for r in newly_broken))
    broken = [r for r in rows if r['tier'] == 'broken']
    if broken and not newly_broken:
        print('  🔴 שבורים:', ', '.join(r['id'] for r in broken))


if __name__ == '__main__':
    main()