#!/usr/bin/env python3
"""Add a browser-tab icon and a page description to the <head> of every page.

  python3 tools/add_head_meta.py            # this site (the folder containing tools/)
  python3 tools/add_head_meta.py ../VST_P3_P4   # another site folder

Safe to re-run: the tags sit between <!-- head-meta:start/end --> markers and are replaced, not duplicated.
Line endings (LF or CRLF) of each file are preserved. *_backup.html and *_app.html (iframe content) are skipped.
Also creates images/favicon-32.png and images/apple-touch-icon.png from images/logo.png if they are missing.
"""
import re, sys, glob, os, html

SITE = '(VST)²: Variable Source Time delays with the VST'
SECTION_DESC = {
    '_page': 'VST light curves of the lensed quasar {t}.',
    '_shift_page': 'VST light curves of the lensed quasar {t}.',
    '_td': 'Time-delay measurements for the lensed quasar {t} from VST monitoring.',
    '_agn': 'VST light curves of AGN in the field of {t}.',
    '_anc': 'Ancillary data for the lensed quasar {t}: discovery paper, spectroscopy and HST/JWST imaging.',
}
FIXED = {
    'index.html': 'VST monitoring of strongly lensed quasars to measure time delays.',
    'people.html': 'The team behind the (VST)² programme.',
    'data.html': 'Data products, access and target coordinates of the (VST)² monitoring campaign.',
}

def description(name):
    if name in FIXED:
        return FIXED[name]
    m = re.match(r'(J\d{4}[+-]\d{4})(_shift_page|_page|_td|_agn|_anc)\.html$', name)
    return SECTION_DESC[m.group(2)].format(t=m.group(1)) if m else None

def make_icons(site):
    src = os.path.join(site, 'images', 'logo.png')
    targets = {os.path.join(site, 'images', 'favicon-32.png'): 32, os.path.join(site, 'images', 'apple-touch-icon.png'): 180}
    if all(os.path.exists(p) for p in targets) or not os.path.exists(src):
        return
    from PIL import Image
    im = Image.open(src).convert('RGBA')
    for p, n in targets.items():
        if not os.path.exists(p):
            im.resize((n, n), Image.LANCZOS).save(p, optimize=True); print('created', os.path.relpath(p, site))

def process(site):
    make_icons(site)
    for f in sorted(glob.glob(os.path.join(site, '*.html'))):
        name = os.path.basename(f)
        if name.endswith('_backup.html') or name.endswith('_app.html'):
            continue
        desc = description(name)
        if desc is None:
            print('skip (unknown page type)', name); continue
        raw = open(f, 'rb').read(); crlf = b'\r\n' in raw
        s = raw.decode('utf-8').replace('\r\n', '\n')
        block = ('<!-- head-meta:start -->\n'
                 f'    <meta name="description" content="{html.escape(desc + " " + SITE, quote=True)}" />\n'
                 '    <link rel="icon" type="image/png" sizes="32x32" href="images/favicon-32.png" />\n'
                 '    <link rel="apple-touch-icon" href="images/apple-touch-icon.png" />\n'
                 '    <!-- head-meta:end -->')
        # remove any existing copies, then insert exactly one right after </title>
        base = re.sub(r'\n?[ \t]*<!-- head-meta:start -->.*?<!-- head-meta:end -->', '', s, flags=re.S)
        assert base.count('</title>') == 1, name
        new = base.replace('</title>', '</title>\n    ' + block, 1)
        if new != s:
            if crlf: new = new.replace('\n', '\r\n')
            tmp = f + '.tmp'; open(tmp, 'wb').write(new.encode('utf-8')); os.replace(tmp, f)
            print('updated', name)

if __name__ == '__main__':
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for site in (sys.argv[1:] or [here]):
        print('==', os.path.abspath(site)); process(os.path.abspath(site))
