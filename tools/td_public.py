#!/usr/bin/env python3
"""Build the blind "Time Delays" overview page of the PUBLIC site (one page, no plots).

  python3 tools/td_public.py ../VST_P3_P4        # run from the internal site root (~/Sites/website)

* Reads the image pairs and delays from T in tools/build_td.py, but writes ONLY the status and the
  relative precision (1 sigma / |delay|) into the page - never the delay values.
* A target listed in UNBLIND below shows its values instead (use it once the paper is out).
* Page = <public>/time_delays.html, built from <public>/data.html (head, menu, footer); content between
  <!-- td-public:start/end -->, CSS between /* td-public-css:start/end */. Idempotent.
* Adds a "Time Delays" menu item (before "Data") to every public page that has the menu.
* Makes light JPG copies of the cutouts (<t>_cutout_web.jpg); click opens the full PNG.
* Stops if any blinded delay value ends up in the page.
"""
import os, re, sys, glob, importlib.util
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # internal site root
PUB = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'VST_P3_P4'))

spec = importlib.util.spec_from_file_location('build_td', os.path.join(HERE, 'tools', 'build_td.py'))
bt = importlib.util.module_from_spec(spec); cwd = os.getcwd(); spec.loader.exec_module(bt); os.chdir(cwd)
T = bt.T

ORDER = ['J0501-0733', 'J0542-2125', 'J0722-3901', 'J1029+2623', 'J2107-1611',
         'J0335-1927', 'J1330+1810', 'J2329-1258', 'J0123-0455']          # same order as menu / Data page

UNBLIND = set()          # e.g. {'J0542-2125'} -> show the delay values of that target

# Targets without TD results, and per-target overrides
EXTRA = {
    'J2107-1611': dict(badge='P3 Monitoring', images='Lensed images A1&ndash;A3, B and C',
                       cutout=('J2107-1611_cutout.png', 'HST/F160W cutout with images A1&ndash;A3, B and C marked.'),
                       pending=('No variability', '')),
    'J0123-0455': dict(badge='P4-P5 Monitoring', images='Two lensed images (A, B)',
                       cutout=('J0123-0455_cutout.png', 'HST/F814W cutout with images A and B marked.'),
                       pending=('In progress', 'Monitoring ongoing.')),
    'J0335-1927': dict(pending=('In progress', '')),
}
PRELIM = {'J2329-1258': 'Preliminary values: monitoring ongoing, not final.'}   # status "Preliminary" + note
PREC = {('J0542-2125', 'A-B'): '&lt; 3%', ('J2329-1258', 'A-B'): '&lt; 10%'}                                     # precision shown instead of the computed one
EVAL = {'J0501-0733': 'Two candidate solutions are still being compared.'}   # status "Under evaluation", no precision
GROUP = {'Literature': 'Archival light curves'}                                 # solution label shown on the page

def dash(p): return p.replace('-', '&ndash;')

def prec(v, e):
    e = sum(float(x) for x in e.split('/')) / len(e.split('/'))
    p = 100 * e / abs(float(v))
    return ('%.1f%%' % p) if p < 10 else ('%d%%' % round(p))

def pcls(v, e):
    e = sum(float(x) for x in e.split('/')) / len(e.split('/'))
    p = 100 * e / abs(float(v))
    return 'p-hi' if p < 5 else ('p-mid' if p < 15 else 'p-lo')

def value(v, e):
    if '/' in e:
        a, b = e.split('/'); return '%s <sup>+%s</sup><sub>&minus;%s</sub> d' % (v.replace('-', '&minus;'), a, b)
    return '%s &plusmn; %s d' % (v.replace('-', '&minus;'), e)

def cutout_web(t, png):
    src = os.path.join(PUB, 'images', t + '_VST', png)
    if not os.path.exists(src): return None
    from PIL import Image
    if Image.open(src).width <= 640: return None          # already small: use it as it is
    web = src.rsplit('.', 1)[0] + '_web.jpg'
    if not os.path.exists(web) or os.path.getmtime(web) < os.path.getmtime(src):
        from PIL import Image
        im = Image.open(src).convert('RGB')
        w = 640; im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        im.save(web, quality=86, optimize=True)
    return 'images/%s_VST/%s' % (t, os.path.basename(web))

HST_DIR = os.path.join(HERE, '..', '..', 'VST', 'HST_cutouts')               # ~/VST/HST_cutouts (hst_cutouts.py output)

