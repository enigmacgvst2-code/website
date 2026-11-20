#!/usr/bin/env python3
"""Create "not available yet" placeholder pages, so menu links never lead to a missing page.

  python3 tools/coming_soon.py td  J2107-1611     # -> J2107-1611_td.html  "Time delay not available yet"
  python3 tools/coming_soon.py agn J1330+1810     # -> J1330+1810_agn.html "AGN light curves not available yet"

Refuses to overwrite an existing page unless it is itself a placeholder. Templates: J2329-1258_td.html
(time delays) and J2107-1611_agn.html (an AGN page with no data). The menu highlight and the <head>
description are set for the new target. When results arrive, use build_td.py / build_agn.py instead.
"""
import re, os, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
import sync_nav_from_index as S

def coming_soon_td(t):
    src = open('J2329-1258_td.html').read()
    style = re.search(r'<style>.*?</style>', src, re.S).group(0)
    main = f'''<div id="main-wrapper">
                    <div class="wrapper style1">
                        <div class="inner">

                            <section class="td-page">
                                <header class="td-header">
                                    <span class="badge">Time delays</span>
                                    <h3>Time Delay Results for {t}</h3>
                                </header>
                                <div class="td-card soon">
                                    <p class="soon-title">Time delay not available yet</p>
                                    <p class="soon-text">Results for {t} will appear here once available.</p>
                                </div>
                            </section>

                        </div>
                    </div>
                </div>


            '''
    style = style.replace('        </style>', '            .td-card.soon { text-align: center; padding: 56px 24px; border-style: dashed; }\n            .soon-title { font-size: 1.15rem; font-weight: 700; color: #0f172a; margin: 0 0 6px; }\n            .soon-text { color: #64748b; margin: 0; }\n        </style>', 1)
    out = re.sub(r'<style>.*?</style>', lambda m: style, src, count=1, flags=re.S)
    out = re.sub(r'<div id="main-wrapper">.*?(?=<div id="footer-wrapper-logo">)', lambda m: main, out, count=1, flags=re.S)
    out = re.sub(r'<script>\s*\(function \(\) \{.*?</script>\s*', '', out, count=1, flags=re.S)        # drop tab/zoom script
    out = re.sub(r'<div class="lightbox".*?</div>\s*', '', out, count=1, flags=re.S)
    out = re.sub(r'<title>.*?</title>', f'<title>VST P3-P5 - Time Delays ({t})</title>', out, count=1)
    out, _ = S.replace_nav(out, S.set_current_page_item(S.extract_nav(out), f'{t}_td.html'))
    return out

def coming_soon_agn(t):
    src = open('J2107-1611_agn.html').read()        # already an empty AGN page in the new layout
    out = src.replace('J2107-1611', t)
    # restore the nav exactly (only the current item should differ)
    nav = S.extract_nav(src)
    out, _ = S.replace_nav(out, S.set_current_page_item(nav, f'{t}_agn.html'))
    return out


if __name__ == '__main__':
    kind, targets = sys.argv[1], sys.argv[2:]
    assert kind in ('td', 'agn') and targets, __doc__
    for t in targets:
        p = f'{t}_{kind}.html'
        def is_placeholder(path):
            h = open(path, encoding='utf-8').read()
            return 'td-card soon' in h if kind == 'td' else re.search(r'id="agn-data">\s*\[\s*\]\s*</script>', h) is not None
        if os.path.exists(p) and not is_placeholder(p):
            sys.exit(f'{p} already exists and is not a placeholder; not overwriting')
        html = coming_soon_td(t) if kind == 'td' else coming_soon_agn(t)
        tmp = p + '.tmp'; open(tmp, 'w', encoding='utf-8').write(html); os.replace(tmp, p)
        print('wrote', p)
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'add_head_meta.py'), ROOT], check=True, stdout=subprocess.DEVNULL)
