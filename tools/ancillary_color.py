#!/usr/bin/env python3
"""
VST colour-image card on the Ancillary pages (internal site for now).

  python3 tools/ancillary_color.py                     # every target in TARGETS, site = .
  python3 tools/ancillary_color.py J0542-2125          # one target
  python3 tools/ancillary_color.py --data ~/VST/ANCILLARY_DATA --site . J0542-2125
  python3 tools/ancillary_color.py --zoom-size 640    # views cut from the deep-look lens boxes (current look)

--zoom-size: cut the views from the box that make_color_images.py writes with
  --look deep --zoom-only --zoom <lens RA> <lens Dec> 640   (<field>_ugriz_zoom_<ra>_<dec>.png, ~15-30 s per field,
  uses the cached halo/ghost models in color/_work) instead of the full-field cube (default --look banner = darker).

For each target it reads the 8-bit RGB cube written by the colour-image scripts
(<field>/color/<field>_ugriz_cube.fits in ANCILLARY_DATA, sky orientation from its TAN WCS),
cuts two lens-centred views and writes them to images/<target>_VST/:
  vst_color_3arcmin.jpg   3' x 3' at the native 0.21" pixels
  vst_color_10arcmin.jpg  10' x 10' at the native pixels
and inserts (or refreshes) a "Color Image" card after the Survey Coverage card (last card).
The card carries data-anc-color="1"; its CSS sits between /* anc-color-css:start/end */ and the
small click-to-enlarge script between <!-- anc-color-js:start/end -->. Idempotent.
tools/ancillary_extra.py keeps this card (its title is in WAVE with rank 100).
Needs numpy and Pillow only (no astropy).
"""
import os, re, sys, math, argparse
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ancillary_extra import COORDS as LENS   # lens positions as on the pages
TARGETS = {  # target: (cube relative to ANCILLARY_DATA, u-band source)
    'J0335-1927': ('COOL_J0335-1927/color/COOL_J0335-1927_ugriz_cube.fits', 'VST-ATLAS'),
    'J0542-2125': ('COOL_J0542-2125/color/COOL_J0542-2125_ugriz_cube.fits', 'DECam'),
    'J1029+2623': ('SDSS_J1029+2623/color/SDSS_J1029+2623_ugriz_cube.fits', 'SDSS'),
}
VIEWS = [  # (file stem, size arcsec, output px or None = native, scale bar arcsec, bar label, caption)
    ('vst_color_10arcmin', 600, None, 60, '1&prime;', '10&prime; &times; 10&prime; field'),
    ('vst_color_3arcmin', 180, None, 30, '30&Prime;', '3&prime; &times; 3&prime; zoom on the lens'),
]
QUALITY = 88
# bands in wavelength order: (band, image source (None = TARGETS u source), chip colour = the band's hue in the
# colour recipe of make_color_images.py: u (0,0,1) g (0,.3,.7) r (.1,.8,.1) i (.6,.4,0) z (.5,0,0), darkened for white text)
BANDS = [('u', None, '#1d4ed8'), ('g', 'Legacy Surveys DR10', '#0369a1'), ('r', 'VST/OmegaCAM', '#15803d'),
         ('i', 'Legacy Surveys DR10', '#b45309'), ('z', 'Legacy Surveys DR10', '#991b1b')]
CHANNEL = {'u': 'blue', 'g': 'blue + green', 'r': 'green', 'i': 'red + green', 'z': 'red'}
I = ' ' * 24

def read_cube(fn):
    """Header dict, data offset and (3, ny, nx) uint8 memmap of a FITS RGB cube."""
    hdr, n = {}, 0
    with open(fn, 'rb') as f:
        while True:
            block = f.read(2880); n += 2880
            if not block:
                raise SystemExit('no END card in ' + fn)
            done = False
            for i in range(0, 2880, 80):
                c = block[i:i+80].decode('ascii', 'replace')
                k = c[:8].strip()
                if k == 'END':
                    done = True; break
                if c[8:10] == '= ':
                    v = c[10:].split('/')[0].strip()
                    hdr[k] = v.strip("'").strip() if v.startswith("'") else (float(v) if v not in ('T', 'F') else v)
            if done:
                break
    if hdr['BITPIX'] != 8 or hdr['NAXIS'] != 3 or hdr['NAXIS3'] != 3:
        raise SystemExit('expected an 8-bit 3-plane cube: ' + fn)
    nx, ny = int(hdr['NAXIS1']), int(hdr['NAXIS2'])
    return hdr, np.memmap(fn, dtype=np.uint8, mode='r', offset=n, shape=(3, ny, nx))