def card(t):
    d = dict(T.get(t, {})); d.update(EXTRA.get(t, {}))
    png, cap = d['cutout']
    dst = os.path.join(PUB, 'images', t + '_VST', png)
    src = os.path.join(HST_DIR, png)
    if not os.path.exists(dst) and os.path.exists(src):                        # new HST cutout -> copy it to the site
        import shutil; shutil.copy2(src, dst)
    if not os.path.exists(dst) and t in T:                                      # not there yet -> keep the old figure
        png, cap = T[t]['cutout']
    web = cutout_web(t, png)
    full = 'images/%s_VST/%s' % (t, png)
    img = ('<img src="%s" data-full="%s" alt="Image of %s" loading="lazy" width="640" data-zoom>' % (web or full, full, t))
    rows = []
    blind = t not in UNBLIND
    if 'pending' in d:
        chip, txt = d['pending']
        rows.append('<p class="tdp-pending"><span class="tdp-st st-wait">%s</span> %s</p>' % (chip, txt))
    else:
        sols = d['sols']
        if t in EVAL:
            pairs = sols[0]['delays']
            rows.append('<ul class="tdp-pairs">')
            for p, v, e in pairs:
                rows.append('<li><span class="tdp-pair">%s</span><span class="tdp-st st-eval">Under evaluation</span>'
                            '<span class="tdp-prec">&mdash;</span></li>' % dash(p))
            rows.append('</ul>')
            d['note'] = EVAL[t]
        else:
            rows.append('<ul class="tdp-pairs">')
            for s in sols:
                if len(sols) > 1:
                    lab = GROUP.get(s.get('name', ''), s.get('name', ''))
                    sub = ''
                    if s.get('sub'):
                        m = re.search(r'<a [^>]*>.*?</a>', s['sub'])
                        sub = ' &middot; ' + m.group(0) if m else ''
                    rows.append('<li class="tdp-group">%s%s</li>' % (lab, sub))
                for p, v, e in s['delays']:
                    if blind:
                        right = '<span class="tdp-prec %s" title="Relative precision">%s</span>' % (pcls(v, e), PREC.get((t, p), prec(v, e)))
                    else:
                        right = '<span class="tdp-prec tdp-val">%s</span>' % value(v, e)
                    chip = '<span class="tdp-st st-prelim">Preliminary</span>' if t in PRELIM else '<span class="tdp-st st-ok">Measured</span>'
                    rows.append('<li><span class="tdp-pair">%s</span>%s%s</li>' % (dash(p), chip, right))
            rows.append('</ul>')
    if t in PRELIM: d['note'] = ((d.get('note') or '') + ' ' + PRELIM[t]).strip()
    note = '<p class="tdp-note">%s</p>' % d['note'] if d.get('note') else ''
    head = ('<div class="tdp-head"><h3>%s</h3><span class="tdp-badge">%s</span></div>'
            '<p class="tdp-sub">%s</p>' % (t, d['badge'], re.sub(r'\s*&middot;.*', '', d['images'])))
    if blind or 'pending' in d:
        colhead = '<div class="tdp-cols"><span>Pair</span><span>Status</span><span>Precision</span></div>' if 'pending' not in d else ''
    else:
        colhead = '<div class="tdp-cols"><span>Pair</span><span>Status</span><span>Time delay</span></div>'
    return ('<article class="tdp-card" id="%s">\n<figure class="tdp-fig">%s<figcaption>%s</figcaption></figure>\n'
            '<div class="tdp-body">%s%s%s%s</div>\n</article>' % (t, img, cap, head, colhead, '\n'.join(rows), note))

