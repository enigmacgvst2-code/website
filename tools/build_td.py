#!/usr/bin/env python3
"""Build the time-delay pages (<target>_td.html).

  python3 tools/build_td.py               # rebuild every target listed in T below
  python3 tools/build_td.py J0335-1927    # rebuild one target

Each page is rebuilt from its current version: only the <style>, the <title> and the main content
(<div id="main-wrapper"> ... footer) are replaced; the logo, menu, footer and <head> tags stay as they are.
To publish results for a target that still has a "Time delay not available yet" page, add it to T and run.
Values are the black "combined tau=0.50" row of the PyCS3 marginalisation plot.
"""
import re, os, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # site root

STYLE = r'''<style>
            .lowercase { text-transform: lowercase; }

            .td-page { max-width: 1040px; margin: 0 auto; padding: 40px 20px; color: #334155; }

            /* Header */
            .td-header { text-align: center; margin-bottom: 36px; }
            .td-header .badge {
                display: inline-block; padding: 4px 14px; margin-bottom: 12px;
                background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; border-radius: 20px;
                font-size: 0.8rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
            }
            .td-header h3 { font-size: 2.1rem; color: #0f172a; font-weight: 700; margin: 0 0 8px; letter-spacing: -0.02em; }
            .td-page .td-header .subtitle { font-size: 0.95rem; color: #64748b; margin: 0; letter-spacing: 0; text-transform: none; font-weight: 400; }

            /* Card shell */
            .td-card {
                background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
                box-shadow: 0 4px 20px -2px rgba(0,0,0,0.04); padding: 24px;
            }
            .td-card h4 {
                font-size: 0.8rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
                color: #64748b; margin: 0 0 16px;
            }
            .td-page .td-card h4 { font-size: 0.8rem !important; letter-spacing: 0.06em !important; margin: 0 0 16px !important; }

            /* Summary: cutout + delay values */
            .td-summary { display: grid; grid-template-columns: 320px 1fr; gap: 24px; margin-bottom: 28px; }
            .td-cutout { margin: 0; }
            .td-cutout img { width: 100%; height: auto; display: block; border-radius: 8px; background: #000; cursor: zoom-in; }
            .td-cutout figcaption { font-size: 0.85rem; color: #64748b; text-align: center; margin-top: 10px; line-height: 1.5; }

            .td-delays { display: flex; flex-direction: column; }
            .delay-list { display: grid; gap: 12px; flex: 1; align-content: center; }
            .delay-row {
                display: flex; align-items: baseline; justify-content: space-between; gap: 12px;
                padding: 16px 20px; border: 1px solid #f1f5f9; border-radius: 10px; background: #f8fafc;
            }
            .delay-row .pair { font-weight: 700; color: #0f172a; font-size: 1.05rem; white-space: nowrap; }
            .delay-row .pair span { color: #94a3b8; font-weight: 400; margin: 0 2px; }
            .delay-row .value { font-variant-numeric: tabular-nums; font-size: 1.6rem; font-weight: 700; color: #0f172a; white-space: nowrap; }
            .delay-row .value .err { font-size: 1rem; font-weight: 400; color: #64748b; margin-left: 4px; }
            .delay-row .value .unit { font-size: 0.9rem; font-weight: 400; color: #64748b; margin-left: 4px; }
            .td-note { font-size: 0.85rem; color: #64748b; margin: 16px 0 0; line-height: 1.5; }

            /* Tabbed figure viewer */
            .tab-bar { display: flex; gap: 6px; border-bottom: 1px solid #e2e8f0; margin: -4px 0 20px; flex-wrap: wrap; }
            /* reset the theme's global button style */
            .td-page .tab-bar button {
                -webkit-appearance: none; appearance: none;
                background: none; background-image: none; box-shadow: none; text-shadow: none;
                border: 0; border-bottom: 2px solid transparent; border-radius: 0;
                height: auto; line-height: 1.4; min-width: 0;
                padding: 10px 14px; margin-bottom: -1px;
                font-family: inherit; font-size: 0.95rem; font-weight: 600;
                text-transform: none; letter-spacing: 0;
                color: #64748b !important; cursor: pointer;
            }
            .td-page .tab-bar button:hover { color: #0f172a !important; background: none; }
            .td-page .tab-bar button[aria-selected="true"] { color: #2563eb !important; border-bottom-color: #2563eb; }
            .tab-panel { margin: 0; }
            .tab-panel[hidden] { display: none; }
            .tab-panel img { width: 100%; height: auto; display: block; border-radius: 6px; cursor: zoom-in; }
            .tab-panel figcaption {
                display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;
                font-size: 0.95rem; color: #475569; line-height: 1.6; padding-top: 16px; margin-top: 16px; border-top: 1px solid #f1f5f9;
            }
            .tab-panel figcaption strong { color: #0f172a; }
            .fullres { font-size: 0.85rem; color: #2563eb; text-decoration: none; white-space: nowrap; border: 0; }
            .fullres:hover { text-decoration: underline; }

            /* Lightbox */
            .lightbox {
                position: fixed; inset: 0; z-index: 10000; display: none; align-items: center; justify-content: center;
                background: rgba(15,23,42,0.88); padding: 24px; cursor: zoom-out;
            }
            .lightbox.open { display: flex; }
            .lightbox img { max-width: 100%; max-height: 100%; border-radius: 6px; background: #fff; box-shadow: 0 10px 40px rgba(0,0,0,0.4); }
            .lightbox .close {
                position: absolute; top: 14px; right: 20px; color: #fff; font-size: 2rem; line-height: 1;
                background: none; border: 0; cursor: pointer;
            }

            @media (max-width: 760px) {
                .td-summary { grid-template-columns: 1fr; }
                .td-cutout { max-width: 360px; margin: 0 auto; }
                .td-header h3 { font-size: 1.6rem; }
                .delay-row .value { font-size: 1.3rem; }
            }

            /* Two-solution layout */
            .solution-list { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; flex: 1; align-content: center; }
            .td-page .solution {
                -webkit-appearance: none; appearance: none; text-align: left; cursor: pointer;
                background: #f8fafc; background-image: none; box-shadow: none; text-shadow: none;
                border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 18px;
                height: auto; line-height: 1.4; min-width: 0; text-transform: none; letter-spacing: 0;
                font-family: inherit; font-weight: 400; font-size: 1rem; color: #334155 !important;
                transition: border-color .15s ease, background-color .15s ease;
            }
            .td-page .solution:hover { border-color: #cbd5e1; background: #f1f5f9; }
            .td-page .solution[aria-pressed="true"] { border-color: #2563eb; background: #eff6ff; box-shadow: 0 0 0 1px #2563eb inset; }
            .solution .sol-name { display: block; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #64748b; margin-bottom: 10px; }
            .solution[aria-pressed="true"] .sol-name { color: #2563eb; }
            .solution .sol-row { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
            .solution .sol-row + .sol-row { margin-top: 6px; }
            .solution .pair { font-weight: 700; color: #0f172a; white-space: nowrap; }
            .solution .pair span { color: #94a3b8; font-weight: 400; margin: 0 2px; }
            .solution .value { font-variant-numeric: tabular-nums; font-size: 1.5rem; font-weight: 700; color: #0f172a; white-space: nowrap; }
            .solution .value .err, .solution .value .unit { font-size: 0.9rem; font-weight: 400; color: #64748b; margin-left: 4px; }

            .viewer-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; border-bottom: 1px solid #e2e8f0; margin: -4px 0 20px; }
            .viewer-head .tab-bar { border-bottom: 0; margin: 0; }
            .segmented { display: inline-flex; background: #f1f5f9; border-radius: 8px; padding: 3px; margin-bottom: 8px; }
            .td-page .segmented button {
                -webkit-appearance: none; appearance: none; background: none; background-image: none; box-shadow: none; text-shadow: none;
                border: 0; border-radius: 6px; padding: 6px 12px; height: auto; line-height: 1.4; min-width: 0;
                font-family: inherit; font-size: 0.85rem; font-weight: 600; text-transform: none; letter-spacing: 0;
                color: #64748b !important; cursor: pointer;
            }
            .td-page .segmented button[aria-pressed="true"] { background: #fff; color: #0f172a !important; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }

            @media (max-width: 760px) {
                .solution-list { grid-template-columns: 1fr; }
                .viewer-head { flex-direction: column-reverse; align-items: stretch; }
                .segmented { align-self: flex-start; margin: 0 0 4px; }
            }

            /* Disabled tab (view not available for the selected solution) */
            .td-page .tab-bar button[disabled] { color: #cbd5e1 !important; cursor: not-allowed; }

            /* Placeholder shown when a plot file is missing */
            .plot-missing {
                display: none; align-items: center; justify-content: center; min-height: 220px;
                border: 1px dashed #cbd5e1; border-radius: 8px; background: #f8fafc;
                color: #94a3b8; font-size: 0.95rem;
            }
            .tab-panel.missing img, .tab-panel.missing .fullres { display: none; }
            .tab-panel.missing .plot-missing { display: flex; }

            .solution .sol-sub { display: block; font-size: 0.8rem; color: #64748b; margin: -6px 0 10px; line-height: 1.4; }
            .solution .sol-sub a { color: #2563eb; }
            .err.asym { display: inline-flex; flex-direction: column; vertical-align: middle; line-height: 1.05; font-size: 0.8rem !important; }
            .err.asym sup, .err.asym sub { position: static; font-size: inherit; vertical-align: baseline; }
            .solution .value.na { font-size: 1rem; font-weight: 400; color: #94a3b8; }
        </style>'''