def wcs(hdr):
    """TAN world->pixel (0-based x, y) and pixel scale (arcsec); no rotation allowed."""
    if 'CD1_1' in hdr:
        a, b, c, d = hdr['CD1_1'], hdr.get('CD1_2', 0.0), hdr.get('CD2_1', 0.0), hdr['CD2_2']
    else:
        c1, c2 = hdr.get('CDELT1', 1.0), hdr.get('CDELT2', 1.0)
        a, b, c, d = hdr.get('PC1_1', 1.0)*c1, hdr.get('PC1_2', 0.0)*c1, hdr.get('PC2_1', 0.0)*c2, hdr.get('PC2_2', 1.0)*c2
    if abs(b) > 1e-3*abs(a) or abs(c) > 1e-3*abs(d):
        raise SystemExit('rotated WCS not supported')
    ra0, de0 = math.radians(hdr['CRVAL1']), math.radians(hdr['CRVAL2'])
    def w2p(ra, de):
        ra, de = math.radians(ra), math.radians(de)
        cc = math.sin(de0)*math.sin(de) + math.cos(de0)*math.cos(de)*math.cos(ra-ra0)
        xi = math.degrees(math.cos(de)*math.sin(ra-ra0)/cc)
        eta = math.degrees((math.cos(de0)*math.sin(de) - math.sin(de0)*math.cos(de)*math.cos(ra-ra0))/cc)
        return hdr['CRPIX1'] - 1 + xi/a, hdr['CRPIX2'] - 1 + eta/d
    return w2p, abs(d)*3600, a < 0, d > 0      # east-left?, north = +y?

def cut(cube, x, y, n):
    """n x n RGB box centred on (x, y), padded with black outside the mosaic; rows from FITS order."""
    _, ny, nx = cube.shape
    x0, y0 = int(round(x)) - n//2, int(round(y)) - n//2
    out = np.zeros((n, n, 3), np.uint8)
    xa, xb, ya, yb = max(x0, 0), min(x0+n, nx), max(y0, 0), min(y0+n, ny)
    if xa < xb and ya < yb:
        for k in range(3):
            out[ya-y0:yb-y0, xa-x0:xb-x0, k] = cube[k, ya:yb, xa:xb]
    return out

def zoom_source(cube_fn, hdr, w2p, scale, ra, de, size):
    """(3, h, w) array + pixel origin of the --zoom-only preview that make_color_images.py writes next to the
    cube (<base>_zoom_<ra>_<dec>.png, north up), rendered e.g. with --look deep; same geometry as that script."""
    from PIL import Image as _I
    fn = cube_fn[:-len('_cube.fits')] + '_zoom_%.4f_%+.4f.png' % (ra, de)
    if not os.path.exists(fn):
        raise SystemExit('missing %s - run: make_color_images.py --fields <F> --look deep --zoom-only --zoom %s %s %d'
                         % (fn, ra, de, size))
    _I.MAX_IMAGE_PIXELS = None
    a = np.asarray(_I.open(fn).convert('RGB'))[::-1]          # back to FITS row order (y up)
    xz, yz = w2p(ra, de); hs = int(size/scale/2)
    x0, y0 = max(int(xz)-hs, 0), max(int(yz)-hs, 0)
    if a.shape[0] != min(int(yz)+hs, int(hdr['NAXIS2']))-y0 or a.shape[1] != min(int(xz)+hs, int(hdr['NAXIS1']))-x0:
        raise SystemExit('zoom size %s does not match --zoom-size %d for %s' % (a.shape[:2], size, fn))
    return np.ascontiguousarray(a.transpose(2, 0, 1)), x0, y0

def make_images(t, data_dir, site_dir, zoom_size=None):
    rel, _ = TARGETS[t]
    hdr, cube = read_cube(os.path.join(data_dir, rel))
    w2p, scale, east_left, north_up_y = wcs(hdr)
    x, y = w2p(*LENS[t])
    if zoom_size:                                            # cut from the --zoom-only preview instead
        cube, x0, y0 = zoom_source(os.path.join(data_dir, rel), hdr, w2p, scale, *LENS[t], zoom_size)
        x, y = x-x0, y-y0
    info = {'scale': scale, 'field': (cube.shape[2]*scale/60, cube.shape[1]*scale/60), 'views': []}
    for stem, size, px, *_ in VIEWS:
        n = int(round(size/scale/2))*2
        a = cut(cube, x, y, n)
        if north_up_y: a = a[::-1]          # image rows go top-down: north up
        if not east_left: a = a[:, ::-1]    # east left
        im = Image.fromarray(np.ascontiguousarray(a))
        if px and px < n:
            im = im.resize((px, px), Image.LANCZOS)
        out = os.path.join(site_dir, 'images', f'{t}_VST', stem + '.jpg')
        im.save(out, quality=QUALITY, optimize=True, progressive=True)
        info['views'].append((stem, im.width))
        print(f'  {out}  {im.width} px  {os.path.getsize(out)//1024} KB')
    return info