CSS = r'''/* td-public-css:start */
        .tdp-page { max-width: 1100px; margin: 0 auto; padding: 10px 20px 40px; color: #334155; }
        .tdp-intro { max-width: 760px; margin: 0 auto 2.2rem; text-align: center; color: #475569; line-height: 1.65; font-size: 1rem; }
        .tdp-intro .tdp-blind { display: inline-flex; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.04em;
            text-transform: uppercase; color: #6366c9; background: rgba(163,165,236,0.18); border: 1px solid rgba(163,165,236,0.6);
            border-radius: 999px; padding: 3px 12px; margin-bottom: 12px; }
        .tdp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(470px, 1fr)); gap: 22px; }
        .tdp-card { display: grid; grid-template-columns: 190px 1fr; gap: 20px; align-items: start; background: #fff;
            border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin: 0; text-align: left; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); }
        .tdp-fig { margin: 0; }
        .tdp-fig img { width: 100%; height: auto; display: block; border-radius: 6px; background: #000; cursor: zoom-in; }
        .tdp-fig figcaption { font-size: 0.74rem; color: #64748b; text-align: center; margin-top: 7px; line-height: 1.4; }
        .tdp-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; }
        .tdp-head h3 { margin: 0; font-size: 1.15rem; color: #0f172a; letter-spacing: 0.01em; text-transform: none; }
        .tdp-badge { font-size: 0.7rem; font-weight: 600; color: #6366c9; background: rgba(163,165,236,0.18); border: 1px solid rgba(163,165,236,0.6); border-radius: 999px; padding: 1px 10px; white-space: nowrap; }
        .tdp-sub { margin: 4px 0 12px; font-size: 0.86rem; color: #64748b; line-height: 1.4; }
        .tdp-cols, .tdp-pairs li { display: grid; grid-template-columns: 4.6em 1fr auto; gap: 8px; align-items: center; }
        .tdp-cols { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8;
            padding: 0 2px 5px; border-bottom: 1px solid #e2e8f0; }
        .tdp-cols span:last-child { text-align: right; }
        .tdp-pairs { list-style: none; margin: 0; padding: 0; }
        .tdp-pairs li { padding: 7px 2px; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
        .tdp-pairs li.tdp-group { display: block; font-size: 0.75rem; font-weight: 600; color: #475569; padding: 10px 2px 3px; border-bottom: 0; }
        .tdp-pairs li.tdp-group a { font-weight: 500; }
        .tdp-pair { font-weight: 600; color: #0f172a; white-space: nowrap; }
        .tdp-st { justify-self: start; font-size: 0.72rem; font-weight: 600; border-radius: 999px; padding: 2px 9px; white-space: nowrap; }
        .st-ok { color: #15803d; background: #dcfce7; }
        .st-eval { color: #b45309; background: #fef3c7; }
        .st-wait { color: #475569; background: #f1f5f9; }
        .tdp-prec { font-variant-numeric: tabular-nums; font-weight: 600; text-align: right; white-space: nowrap; color: #334155; }
        .st-prelim { color: #6366c9; background: rgba(163,165,236,0.18); }
        .tdp-val { color: #0f172a; }
        .tdp-pending { margin: 8px 0 0; font-size: 0.9rem; color: #64748b; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
        .tdp-note { margin: 10px 0 0; font-size: 0.8rem; color: #64748b; line-height: 1.45; }
        .tdp-foot { max-width: 760px; margin: 2rem auto 0; text-align: center; font-size: 0.8rem; color: #94a3b8; line-height: 1.6; }
        .tdp-lightbox { position: fixed; inset: 0; background: rgba(15,23,42,0.88); display: none; align-items: center; justify-content: center; z-index: 10000; padding: 20px; cursor: zoom-out; }
        .tdp-lightbox.open { display: flex; }
        .tdp-lightbox img { max-width: 100%; max-height: 100%; border-radius: 6px; }
        .tdp-lightbox button { position: absolute; top: 12px; right: 16px; background: none; border: 0; color: #fff; font-size: 2rem; line-height: 1; cursor: pointer; padding: 4px 10px; box-shadow: none; }
        @media (max-width: 1100px) { .tdp-grid { grid-template-columns: 1fr; max-width: 680px; margin: 0 auto; } }
        @media (max-width: 560px) {
            .tdp-page { padding: 0 4px 30px; }
            .tdp-card { grid-template-columns: 1fr; padding: 16px; gap: 14px; }
            .tdp-fig { max-width: 260px; margin: 0 auto; }
        }
        /* td-public-css:end */'''

