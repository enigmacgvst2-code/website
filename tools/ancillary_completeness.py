#!/usr/bin/env python3
"""
"Ground-based Images Zeropoint and Completeness" + "HST/JWST Zeropoint and Completeness" cards on the Ancillary pages (internal site only): one for the ground-based
mosaics (completeness.csv), one for the HST/JWST images (completeness_hst_jwst.csv, data-anc-depth="2";
zeropoint word: PHOTFLAM for HST, PIXAR_SR for JWST, where the MJy/sr -> AB zeropoint is set by the pixel area).

  python3 tools/ancillary_completeness.py J0335-1927                    # insert/refresh the card in J0335-1927_anc.html
  python3 tools/ancillary_completeness.py J0335-1927 --out PREVIEW.html # write a copy of the page with the card instead
  python3 tools/ancillary_completeness.py                               # every target in completeness.csv

Reads ANCILLARY_DATA/completeness.csv (written by measure_completeness.py; nothing is re-measured) and
builds one table: per band the image source, PSF FWHM, the 90% and 80% completeness limits (AB, point
sources, +- bootstrap error on m90), the empty-aperture 5-sigma depth and the adopted zeropoint
(value + "measured" = calibrated on reference stars, or "nominal" = image header value, not yet calibrated).
The card carries data-anc-depth="1"; its CSS sits between /* anc-depth-css:start/end */. It goes after
the Color Image card (or after Survey Coverage). Idempotent. Before running tools/ancillary_extra.py on a
page that has this card, add  'Ground-based Images Zeropoint and Completeness': 101  and  'HST/JWST Zeropoint and Completeness': 102  to WAVE there (it stops on unknown titles).
Standard library only.
"""
import os, re, csv, argparse

TITLE = 'Ground-based Images Zeropoint and Completeness'
ORDER = ['u', 'g', 'r', 'i', 'z', 'Y', 'J', 'H', 'Ks', 'K']
# chip colours: u g r i z as on the Color Image card (tools/ancillary_color.py BANDS); Y J H K continue redwards
COLOR = {'u': '#1d4ed8', 'g': '#0369a1', 'r': '#15803d', 'i': '#b45309', 'z': '#991b1b', 'Y': '#a16207',
         'J': '#7c2d12', 'H': '#57534e', 'Ks': '#1f2937', 'K': '#1f2937'}
SURVEY = {'LS': 'Legacy Surveys DR10', 'VHS': 'VISTA VHS', 'UHS': 'UKIRT UHS', 'DES': 'DES DR2', 'SDSS': 'SDSS',
          'ATLAS': 'VST-ATLAS', 'DECAM': 'DECam', 'ADHOC': 'VST/OmegaCAM (ad hoc)'}
ZPREF = {'vhs': 'VHS', 'ls_dr10': 'LS DR10', 'sdss_dr17': 'SDSS DR17', 'atlas_er5': 'ATLAS ER5',
         'des_dr2': 'DES DR2', 'gaia_gspc': 'Gaia XP (GSPC)', 'uhs_dr3': 'UHS DR3'}
FILT_LABEL = {'Ks': 'K<sub>s</sub>'}

# ---- second card: HST/JWST images (ANCILLARY_DATA/completeness_hst_jwst.csv, measure_completeness_hst_jwst.py)
SPACE_TITLE = 'HST/JWST Zeropoint and Completeness'
INSTR = {'ACS': 'HST/ACS', 'WFC3UVIS': 'HST/WFC3-UVIS', 'WFC3IR': 'HST/WFC3-IR', 'NIRCAM': 'JWST/NIRCam',
         'MIRI': 'JWST/MIRI'}
NM = ('ACS', 'WFC3UVIS')   # filter number in nm (F606W); otherwise in 10 nm (F105W = 1.05 um, F560W = 5.6 um)
# rows in wavelength order; chip colours run along the card from violet (bluest filter) to deep dark red (reddest),
# one colour per filter, all dark enough for white text
GRADIENT = ['#6d28d9', '#4338ca', '#1d4ed8', '#0369a1', '#0f766e', '#15803d', '#4d7c0f', '#a16207', '#c2410c',
            '#b91c1c', '#7f1d1d']
# images of the same filter/instrument told apart by a label (from the FITS headers):
#   (field, suffix of <target>_<inst>_<filter>_<suffix>.fits): label; MAIN: label of the image without suffix
POINTING = {('J0542', 'CL2'): 'west field',        # 2nd WFC3/IR pointing, ~2.5' W of the lens (PID 17243)
            ('J2107', 'IFBI51010'): '26 Jun 2024',  # PID 17601, 2nd epoch
            ('J2107', 'IFBI51020'): '26 Jun 2024',
            ('J2107', 'IFBI51030'): '26 Jun 2024',
            ('J1330', 'IDGC06040'): '1.2 ks',       # PID 15320, 2nd F160W set of the same visit
            }
