#!/usr/bin/env python3
"""
North-up/east-left versions of Ancillary-page images that have NO FITS (only the old screenshot PNG/JPG):
the screenshot is registered (similarity transform from a few control points, refined on all matched sources) against a reference image that HAS a WCS, then warped onto a north-up grid at its own scale.

  python3 tools/ancillary_register.py J0335-1927 [--site .]

JOBS: target -> [(stem, reference FITS, HDU, plane or None)]. The screenshot read is the file the page
uses now (images/<t>_VST/<stem>.png|jpg); it is kept, the new image is <stem>_nup.jpg and the page
<img src> is pointed to it. tools/ancillary_extra.py: the IMG stems for these are '<stem>_nup'.
Needs astropy, reproject, scipy, scikit-image, Pillow.
"""
import os, re, sys, argparse, warnings
import numpy as np
from PIL import Image
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from reproject import reproject_interp
from skimage.transform import SimilarityTransform, AffineTransform, warp
warnings.simplefilter('ignore')
Image.MAX_IMAGE_PIXELS = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ancillary_extra import COORDS as LENS   # lens positions as on the pages
V = os.path.expanduser('~/VST/ANCILLARY_DATA')
S = os.path.expanduser('~/VST/FINAL_STACKS')
M = os.path.expanduser('~/VST/mosaic/stacks')
# target -> [(stem, reference FITS, HDU, plane or None, control points)]
# control points = [(x, y) in the screenshot (full size, origin top-left), (RA, Dec) of the same object], >= 2;
# they give the starting transform, which is then refined on all sources matched within a few pixels.
JOBS = {
    'J0335-1927': [('f625w_hst', V + '/COOL_J0335-1927/color/COOL_J0335-1927_ugriz_cube.fits', 0, 1,
                    [((1300, 1670), (53.788529, -19.499697)),    # edge-on spiral (S)
                     ((1640, 924), (53.760535, -19.492060)),     # star with spikes
                     ((920, 700), (53.770848, -19.469490)),      # brightest cluster galaxy
                     ((986, 1134), (53.781013, -19.480254))])],  # star
    'J1029+2623': [('f160w_hst', os.path.expanduser('~/Riduzioni_JWST/Luisa') + '/SDSS_J1029+2623/nircam_f444w_i2d_mbkgsub.fits', 'SCI', None,
                    [((541, 489), (157.305611, 26.392480)),      # BCG 1
                     ((629, 483), (157.302038, 26.392347)),      # BCG 2
                     ((493, 614), (157.308029, 26.388113))])],   # bright knot at the S end of the arc
    # no control points known: grid search in rotation/scale about the lens (screenshot px), VST r stack
    'J0722-3901': [('f160w_hst', M + '/J0722-3901_stack_clipped.fits', 0, None,       # dense star field
                    {'xcorr': (0.50, -30, -5)})],     # (screenshot -> 0.25"/px scale, rotation range searched)  # double star E, west component
    'J2107-1611': [('f160w_hst', M + '/PSJ2107-1611_stack_clipped.fits', 0, None, {'lens': (612, 440), 'scale': (0.44, 0.60)})],
    'J0123-0455': [('f814w_hst', S + '/PS_J0123-0455_stack_clipped.fits', 0, None,
                    [((517, 371), (20.841003, -4.932868)),       # lensed quasar
                     ((778, 428), (20.835056, -4.934981)),       # point source
                     ((689, 546), (20.837544, -4.937497)),       # point source
                     ((941, 264), (20.830782, -4.931497))])],    # galaxy
    'J1330+1810': [('f160w_hst', S + '/COOL_J1330+1810_stack_clipped.fits', 0, None,
                    [((634, 437), (202.577838, 18.175866)),      # lens galaxy
                     ((456, 540), (202.585322, 18.177199)),      # bright elliptical
                     ((465, 126), (202.575148, 18.188199))])],   # star with spikes
    'J2329-1258': [('f814w_hst', V + '/WISE_2329-1258/WISE_2329-1258_i_LS_swarped.fits', 0, None,   # LS DR10 i (VST stack too noisy)
                    [((865, 442), (352.492352, -12.981743)),     # star 7" NE of the quasar (spikes)
                     ((1016, 1001), (352.501768, -12.998724)),   # star with spikes
                     ((826, 1514), (352.518565, -13.006767)),    # point source
                     ((1460, 1056), (352.492046, -13.010242))])],# galaxy (points 2-4 from a rotation/scale search: 43.5 deg, 93 matches)
}
REF_SCALE, REF_HALF = 0.25, 170.0     # reference grid: 0.25"/px, +-170" around the lens
REF_SCALE = float(os.environ.get('REG_SCALE', REF_SCALE)); REF_HALF = float(os.environ.get('REG_HALF', REF_HALF))
QUALITY = 90