def fmt(v):
    if v is None: return None
    return ('&minus;' + v[1:]) if v.startswith('-') else ('+' + v.lstrip('+'))

def pair(p):
    a, b = p.split('-', 1)
    return f'{a}<span>&ndash;</span>{b}'

# ----------------------------------------------------------------------------------
# Target configuration. Values are the black "combined" row (tau = 0.50) of each delay plot.
# ----------------------------------------------------------------------------------
T = {
 'J0335-1927': dict(badge='VST P3-P5 Monitoring', images='Three lensed images (A, B, C)',
    cutout=('J0335-1927_cutout.png', 'HST/F625W cutout with images A, B and C marked.'),
    sols=[dict(delays=[('A-B','-210.9','19.8'),('A-C','+267.9','17.5'),('B-C','+472.1','20.1')],
               plots={'delays':'marginalisation_spline_sigma_0.50.png','curves':'multi_plot_combinations.png'})]),
 'J0501-0733': dict(badge='VST P3 Monitoring', images='Two lensed images (A, B)',
    cutout=('color.jpg', 'RGB image from <a href="https://alasky.cds.unistra.fr/DESI-legacy-surveys/DR10/CDS_P_DESI-Legacy-Surveys_DR10_color/" target="_blank">DESI Legacy Survey DR10</a>.'),
    sols=[dict(name='Solution 1', delays=[('A-B','-104.2','12.7')],
               plots={'delays':'marginalisation_spline_sigma_0.50.png','curves':'J0501_match_td1.png'}),
          dict(name='Solution 2', delays=[('A-B','-52.4','8.5')],
               plots={'delays':'marginalisation_spline_sigma_0.50_2.png','curves':'J0501_match_td2.png'})]),
 'J0542-2125': dict(badge='VST P3-P4 Monitoring', images='Three lensed images (A, B, C) &middot; delay measured between A and B',
    cutout=('J0542-2125_cutout.png', 'HST/F160W cutout with images A, B and C marked.'),
    sols=[dict(delays=[('A-B','+20.6','0.5')],
               plots={'delays':'marginalisation_spline_sigma_0.50.png','curves':'plot_ab.png'})]),
 'J0722-3901': dict(badge='VST P3 Monitoring', images='Four lensed images (A, B, C, D)',
    cutout=('J0722-3901_cutout.png', 'HST/F160W cutout with images A, B, C and D marked.'),
    note='B and C are measured together as a single light curve (BC).',
    sols=[dict(delays=[('A-BC','-9.4','2.8'),('A-D','-5.2','3.7'),('BC-D','+4.3','2.6')],
               plots={'delays':'marginalisation_spline_sigma_0.50.png','curves':'multi_plot_combinations.png'})]),
 'J1029+2623': dict(badge='VST P3-P4 Monitoring', images='Three lensed images (A, B, C)',
    cutout=('J1029+2623_cutout.png', 'HST/F160W cutout with images A, B and C marked.'),
    sols=[dict(name='VST monitoring', delays=[('B-C','-9.1','1.0')],
               plots={'delays':'marginalisation_spline_sigma_0.50.png','curves':'plot_bc.png'}),
          dict(name='Literature',
               sub='A vs (BC) using data from <a href="https://iopscience.iop.org/article/10.1088/0004-637X/764/2/186" target="_blank" rel="noopener noreferrer">Fohlmeister et al. 2013</a>',
               delays=[('A-(BC)', '-748.6', '26.0/24.3')],
               plots={'delays':'marginalisation_spline_sigma_0.50_f.png','curves':'plot_a_bc.png'})]),
 'J1330+1810': dict(badge='VST P4 Monitoring', images='Four lensed images (A, B, C, D)',
    cutout=('J1330+1810_cutout.png', 'HST/F160W cutout with images A, B, C and D marked.'),
    note='A and B are measured together as a single light curve (AB).',
    sols=[dict(delays=[('AB-C','+9.8','1.3'),('AB-D','-16.1','2.7'),('C-D','-25.9','3.1')],
               plots={'delays':'marginalisation_spline_sigma_0.50.png','curves':'multi_plot_combinations.png'})]),
 'J2329-1258': dict(badge='VST P4-P5 Monitoring', images='Two lensed images (A, B)',
    cutout=('J2329-1258_cutout.png', 'HST/F814W cutout with images A and B marked.'),
    sols=[dict(delays=[('A-B','-46.9','5.5')],
               plots={'delays':'marginalisation_spline_sigma_0.50.png','curves':'multi_plot.png'})]),
}