MAIN = {'J0542': 'lens field', 'J2107': '10 May 2024', 'J1330': '1.0 ks'}
# images left out of the card: (field, band label). J2329: only the 674 s F814W (jf56d3010, the image behind the
# website's F814W picture); the single 5 s subarray exposure jf56d3dmq is not shown (Marianna)
SKIP = {('J2329', 'F814W_ACS_JF56D3DMQ')}
# fields where only the deepest image (faintest m90) of each filter is shown, whatever the instrument or date (Marianna):
# J2107 -> F475X 26 Jun 2024, F814W ACS, F160W 26 Jun 2024; J1330 -> F814W ACS, F160W 1.2 ks; J2329 -> F814W 674 s
DEEPEST = {'J2107', 'J1330', 'J2329', 'J0335', 'J1029', 'J0501'}   # J0335/J1029: duplicates are same-pointing sets (PID 17726, 12195); J0501: 17308 + 17444 visits
I = ' ' * 24

def f(x):
    return float(x) if x not in ('', None) else float('nan')

def rows_for(t, data):
    with open(os.path.join(data, 'completeness.csv'), newline='') as fh:
        rows = [r for r in csv.DictReader(fh) if r['field'] == t[:5]]
    for r in rows:
        r['filt'], _, surv = r['band'].partition('_')
        r['surv'] = SURVEY.get(surv, surv)
    rows.sort(key=lambda r: ORDER.index(r['filt']) if r['filt'] in ORDER else 99)
    return rows

def rows_space(t, data):
    fn = os.path.join(data, 'completeness_hst_jwst.csv')
    if not os.path.exists(fn):
        return []
    key5 = t[:5]   # the CSV field is 'J0335' or, for fields without field_info.json, 'J0722-3901' / 'PS_J2107-1611'
    with open(fn, newline='') as fh:
        rows = [r for r in csv.DictReader(fh) if key5 in r['field'] and (key5, r['band']) not in SKIP]
    if key5 in DEEPEST:
        best = {}
        for r in rows:
            k = r['band'].split('_')[0]
            if k not in best or f(r['m90']) > f(best[k]['m90']):
                best[k] = r
        rows = [r for r in rows if best[r['band'].split('_')[0]] is r]
    n_same = {}
    for r in rows:
        k = tuple(r['band'].split('_')[:2]); n_same[k] = n_same.get(k, 0) + 1
    for r in rows:
        parts = r['band'].split('_')
        r['filt'], ins, suf = parts[0], parts[1], (parts[2] if len(parts) > 2 else '')
        lab = ('' if n_same[(r['filt'], ins)] < 2 else   # a label only when the filter/instrument appears twice
               POINTING.get((key5, suf), suf.lower()) if suf else MAIN.get(key5, 'main'))
        r['surv'] = INSTR.get(ins, ins) + (f' &middot; {lab}' if lab else '')
        n = int(re.sub(r'\D', '', r['filt']) or 0)
        r['key'] = (n if ins in NM else 10 * n, list(INSTR).index(ins) if ins in INSTR else 9, suf)
        r['wide'] = True
    rows.sort(key=lambda r: r['key'])
    filts = list(dict.fromkeys(r['filt'] for r in rows))   # filters in wavelength order
    for r in rows:
        i = filts.index(r['filt'])
        r['color'] = GRADIENT[round(i * (len(GRADIENT) - 1) / (len(filts) - 1)) if len(filts) > 1 else 0]
    return rows

WIDE = ' class="w"'

def chip(r):  # same look as the band chips of the Color Image card: band letter + image source
    return (f'<span class="cmp-chip" style="--band:{r.get("color") or COLOR.get(r["filt"], "#475569")}">'
            f'<b{WIDE if r.get("wide") else ""}>{FILT_LABEL.get(r["filt"], r["filt"])}</b>{r["surv"]}</span>')