def reference(t, fn, ext, plane, root_map):
    fn = root_map(fn)
    h = fits.open(fn, memmap=True)[ext]
    d = h.data if plane is None else h.data[plane]
    w = WCS(h.header).celestial
    out = WCS(naxis=2); out.wcs.ctype = ['RA---TAN', 'DEC--TAN']; out.wcs.crval = list(LENS[t])
    n = int(2*REF_HALF/REF_SCALE); s = REF_SCALE/3600
    out.wcs.cdelt = [-s, s]; out.wcs.crpix = [n/2 + .5, n/2 + .5]
    if d.ndim == 2 and d.shape[0]*d.shape[1] > 4e7:      # big mosaic: cut around the lens first
        x, y = w.all_world2pix(*LENS[t], 0); m = int(REF_HALF*1.5/(proj_plane_pixel_scales(w).mean()*3600))
        X, Y = int(x), int(y); y0, x0 = max(Y-m, 0), max(X-m, 0)
        d = d[y0:Y+m, x0:X+m]; w = w[y0:Y+m, x0:X+m]
    r, _ = reproject_interp((np.asarray(d, np.float32), w), out, shape_out=(n, n))
    return np.nan_to_num(r)[::-1].copy(), out, n  # display orientation: row 0 = north, col 0 = east

def screenshot(fn):
    g = np.asarray(Image.open(fn).convert('L'), np.float32)
    from scipy.ndimage import label
    lab, _ = label((g >= 254) | (g <= 0))            # margins = white/black regions touching the border
    edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    blank = np.isin(lab, edge[edge > 0])
    sky = np.median(g[~blank])
    g[blank] = sky
    return g, blank

def peaks(im, sig, n, mask=None, box=9):
    from scipy.ndimage import gaussian_filter, maximum_filter
    g = gaussian_filter(im, sig); mx = maximum_filter(g, box)
    lo = g[g < np.percentile(g, 80)]
    pk = (g == mx) & (g > np.median(lo) + 5*np.std(lo))
    if mask is not None:
        pk &= ~mask
    y, x = np.nonzero(pk); o = np.argsort(-g[y, x])[:n]
    return np.c_[x[o], y[o]].astype(float)

def search(Q, tree, anchor_src, anchor_ref, scales, rots=np.arange(-180, 180, 0.5), tol=3):
    """rotation/scale grid search about one known point (the lens): most sources matched within tol."""
    best = (0, 0, 0)
    for rot in rots:
        th = np.radians(rot)
        for sc in scales:
            Rm = sc*np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
            d, _ = tree.query((Q - anchor_src) @ Rm.T + anchor_ref, distance_upper_bound=tol)
            k = int(np.isfinite(d).sum())
            if k > best[0]:
                best = (k, rot, sc)
    k, rot, sc = best
    T = SimilarityTransform(scale=sc, rotation=np.radians(rot))
    T = SimilarityTransform(matrix=SimilarityTransform(translation=anchor_ref - T(anchor_src[None])[0]).params @ T.params)
    print('   search about the lens: %d sources matched, scale %.4f, rot %.1f deg' % (k, sc, rot))
    return T