VIEWS = [('delays', 'Time-delay estimates'), ('curves', 'Matched light curves')]

def build_section(name, c):
    IMG = f'images/{name}_VST/'
    multi = len(c['sols']) > 1
    out = []
    out.append(f'''<section class="td-page">
                                <header class="td-header">
                                    <span class="badge">{c['badge']}</span>
                                    <h3>Time Delay Results for {name}</h3>
                                    <p class="subtitle">{c['images']} &middot; PyCS3{' &middot; two possible solutions' if name=='J0501-0733' else ''}</p>
                                </header>

                                <div class="td-summary">
                                    <div class="td-card">
                                        <h4>Lensed images</h4>
                                        <figure class="td-cutout">
                                            <img src="{IMG}{c['cutout'][0]}" alt="Image of {name}" loading="lazy" data-zoom>
                                            <figcaption>{c['cutout'][1]}</figcaption>
                                        </figure>
                                    </div>

                                    <div class="td-card td-delays">
                                        <h4>Combined time delays</h4>
                                        <!-- Values: black "combined" row of the delay plot (tau = 0.50). Update when the analysis is re-run. -->''')
    def rows(sol, cls):
        r = []
        for p, v, e in sol['delays']:
            if v is None:
                val = '<span class="value na">see plot</span>'
            else:
                if '/' in e:
                    up, dn = e.split('/')
                    err = f'<span class="err asym"><sup>+{up}</sup><sub>&minus;{dn}</sub></span>'
                else:
                    err = f'<span class="err">&plusmn; {e}</span>'
                val = f'<span class="value">{fmt(v)}{err}<span class="unit">days</span></span>'
            r.append(f'''
                                                <span class="{cls}">
                                                    <span class="pair">{pair(p)}</span>
                                                    {val}
                                                </span>''')
        return ''.join(r)
    if multi:
        out.append('\n                                        <div class="solution-list">')
        for i, s in enumerate(c['sols'], 1):
            sub = f'\n                                                <span class="sol-sub">{s["sub"]}</span>' if s.get('sub') else ''
            out.append(f'''
                                            <div class="solution" role="button" tabindex="0" data-sol="{i}" aria-pressed="{'true' if i==1 else 'false'}">
                                                <span class="sol-name">{s['name']}</span>{sub}{rows(s, 'sol-row')}
                                            </div>''')
        out.append('\n                                        </div>')
        tail = ' Select one to show its plots below.' if multi else ''
    else:
        out.append('\n                                        <div class="delay-list">')
        out.append(rows(c['sols'][0], 'delay-row').replace('<span class="delay-row">', '<div class="delay-row">').replace('</span>\n                                                </span>', '</span>\n                                                </div>'))
        out.append('\n                                        </div>')
        tail = ''
    note = (' ' + c['note']) if c.get('note') else ''
    out.append(f'''
                                        <p class="td-note">Combined estimate (&tau; = 0.50) over all PyCS3 spline configurations.{note}{tail}</p>
                                    </div>
                                </div>

                                <div class="td-card">
                                    <div class="viewer-head">
                                        <div class="tab-bar" role="tablist" aria-label="Time delay plots">''')
    for k, (v, label) in enumerate(VIEWS):
        out.append(f'''
                                            <button role="tab" data-view="{v}" aria-selected="{'true' if k==0 else 'false'}"{'' if k==0 else ' tabindex="-1"'}>{label}</button>''')
    out.append('\n                                        </div>')
    if multi:
        out.append('\n                                        <div class="segmented" role="group" aria-label="Solution">')
        for i, s in enumerate(c['sols'], 1):
            out.append(f'\n                                            <button data-sol="{i}" aria-pressed="{"true" if i==1 else "false"}">{s["name"]}</button>')
        out.append('\n                                        </div>')
    out.append('\n                                    </div>')
    fig = 0
    for i, s in enumerate(c['sols'], 1):
        for v, label in VIEWS:
            if v not in s['plots']: continue
            fig += 1
            f = s['plots'][v]
            which = f" ({s['name']})" if multi else ''
            if v == 'delays':
                cap = f'Time delay measurements for each PyCS3 configuration{which}; black is the combined estimate.'
            else:
                cap = f'Light curves shifted by the combined time delay{"s" if len(s["delays"])>1 else ""}{which}.'
            hidden = '' if fig == 1 else ' hidden'
            out.append(f'''
                                    <figure class="tab-panel" data-sol="{i}" data-view="{v}" role="tabpanel"{hidden}>
                                        <img src="{IMG}{f}" alt="{label} for {name}{which}" loading="lazy" data-zoom onerror="this.parentNode.classList.add('missing')">
                                        <div class="plot-missing">Plot not available yet</div>
                                        <figcaption>
                                            <span><strong>Figure {fig}:</strong> {cap}</span>
                                            <a class="fullres" href="{IMG}{f}" target="_blank">Full resolution &#8599;</a>
                                        </figcaption>
                                    </figure>''')
    out.append('''
                                </div>
                            </section>''')
    return ''.join(out)

