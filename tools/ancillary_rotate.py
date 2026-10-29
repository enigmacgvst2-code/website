#!/usr/bin/env python3
"""
Re-make the HST/JWST images of the Ancillary pages north up, east left (as the Color Image card).

  python3 tools/ancillary_rotate.py                # every job in JOBS
  python3 tools/ancillary_rotate.py J0542-2125     # one target
  python3 tools/ancillary_rotate.py --fits-root ~/Riduzioni_JWST/Luisa --site .

For each job: read the SCI image of the reduced FITS, block-average it to about the output pixel
scale, reproject (bilinear) onto a north-up/east-left TAN grid that covers the whole footprint,
grey-scale asinh stretch (black = sky - 1 sigma, white = 99.8th percentile), white outside the data.
Writes images/<target>_VST/<stem>.jpg and points the page's <img src> for that stem to the .jpg
(the old .png/.jpg stays in git). tools/ancillary_extra.py keeps whatever extension the page uses.
Needs astropy, reproject, scipy, Pillow.
"""
import os, re, sys, argparse, warnings
import numpy as np
from PIL import Image
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.stats import sigma_clipped_stats
from reproject import reproject_interp
warnings.simplefilter('ignore')

# target: [(stem in images/<target>_VST/, FITS relative to --fits-root, max output size px)]
JOBS = {
    'J0335-1927': [('f444w_jwst', 'COOL_J0335-1927/J0335_nircam_f444w_new_i2d_mbkgsub_sci.fits', 2000)],
    'J0542-2125': [('f160w_hst', 'COOL_J0542-2125/HST/cool_j0542_f160w.fits', None),
                   ('f444w_jwst', 'COOL_J0542-2125/nircam_f444w_i2d_mbkgsub.fits', 2600)],
    'J1029+2623': [('f444w_jwst', 'SDSS_J1029+2623/nircam_f444w_i2d_mbkgsub.fits', 2000)],
}
QUALITY = 90

def sci_hdu(fn):
    h = fits.open(fn, memmap=True)
    for x in h:
        if x.is_image and x.header.get('NAXIS', 0) == 2 and (x.name in ('SCI', 'PRIMARY') or len(h) == 1):
            return x
    raise SystemExit('no 2-D SCI image in ' + fn)

def make(fn, maxpx):
    hdu = sci_hdu(fn)
    data = np.asarray(hdu.data, dtype=np.float32)
    w = WCS(hdu.header).celestial
    scale = proj_plane_pixel_scales(w).mean()                       # deg / px
    good = np.isfinite(data) & (data != 0)
    ys, xs = np.nonzero(good[::8, ::8]); ys, xs = ys*8, xs*8
    ra, dec = w.all_pix2world(xs, ys, 0)
    ra0, dec0 = w.all_pix2world([data.shape[1]/2], [data.shape[0]/2], 0)
    out = WCS(naxis=2); out.wcs.ctype = ['RA---TAN', 'DEC--TAN']; out.wcs.crval = [ra0[0], dec0[0]]
    out.wcs.crpix = [1, 1]; out.wcs.cdelt = [-scale, scale]
    x, y = out.all_world2pix(ra, dec, 0)
    span = max(x.max()-x.min(), y.max()-y.min()) + 16
    b = max(1, int(np.ceil(span/maxpx))) if maxpx else 1          # block-average factor
    if b > 1:
        ny, nx = (data.shape[0]//b)*b, (data.shape[1]//b)*b
        d = np.where(good, data, 0)[:ny, :nx].reshape(ny//b, b, nx//b, b)
        n = good[:ny, :nx].reshape(ny//b, b, nx//b, b).sum(axis=(1, 3))
        data = np.where(n > b*b/2, d.sum(axis=(1, 3))/np.maximum(n, 1), np.nan).astype(np.float32)
        w = w[::b, ::b]
    else:
        data = np.where(good, data, np.nan)
    out.wcs.cdelt = [-scale*b, scale*b]
    x, y = out.all_world2pix(ra, dec, 0)
    out.wcs.crpix = [1 - x.min() + 8/b + 1, 1 - y.min() + 8/b + 1]
    shape = (int(np.ceil(y.max()-y.min() + 16/b + 2)), int(np.ceil(x.max()-x.min() + 16/b + 2)))
    img, foot = reproject_interp((data, w), out, shape_out=shape, order='bilinear')
    ok = np.isfinite(img) & (foot > 0)
    # trim empty borders
    rows, cols = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    img, ok = img[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1], ok[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]
    v = img[ok]
    _, med, sig = sigma_clipped_stats(v[::max(1, v.size//2000000)], sigma=3, maxiters=5)
    lo, hi = med - sig, np.percentile(v, 99.8)
    q = 12.0
    s = np.arcsinh(np.clip((img - lo)/(hi - lo), 0, None)*q)/np.arcsinh(q)
    g = (np.clip(s, 0, 1)*255).astype(np.uint8)
    g[~ok] = 255
    return Image.fromarray(g[::-1]), scale*b*3600, b               # FITS y up -> north up

def point_page(page, t, stem):
    pat = re.compile(r'(src="images/' + re.escape(t) + r'_VST/' + re.escape(stem) + r')\.(?:png|jpg|jpeg)"')
    return pat.sub(r'\1.jpg"', page)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('targets', nargs='*')
    p.add_argument('--fits-root', default=os.path.expanduser('~/Riduzioni_JWST/Luisa'))
    p.add_argument('--site', default='.')
    a = p.parse_args()
    for t in a.targets or list(JOBS):
        fn_page = os.path.join(a.site, f'{t}_anc.html')
        raw = open(fn_page, 'rb').read().decode('utf-8'); page = raw
        for stem, rel, maxpx in JOBS[t]:
            im, pix, b = make(os.path.join(a.fits_root, rel), maxpx)
            out = os.path.join(a.site, 'images', f'{t}_VST', stem + '.jpg')
            im.save(out, quality=QUALITY, optimize=True, progressive=True)
            print(f'{t} {stem}: {im.width}x{im.height} px, {pix:.3f}"/px (bin {b}), {os.path.getsize(out)//1024} KB')
            page = point_page(page, t, stem)
        if page != raw:
            open(fn_page, 'wb').write(page.encode('utf-8')); print('  updated', fn_page)

if __name__ == '__main__':
    main()