def zp_html(r):
    v = f'{f(r["zp"]):.2f}'
    if r['zp_source'].startswith('header PIXAR_SR'):   # JWST: MJy/sr -> AB, set by the pixel area
        return f'{v} <span class="cmp-zp" title="from the pixel area in the header (PIXAR_SR), MJy/sr to AB">PIXAR_SR</span>'
    if r['zp_source'].startswith('header PHOTFLAM'):   # HST: header flux calibration
        return f'{v} <span class="cmp-zp" title="from PHOTFLAM/PHOTPLAM in the header">PHOTFLAM</span>'
    m = re.match(r'measured \((.*)\)', r['zp_source'])
    if m:
        return f'{v} <span class="cmp-zp" title="calibrated on {ZPREF.get(m.group(1), m.group(1))} stars">measured</span>'
    return f'{v} <span class="cmp-zp cmp-zp-hdr" title="nominal zeropoint from the image header, not yet calibrated on reference stars">nominal</span>'

def card(t, rows, title=TITLE, marker='1'):
    trs = ''.join(
        f'{I}                <tr>'
        f'<td>{chip(r)}</td>'
        f'<td data-label="PSF FWHM">{f(r["fwhm"]):.{2 if f(r["fwhm"]) >= 0.5 else 3}f}&Prime;</td>'
        f'<td data-label="90%" class="cmp-key">{f(r["m90"]):.2f} <small>&plusmn; {f(r["m90_err"]):.2f}</small></td>'
        f'<td data-label="80%">{f(r["m80"]):.2f}</td>'
        f'<td data-label="5&sigma; depth">{f(r["m5_emp"]):.2f}</td>'
        f'<td data-label="Zeropoint">{zp_html(r)}</td></tr>\n' for r in rows)
    return (
        f'{I}<section class="dataset-card card-spectrum card-depth" data-anc-depth="{marker}">\n'
        f'{I}    <div class="dataset-header">\n'
        f'{I}        <h2>{title}</h2>\n'
        f'{I}    </div>\n'
        f'{I}    <div class="cmp-wrap">\n'
        f'{I}        <table class="cmp-table">\n'
        f'{I}            <thead><tr><th>Band</th><th>PSF FWHM</th><th>90%</th><th>80%</th>'
        f'<th>5&sigma; depth</th><th>Zeropoint</th></tr></thead>\n'
        f'{I}            <tbody>\n{trs}'
        f'{I}            </tbody>\n'
        f'{I}        </table>\n'
        f'{I}    </div>\n'
        f'{I}</section>\n')

CSS = """            /* anc-depth-css:start */
            .card-depth {   /* = .card-spectrum of the Color Image card (tools/ancillary_color.py) */
                border-left: 6px solid transparent;
                background: linear-gradient(to bottom, #7c3aed, #2563eb, #10b981, #f59e0b, #dc2626) border-box left top / 6px 100% no-repeat,
                            linear-gradient(135deg, rgba(71, 85, 105, 0.05) 0%, #ffffff 100%) padding-box;
            }
            .card-depth .dataset-header h2 { color: #334155; }
            .card-depth .dataset-header { border-bottom-color: rgba(71, 85, 105, 0.2); }
            .cmp-chip { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px 2px 2px; border-radius: 14px;
                border: 1px solid var(--band); color: #334155; font-size: 0.92em; white-space: nowrap; }
            .cmp-chip b { display: inline-flex; align-items: center; justify-content: center; min-width: 22px; height: 22px;
                padding: 0 4px; box-sizing: border-box; border-radius: 11px; background: var(--band); color: #fff;
                font-weight: 700; font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 13px; line-height: 1; }
            .cmp-chip b.w { padding: 0 8px; font-size: 12px; font-weight: 600; letter-spacing: 0.04em;
                font-family: inherit; -webkit-font-smoothing: antialiased; }
            .cmp-chip b { text-shadow: none; }   /* the page wrapper adds a white text-shadow: blurs white-on-colour text */
            .cmp-chip b sub { font-size: 9px; vertical-align: baseline; position: relative; top: 2px; }
            .cmp-wrap { overflow-x: auto; }
            .cmp-table { width: 100%; border-collapse: collapse; font-size: 0.88em; margin: 0; font-variant-numeric: tabular-nums; }
            .cmp-table th { text-align: left; font-weight: 700; color: #334155; border-bottom: 2px solid rgba(71, 85, 105, 0.25);
                padding: 7px 9px; white-space: nowrap; }
            .cmp-table td { padding: 6px 9px; border-bottom: 1px solid #e2e8f0; color: #4a5568; white-space: nowrap; }
            .cmp-table tbody tr:last-child td { border-bottom: none; }
            .cmp-table td.cmp-key { font-weight: 700; color: #334155; }
            .cmp-table small { color: #94a3b8; font-weight: 400; }
            .cmp-zp { font-size: 0.85em; color: #64748b; }
            .cmp-zp-hdr { color: #991b1b; font-weight: 600; }
            @media (max-width: 768px) {
                .cmp-table thead { display: none; }
                .cmp-table, .cmp-table tbody, .cmp-table tr, .cmp-table td { display: block; width: 100%; }
                .cmp-table tr { display: grid; grid-template-columns: 1fr 1fr; column-gap: 12px;
                    border-bottom: 1px solid #e2e8f0; padding: 8px 0; }
                .cmp-table td { border: none; padding: 2px 0; white-space: normal; width: auto; }
                .cmp-table td:first-child, .cmp-table td:last-child { grid-column: 1 / -1; }
                .cmp-table td:not(:first-child)::before { content: attr(data-label) ": "; font-weight: 600; color: #718096; }
            }
            /* anc-depth-css:end */
"""
CARD_RE = re.compile(r'\n?[ \t]*<section class="dataset-card[^"]*" data-anc-depth="\d">.*?</section>\n', re.S)
CSS_RE = re.compile(r'[ \t]*/\* anc-depth-css:start \*/.*?/\* anc-depth-css:end \*/\n', re.S)
JS_RE = re.compile(r'<!-- anc-depth-js:start -->.*?<!-- anc-depth-js:end -->\n', re.S)  # first (plot) version
ANY_CARD_RE = re.compile(r'[ \t]*<section class="dataset-card[^"]*"[^>]*>.*?</section>\n', re.S)