COMPASS = ('<svg class="sky-compass" viewBox="0 0 44 44" aria-hidden="true">'
           '<path d="M36 36 V10 M36 36 H10" stroke="#fff" stroke-width="1.6" fill="none"/>'
           '<path d="M32.5 13 L36 7 L39.5 13 Z M13 32.5 L7 36 L13 39.5 Z" fill="#fff"/>'
           '<text x="36" y="5" text-anchor="middle">N</text><text x="3" y="40" text-anchor="middle">E</text></svg>')

def card(t, info):
    _, usrc = TARGETS[t]
    chips = ' '.join(f'<span class="band-chip" style="--band:{col}" title="{band} band: {CHANNEL[band]} channel">'
                     f'<b>{band}</b>{usrc if src is None else src}</span>' for band, src, col in BANDS)
    figs = []
    for (stem, size, _px, bar, barlab, cap), (_, width) in zip(VIEWS, info['views']):
        src = f'images/{t}_VST/{stem}.jpg'
        extra = ('' if size <= 180 else  # dashed box = the 3' view (no marks on the zoom, user)
                 f'{I}                    <span class="sky-box" style="width:{100*180/size:.3f}%;height:{100*180/size:.3f}%"></span>\n')
        figs.append(
            f'{I}        <figure class="data-figure sky-fig">\n'
            f'{I}            <a class="sky-zoom" href="{src}" title="Click to enlarge">\n'
            f'{I}                <span class="sky-frame">\n'
            f'{I}                    <img src="{src}" width="{width}" height="{width}" loading="lazy" '
            f'alt="u g r i z color image of {t}, {size//60}&prime; &times; {size//60}&prime;">\n'
            f'{extra}'
            f'{I}                    <span class="sky-scale" style="width:{100*bar/size:.3f}%"><span>{barlab}</span></span>\n'
            f'{I}                    {COMPASS}\n'
            f'{I}                </span>\n'
            f'{I}            </a>\n'
            f'{I}            <figcaption>{cap}.</figcaption>\n'
            f'{I}        </figure>\n')
    return (f'{I}<section class="dataset-card card-spectrum" data-anc-color="1">\n'
            f'{I}    <div class="dataset-header">\n'
            f'{I}        <h2>Color Image</h2>\n'
            f'{I}    </div>\n'
            f'{I}    <p class="prog-note">u g r i z color image of the field; click to enlarge.</p>\n'
            f'{I}    <div class="sky-pair">\n' + ''.join(figs) +
            f'{I}    </div>\n'
            f'{I}    <div class="meta-grid">\n'
            f'{I}        <div class="meta-item band-list"><span class="meta-label">Images:</span> {chips}</div>\n'
            f'{I}        <div class="meta-item"><span class="meta-label">Pixel scale:</span> {info["scale"]:.2f}&Prime;</div>\n'
            f'{I}    </div>\n'
            f'{I}</section>\n')

