# -*- coding: utf-8 -*-
import re
path = r'C:\Users\DAVID\Desktop\פרויקטים\תיק עבודות\portfolio.html'
html = open(path, encoding='utf-8').read()

STATUS_URL = "https://storied-alfajores-6f10d2.netlify.app/status-dashboard.html"
LINK = f'''        <a href="#" class="archive-link" data-open-preview="{STATUS_URL}" data-preview-title="מפת סטטוס פרויקטים" data-i18n-preview="arch_status_title"><i data-lucide="map"></i><span data-i18n="arch_status">מפת סטטוס</span></a>
'''

if 'arch_status' not in html:
    html = html.replace(
        '        <a href="#" class="archive-link" data-open-preview="https://storied-alfajores-6f10d2.netlify.app/about/portfolio.html"',
        LINK + '        <a href="#" class="archive-link" data-open-preview="https://storied-alfajores-6f10d2.netlify.app/about/portfolio.html"'
    )
    html = html.replace("arch_about:'תיק מפורט',", "arch_about:'תיק מפורט',arch_status:'מפת סטטוס',arch_status_title:'מפת סטטוס פרויקטים',")
    html = html.replace("arch_about:'Full portfolio',", "arch_about:'Full portfolio',arch_status:'Status map',arch_status_title:'Project status map',")
    html = html.replace("arch_about:'Полное портфолио',", "arch_about:'Полное портфолио',arch_status:'Карта статусов',arch_status_title:'Карта статусов проектов',")

# hero button
HERO_BTN = '''          <a href="#" class="btn btn-outline" data-open-preview="''' + STATUS_URL + '''" data-preview-title="מפת סטטוס"><i data-lucide="map"></i><span data-i18n="arch_status">מפת סטטוס</span></a>
'''
if 'status-dashboard.html' not in html.split('hero-spotlight')[0] or html.count('status-dashboard') < 2:
    html = html.replace(
        '          <a href="https://github.com/DavidPatlas-AI" target="_blank" class="btn btn-outline"><i data-lucide="github"></i><span>GitHub</span></a>',
        HERO_BTN + '          <a href="https://github.com/DavidPatlas-AI" target="_blank" class="btn btn-outline"><i data-lucide="github"></i><span>GitHub</span></a>'
    )

html = html.replace('id="statCatalog" data-count="40">40', 'id="statCatalog" data-count="43">43')
html = html.replace("arch_sub'>41+ בתיק", "arch_sub'>43 בתיק")
html = html.replace('arch_sub">41+ בתיק', 'arch_sub">43 בתיק')

open(path, 'w', encoding='utf-8').write(html)
print('Patched portfolio.html')