SCRIPT = '''
        <div class="lightbox" id="lightbox" aria-hidden="true">
            <button class="close" aria-label="Close">&times;</button>
            <img alt="">
        </div>
        <script>
            (function () {
                var panels = Array.prototype.slice.call(document.querySelectorAll('.tab-panel'));
                var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab-bar [role="tab"]'));
                var solBtns = Array.prototype.slice.call(document.querySelectorAll('.solution[data-sol], .segmented [data-sol]'));
                var state = { sol: panels.length ? panels[0].dataset.sol : '1', view: 'delays' };

                function has(sol, view) {
                    return panels.some(function (p) { return p.dataset.sol === sol && p.dataset.view === view; });
                }
                function render() {
                    if (!has(state.sol, state.view)) {
                        var t = tabs.filter(function (t) { return has(state.sol, t.dataset.view); })[0];
                        if (t) state.view = t.dataset.view;
                    }
                    tabs.forEach(function (t) {
                        var on = t.dataset.view === state.view;
                        t.disabled = !has(state.sol, t.dataset.view);
                        t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1;
                    });
                    solBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.sol === state.sol); });
                    panels.forEach(function (p) { p.hidden = !(p.dataset.sol === state.sol && p.dataset.view === state.view); });
                }

                tabs.forEach(function (t, i) {
                    t.addEventListener('click', function () { state.view = t.dataset.view; render(); });
                    t.addEventListener('keydown', function (e) {
                        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                            var n = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
                            if (!n.disabled) { state.view = n.dataset.view; render(); n.focus(); }
                        }
                    });
                });
                solBtns.forEach(function (b) {
                    b.addEventListener('click', function (e) {
                        if (e.target.closest('a')) return;   // let links inside a card work
                        state.sol = b.dataset.sol; render();
                    });
                    b.addEventListener('keydown', function (e) {
                        if ((e.key === 'Enter' || e.key === ' ') && b.classList.contains('solution')) { e.preventDefault(); state.sol = b.dataset.sol; render(); }
                    });
                });
                render();

                // Click-to-enlarge
                var box = document.getElementById('lightbox'), big = box.querySelector('img');
                document.querySelectorAll('img[data-zoom]').forEach(function (img) {
                    img.addEventListener('click', function () {
                        big.src = img.src; big.alt = img.alt;
                        box.classList.add('open'); box.setAttribute('aria-hidden', 'false');
                    });
                });
                function close() { box.classList.remove('open'); box.setAttribute('aria-hidden', 'true'); }
                box.addEventListener('click', close);
                document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
            })();
        </script>
'''