CSS = """            /* anc-color-css:start */
            .card-spectrum {
                border-left: 6px solid transparent;
                background: linear-gradient(to bottom, #7c3aed, #2563eb, #10b981, #f59e0b, #dc2626) border-box left top / 6px 100% no-repeat,
                            linear-gradient(135deg, rgba(71, 85, 105, 0.05) 0%, #ffffff 100%) padding-box;
            }
            .card-spectrum .dataset-header h2 { color: #334155; }
            .card-spectrum .dataset-header { border-bottom-color: rgba(71, 85, 105, 0.2); }
            .sky-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin: 10px 0 18px 0; }
            @media (max-width: 768px) { .sky-pair { grid-template-columns: 1fr; } }
            .sky-fig { margin: 0; }
            .sky-zoom { display: block; border: none; cursor: zoom-in; }
            .sky-frame { position: relative; display: block; line-height: 0; border-radius: 6px; overflow: hidden; background: #000; }
            .sky-frame img { display: block; width: 100%; height: auto; border-radius: 0 !important; }
            .sky-scale { position: absolute; left: 4%; bottom: 5%; height: 2px; background: #fff; }
            .sky-scale span { position: absolute; left: 0; right: 0; bottom: 6px; text-align: center; color: #fff;
                font-size: 12px; line-height: 1; font-weight: 600; text-shadow: 0 0 3px #000; white-space: nowrap; }
            .sky-compass { position: absolute; right: 3%; bottom: 3%; width: 44px; height: 44px; overflow: visible; }
            .sky-compass text { fill: #fff; font-size: 10px; font-weight: 700; font-family: sans-serif; }
            .sky-box { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
                border: 1px dashed rgba(255, 255, 255, 0.8); }
            .sky-light { position: fixed; inset: 0; z-index: 10000; background: rgba(0, 0, 0, 0.9);
                display: flex; align-items: center; justify-content: center; cursor: zoom-out; }
            .sky-light img { max-width: 94vw; max-height: 94vh; border-radius: 4px; }
            .band-list { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
            .band-chip { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px 2px 2px; border-radius: 14px;
                border: 1px solid var(--band); color: #334155; font-size: 0.92em; white-space: nowrap; }
            .band-chip b { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px;
                border-radius: 50%; background: var(--band); color: #fff; font-weight: 700;
                font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 13px; line-height: 1; }
            /* anc-color-css:end */
"""
JS = """<!-- anc-color-js:start -->
<script>
document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a.sky-zoom');
    if (!a) return;
    e.preventDefault();
    var box = document.createElement('div');
    box.className = 'sky-light';
    var img = document.createElement('img');
    img.src = a.getAttribute('href'); img.alt = '';
    box.appendChild(img);
    function close() { box.remove(); document.removeEventListener('keydown', esc); }
    function esc(ev) { if (ev.key === 'Escape') close(); }
    box.addEventListener('click', close);
    document.addEventListener('keydown', esc);
    document.body.appendChild(box);
});
</script>
<!-- anc-color-js:end -->
"""
CARD_RE = re.compile(r'\n?[ \t]*<section class="dataset-card[^"]*" data-anc-color="1">.*?</section>\n', re.S)
CSS_RE = re.compile(r'[ \t]*/\* anc-color-css:start \*/.*?/\* anc-color-css:end \*/\n', re.S)
JS_RE = re.compile(r'<!-- anc-color-js:start -->.*?<!-- anc-color-js:end -->\n', re.S)
ANY_CARD_RE = re.compile(r'[ \t]*<section class="dataset-card[^"]*"[^>]*>.*?</section>\n', re.S)

def build(page, t, info):
    """Refresh the card, CSS and script in place when present (stable with tools/ancillary_extra.py)."""
    c = card(t, info)
    if CSS_RE.search(page):
        page = CSS_RE.sub(lambda m: CSS, page, count=1)
    else:
        i = page.index('</style>'); i = page.rfind('\n', 0, i) + 1
        page = page[:i] + CSS + page[i:]
    page = CARD_RE.sub('', page)
    cards = list(ANY_CARD_RE.finditer(page))
    if not cards:
        raise SystemExit('no dataset cards found')
    after = next((m for m in cards if '<h2>Survey Coverage</h2>' in m.group(0)), cards[-1])
    page = page[:after.end()] + '\n' + c + page[after.end():]
    if JS_RE.search(page):
        page = JS_RE.sub(lambda m: JS, page, count=1)
    else:
        i = page.rindex('</body>'); i = page.rfind('\n', 0, i) + 1
        page = page[:i] + JS + page[i:]
    return page

def main():
    p = argparse.ArgumentParser()
    p.add_argument('targets', nargs='*')
    p.add_argument('--data', default=os.path.expanduser('~/VST/ANCILLARY_DATA'))
    p.add_argument('--site', default='.')
    p.add_argument('--zoom-size', type=float, default=None, help='cut the views from the make_color_images.py --zoom-only preview of this size (arcsec) centred on the lens, e.g. 640 for a --look deep render, instead of the cube')
    a = p.parse_args()
    for t in a.targets or list(TARGETS):
        if t not in TARGETS:
            print('no colour image configured for', t); continue
        print(t)
        info = make_images(t, a.data, a.site, a.zoom_size)
        fn = os.path.join(a.site, f'{t}_anc.html')
        raw = open(fn, 'rb').read().decode('utf-8')
        crlf = '\r\n' in raw
        new = build(raw.replace('\r\n', '\n'), t, info)
        if crlf: new = new.replace('\n', '\r\n')
        if new != raw:
            open(fn, 'wb').write(new.encode('utf-8')); print('  updated  ', fn)
        else:
            print('  unchanged', fn)

if __name__ == '__main__':
    main()