def xcorr(src, blank, ref, Q, P, sc, lo, hi):
    """rotation by image cross-correlation (screenshot smoothed and scaled to the reference pixels),
    then the translation by voting on source positions."""
    from scipy.ndimage import gaussian_filter, zoom, rotate
    from skimage.feature import match_template
    def prep(im, sig):
        im = gaussian_filter(im, sig); v = im - np.median(im); sd = np.std(v[v < np.percentile(v, 90)])
        return np.arcsinh(np.clip(v/sd, -3, None)/3)
    S = prep(zoom(np.where(blank, np.median(src), src), sc, order=1), 1.5)
    Rf = prep(np.nan_to_num(ref), 1.0)
    def corr(ang):
        r = rotate(S, -ang, reshape=True, order=1, cval=0); h, w = r.shape
        return float(match_template(Rf, r[h//6:-h//6, w//6:-w//6]).max())
    angs = np.arange(lo, hi + 1e-6, 1.0); a0 = angs[np.argmax([corr(a) for a in angs])]
    angs = np.arange(a0 - 1, a0 + 1.01, 0.25); ang = angs[np.argmax([corr(a) for a in angs])]
    th = np.radians(ang); q = Q @ (sc*np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])).T
    dd = (P[None] - q[:, None]).reshape(-1, 2)
    H, xe, ye = np.histogram2d(dd[:, 0], dd[:, 1], bins=[np.arange(dd[:, 0].min(), dd[:, 0].max() + 3, 3)]*1 +
                               [np.arange(dd[:, 1].min(), dd[:, 1].max() + 3, 3)])
    i, j = np.unravel_index(H.argmax(), H.shape)
    tx, ty = (xe[i] + xe[i+1])/2, (ye[j] + ye[j+1])/2
    print('   cross-correlation: rot %.2f deg (scale %.3f), translation from %d votes' % (ang, sc, H.max()))
    return SimilarityTransform(scale=sc, rotation=th, translation=(tx, ty))

def match(src, blank, ref, rw, n, cps, t=None):
    """similarity transform screenshot px -> reference display px, from control points (or a search
    about the lens when cps = {'lens': (x, y), 'scale': (lo, hi)}), refined on all matched sources."""
    from scipy.ndimage import binary_dilation
    from scipy.spatial import cKDTree
    sat = (src >= 250) & ~blank
    masks = [binary_dilation(blank | sat, iterations=20),                            # bright objects masked widely
             binary_dilation(blank, iterations=20) | binary_dilation(sat, iterations=4),
             binary_dilation(blank, iterations=20)]
    Qs = [peaks(src, 2.0, nq, mask=m, box=11) for m in masks for nq in (400, 800)]
    Q = Qs[0]
    P = peaks(ref, 1.0, 1500)
    tree = cKDTree(P)
    if isinstance(cps, dict) and 'xcorr' in cps:
        T = xcorr(src, blank, ref, Qs[1], P, *cps['xcorr'])
    elif isinstance(cps, dict):
        lx, ly = rw.all_world2pix(*LENS[t], 0)
        lo, hi = cps['scale']
        T = search(Q, tree, np.array(cps['lens'], float), np.array([lx, n - 1 - ly]), np.arange(lo, hi, 0.004))
    else:
        xy = np.array([c[0] for c in cps], float)
        rx, ry = rw.all_world2pix([c[1][0] for c in cps], [c[1][1] for c in cps], 0)
        dst = np.c_[rx, n - 1 - ry]
        T = SimilarityTransform(); T.estimate(xy, dst)
        print('   control points: scale %.4f, rot %.2f deg, residuals %s px' % (T.scale, np.degrees(T.rotation),
              np.round(np.sqrt(((T(xy) - dst)**2).sum(1)), 1)))
    T0, best = T, None
    for Q in Qs:
      for uniq in (True, False):
        T = T0
        for tol in (6, 4, 3, 2, 2):
            d, i = tree.query(T(Q), distance_upper_bound=tol)
            ok = np.isfinite(d)
            u, c = np.unique(i[ok], return_counts=True)       # one screenshot source per reference source
            if uniq:
                ok &= np.isin(i, u[c == 1])
            if ok.sum() < 6:
                break
            T2 = SimilarityTransform()
            if not T2.estimate(Q[ok], P[i[ok]]) or not np.isfinite(T2.params).all():
                break
            T = T2
        d, i = tree.query(T(Q), distance_upper_bound=2); ok = np.isfinite(d)
        k = len(np.unique(i[ok]))                            # distinct reference sources matched
        if os.environ.get('REG_DEBUG'):
            print('     cand %d peaks uniq=%s: %d, rot %.2f, scale %.4f' % (len(Q), uniq, k, np.degrees(T.rotation), T.scale))
        if best is None or k > best[0]:
            best = (k, T, np.sqrt((d[ok]**2).mean()) if ok.any() else np.nan)
    k, T, rms = best
    print('   refined on %d sources: scale %.4f, rot %.2f deg, rms %.2f ref px' % (k, T.scale, np.degrees(T.rotation), rms))
    return T

def north_up(img_rgb, blank, T):
    """warp the screenshot so that it has the reference orientation, at its own pixel scale."""
    k = 1.0/T.scale                       # keep the screenshot's pixel scale
    M = AffineTransform(scale=(k, k)).params @ T.params
    h, w = blank.shape
    yy, xx = np.nonzero(~blank[::4, ::4]); pts = np.c_[xx*4, yy*4].astype(float)
    q = (M @ np.c_[pts, np.ones(len(pts))].T).T[:, :2]
    x0, y0 = q.min(0) - 2; x1, y1 = q.max(0) + 2
    M = AffineTransform(translation=(-x0, -y0)).params @ M
    shape = (int(np.ceil(y1 - y0)), int(np.ceil(x1 - x0)))
    inv = AffineTransform(matrix=np.linalg.inv(M))
    out = np.stack([warp(img_rgb[..., c], inv, output_shape=shape, order=1, cval=1.0) for c in range(img_rgb.shape[2])], -1)
    m = warp(blank.astype(float), inv, output_shape=shape, order=0, cval=1.0) > 0.5
    out[m] = 1.0
    north_up.M = M
    return Image.fromarray((np.clip(out, 0, 1)*255).astype(np.uint8).squeeze())

def main():
    p = argparse.ArgumentParser()
    p.add_argument('targets', nargs='*')
    p.add_argument('--site', default='.')
    p.add_argument('--root', default=None, help='replace ~ in the JOBS paths (for running in another environment)')
    a = p.parse_args()
    home = os.path.expanduser('~')
    root_map = (lambda f: f.replace(home, a.root, 1)) if a.root else (lambda f: f)
    for t in a.targets or list(JOBS):
        fn_page = os.path.join(a.site, f'{t}_anc.html')
        raw = open(fn_page, 'rb').read().decode('utf-8'); page = raw
        for stem, ref_fn, ext, plane, cps in JOBS[t]:
            m = re.search(r'src="(images/' + re.escape(t) + r'_VST/' + re.escape(stem) + r'(?:_nup)?\.(?:png|jpg|jpeg))"', page)
            if not m:
                print(t, stem, 'not on the page'); continue
            shot = os.path.join(a.site, m.group(1))
            if '_nup.' in shot:                     # already done: read the original screenshot again
                base = shot.rsplit('_nup.', 1)[0]
                shot = next(base + e for e in ('.png', '.jpg', '.jpeg') if os.path.exists(base + e))
            print(t, stem, '<-', m.group(1))
            ref, rw, n = reference(t, ref_fn, ext, plane, root_map)
            g, blank = screenshot(shot)
            T = match(g, blank, ref, rw, n, cps, t)
            rgb = np.asarray(Image.open(shot).convert('RGB'), np.float32)/255
            if (np.ptp(rgb, axis=2) < 2/255).all():
                rgb = rgb[..., :1]
            im = north_up(rgb, blank, T)
            lx, ly = rw.all_world2pix(*LENS[t], 0)
            ls = T.inverse(np.array([[lx, n - 1 - ly]]))[0]
            lo = (north_up.M @ np.r_[ls, 1])[:2]
            print('   lens: screenshot (%.0f, %.0f) -> north-up image (%.0f, %.0f)' % (ls[0], ls[1], lo[0], lo[1]))
            out = os.path.join(a.site, 'images', f'{t}_VST', stem + '_nup.jpg')
            im.save(out, quality=QUALITY, optimize=True, progressive=True)
            print(f'   -> {out} {im.width}x{im.height}, {REF_SCALE*T.scale:.3f}"/px, {os.path.getsize(out)//1024} KB')
            page = page.replace(f'src="{m.group(1)}"', f'src="images/{t}_VST/{stem}_nup.jpg"')
        if page != raw:
            open(fn_page, 'wb').write(page.encode('utf-8')); print('  updated', fn_page)

if __name__ == '__main__':
    main()