def build(page, t, rows, space=()):
    # CSS goes just before the anc-extra block (tools/ancillary_extra.py re-adds its block last), so that
    # both tools leave each other's output unchanged
    page = CSS_RE.sub('', page)
    i = page.find('/* anc-extra-css:start */')
    if i < 0:
        i = page.index('</style>')
    i = page.rfind('\n', 0, i) + 1
    page = page[:i] + CSS + page[i:]
    page = JS_RE.sub('', CARD_RE.sub('', page))
    cards = list(ANY_CARD_RE.finditer(page))
    if not cards:
        raise SystemExit('no dataset cards found')
    after = (next((m for m in cards if '<h2>Color Image</h2>' in m.group(0)), None) or
             next((m for m in cards if '<h2>Survey Coverage</h2>' in m.group(0)), cards[-1]))
    new = (card(t, rows) if rows else '') + ('\n' + card(t, space, SPACE_TITLE, '2') if space else '')
    return page[:after.end()] + '\n' + new.lstrip('\n') + page[after.end():]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('targets', nargs='*')
    p.add_argument('--data', default=os.path.expanduser('~/VST/ANCILLARY_DATA'))
    p.add_argument('--site', default='.')
    p.add_argument('--out', help='write the result here instead of updating <target>_anc.html (one target only)')
    a = p.parse_args()
    targets = a.targets
    if not targets:
        fields = set()
        for name in ('completeness.csv', 'completeness_hst_jwst.csv'):
            if os.path.exists(os.path.join(a.data, name)):
                with open(os.path.join(a.data, name), newline='') as fh:
                    fields |= {r['field'] for r in csv.DictReader(fh)}
        targets = sorted(fn[:-9] for fn in os.listdir(a.site) if fn.endswith('_anc.html') and not fn.endswith('_backup_anc.html')
                         and any(fn[:5] in fld for fld in fields))
    if a.out and len(targets) != 1:
        raise SystemExit('--out needs exactly one target')
    for t in targets:
        rows, space = rows_for(t, a.data), rows_space(t, a.data)
        if not rows and not space:
            print('no completeness rows for', t); continue
        fn = os.path.join(a.site, f'{t}_anc.html')
        raw = open(fn, 'rb').read().decode('utf-8')
        crlf = '\r\n' in raw
        new = build(raw.replace('\r\n', '\n'), t, rows, space)
        out = a.out or fn
        if a.out:  # preview copy elsewhere: point relative links (css, images, menu) back at the site
            rel = os.path.relpath(os.path.abspath(a.site), os.path.dirname(os.path.abspath(out)))
            if rel != '.':
                new = new.replace('<head>', f'<head>\n        <base href="{rel}/">', 1)
            new = re.sub(r'<title>(.*?)</title>', r'<title>\1 (preview)</title>', new, count=1)
        if crlf: new = new.replace('\n', '\r\n')
        old = open(out, 'rb').read().decode('utf-8') if os.path.exists(out) else None
        if new != old:
            open(out, 'wb').write(new.encode('utf-8')); print('updated  ', out)
        else:
            print('unchanged', out)

if __name__ == '__main__':
    main()