def content():
    cards = '\n'.join(card(t) for t in ORDER)
    return '''<!-- td-public:start -->
                            <div class="hero-brand-section">
                                <h1 class="hero-title">
                                    <span class="dark-text">Time Delays</span>
                                </h1>
                            </div>
                            <div class="tdp-page">
                                <div class="tdp-intro">
                                    <span class="tdp-blind">Blind analysis</span><br>
                                    Time delays between the lensed quasar images from the (VST)&sup2; light curves.
                                    The values are kept blind until publication: for each image pair we give the status of the measurement
                                    and its relative precision.
                                </div>
                                <div class="tdp-grid">
%s
                                </div>
                                <p class="tdp-foot">Click an image to enlarge it.</p>
                            </div>
                            <div class="tdp-lightbox" id="tdp-lightbox" aria-hidden="true"><button aria-label="Close">&times;</button><img alt=""></div>
                            <script>
                                (function () {
                                    var lb = document.getElementById('tdp-lightbox'), im = lb.querySelector('img');
                                    document.querySelectorAll('.tdp-fig img[data-zoom]').forEach(function (i) {
                                        i.addEventListener('click', function () { im.src = i.dataset.full || i.src; im.alt = i.alt; lb.classList.add('open'); lb.setAttribute('aria-hidden', 'false'); });
                                    });
                                    function close() { lb.classList.remove('open'); lb.setAttribute('aria-hidden', 'true'); im.removeAttribute('src'); }
                                    lb.addEventListener('click', close);
                                    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
                                })();
                            </script>
                            <!-- td-public:end -->''' % cards

PUBLISH = False      # False: menu item kept as an HTML comment on every page (page not linked), True: visible
NAV_ITEM = '<li><a href="time_delays.html">Time Delays</a></li>'
NAV_HIDDEN = '<!-- ' + NAV_ITEM + ' -->'
DATA_LI = re.compile(r'([ \t]*)<li(\s+class="[^"]*")?\s*>\s*<a href="data.html">Data</a>\s*</li>')

def add_nav(html, nl):
    want, other = (NAV_ITEM, NAV_HIDDEN) if PUBLISH else (NAV_HIDDEN, NAV_ITEM)
    if want in html: return html
    if other in html: return html.replace(other, want)            # switch commented <-> visible
    m = DATA_LI.search(html)
    if not m: return html
    return html[:m.start()] + m.group(1) + want + nl + html[m.start():]

def main():
    src = open(os.path.join(PUB, 'data.html'), encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in src else '\n'
    a, b = src.index('<!-- Hero Section -->'), src.index('<!-- End Data Sections -->') + len('<!-- End Data Sections -->')
    page = src[:a] + content().replace('\n', nl) + src[b:]
    page = re.sub(r'<title>.*?</title>', '<title>VST P3-P5 - Time Delays</title>', page, count=1)
    page = re.sub(r'(<meta name="description" content=")[^"]*', r'\1Status and precision of the time-delay measurements of the (VST)&#178; monitoring campaign (values kept blind). (VST)&#178;: Variable Source Time delays with the VST', page, count=1)
    page = add_nav(page, nl)
    page = page.replace('<li class="current_page_item" ><a href="data.html">Data</a></li>', '<li><a href="data.html">Data</a></li>')
    page = page.replace(NAV_HIDDEN, NAV_ITEM).replace(NAV_ITEM, '<li class="current_page_item"><a href="time_delays.html">Time Delays</a></li>')
    i = page.index('</style>')
    page = page[:i] + '    ' + CSS.replace('\n', nl) + nl + '    ' + page[i:]
    # leak check: no blinded delay value may appear in that target's card (nor anywhere outside the cards)
    outside = re.sub(r'<article class="tdp-card".*?</article>', '', page, flags=re.S)
    for t in ORDER:
        if t in UNBLIND: continue
        own = re.search(r'<article class="tdp-card" id="%s">.*?</article>' % re.escape(t), page, re.S).group(0)
        for s in T.get(t, {}).get('sols', []):
            for p, v, e in s['delays']:
                num = v.lstrip('+-')
                if any(re.search(r'(?<![\d.])%s(?![\d])' % re.escape(num), x) for x in (own, outside)):
                    sys.exit('STOP: blinded value %s (%s %s) found in the page' % (num, t, p))
    open(os.path.join(PUB, 'time_delays.html'), 'w', encoding='utf-8', newline='').write(page)
    print('wrote', os.path.join(PUB, 'time_delays.html'))
    n = 0
    for f in sorted(glob.glob(os.path.join(PUB, '*.html'))):
        if f.endswith('_backup.html') or f.endswith('time_delays.html'): continue
        h = open(f, encoding='utf-8', newline='').read()
        h2 = add_nav(h, '\r\n' if '\r\n' in h else '\n')
        if h2 != h:
            open(f, 'w', encoding='utf-8', newline='').write(h2); n += 1
    print('menu item added to', n, 'pages')

if __name__ == '__main__':
    main()