def strip_generated_script(s):
    # remove the tab/lightbox script this tool appended last time (sits right before </body>)
    return re.sub(r'\n[ \t]*<div class="lightbox" id="lightbox".*</script>\n\s*(?=</body>)', '', s, count=1, flags=re.S)

def build(name, c):
    path = f'{name}_td.html'
    src = strip_generated_script(open(path, encoding='utf-8').read())
    out = re.sub(r'<style>.*?</style>', lambda m: STYLE, src, count=1, flags=re.S)
    out = re.sub(r'<title>.*?</title>', f'<title>VST P3-P5 - Time Delays ({name})</title>', out, count=1)
    main = f'''<div id="main-wrapper">
                    <div class="wrapper style1">
                        <div class="inner">

                            {build_section(name, c)}

                        </div>
                    </div>
                </div>


            '''
    out, n = re.subn(r'<div id="main-wrapper">.*?(?=<div id="footer-wrapper-logo">)', lambda m: main, out, count=1, flags=re.S)
    assert n == 1, name
    assert out.count('</body>') == 1, name
    out = out.replace('</body>', SCRIPT + '\n    </body>', 1)
    # sanity: logo, menu, footer and the rest of <head> are unchanged
    def outside(s):
        s = re.sub(r'<style>.*?</style>', '', s, count=1, flags=re.S)
        s = re.sub(r'<title>.*?</title>', '', s, count=1)
        s = strip_generated_script(s)
        i, j = s.index('<div id="main-wrapper">'), s.index('<div id="footer-wrapper-logo">')
        return (s[:i] + s[j:]).split()
    assert outside(src) == outside(out), name
    tmp = path + '.tmp'; open(tmp, 'w', encoding='utf-8').write(out); os.replace(tmp, path)
    print('built', path)

if __name__ == '__main__':
    names = sys.argv[1:] or list(T)
    for n in names:
        if n not in T: sys.exit(f'{n}: not in T (add its values first)')
        build(n, T[n])
