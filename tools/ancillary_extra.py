#!/usr/bin/env python3
"""Builds the data cards of the Ancillary pages (<target>_anc.html) from the tables below, so that
every instrument card has the same layout on every page.

Page layout after a run:
  Discovery Paper (hand-written, untouched)
  -> instrument cards in colour/spectral order (WAVE): KCWI, MUSE, DEIMOS, FORS2, HST, ERIS, JWST
  -> Archival Data (> 10 yr)  -> Survey Coverage

Every program in an instrument card looks the same:
  title "Program <PID>" + release badge (Public / Proprietary until ...), optional note,
  PID / PI / Instrument or Mode / Filters / Date / Exposure, archive buttons, optional image on the right.
The hand-written instrument cards are replaced (REPLACED); only the Discovery Paper card is kept as it is.
Generated cards carry data-anc-extra="1"; extra CSS sits between /* anc-extra-css:start/end */.

Selection (user, 21-22 Oct 2026): only important pointed programs -- imaging, IFU and multi-object
spectroscopy; no single-slit spectra of the quasars, no small ground-based programs; programs
older than 10 yr not already on the pages go into one compact table card. Dates, exposures and
release dates from the ESO, MAST, Gemini, KOA and SMOKA archives (queried 21-22 Oct 2026);
survey bands from VizieR and the NOIRLab Data Lab (bands with detections within 30").
Edit CARDS / ARCHIVE / BANDS / WAVE below and re-run:
  python3 tools/ancillary_extra.py . ../VST_P3_P4        (both sites)
  python3 tools/ancillary_extra.py . ../VST_P3_P4 J1029+2623
"""
import os
import re
import sys
from html import escape
from urllib.parse import quote

COORDS = {  # as shown on the Ancillary pages (deg)
    'J0123-0455': (20.84084, -4.93266),
    'J0335-1927': (53.7668333, -19.46390),
    'J0501-0733': (75.3729, -7.5525),
    'J0542-2125': (85.7392, -21.4261),
    'J0722-3901': (110.6773750, -39.03310),
    'J1029+2623': (157.3026604, 26.3924),
    'J1330+1810': (202.57772, 18.17581),
    'J2107-1611': (316.9685000, -16.19210),
    'J2329-1258': (352.49114, -12.98306),
}

# ---------------------------------------------------------------- card order and colours
# Cards follow the colour sequence of the spectrum (violet -> blue -> cyan -> green -> orange -> red),
# which also follows wavelength; the grey cards (archival, surveys) come last. Original colours kept:
# purple = discovery paper, blue = MUSE, green = FORS2, orange = HST, red = JWST.
ARCHIVE_TITLE = 'Archival Data (&gt; 10 yr)'
WAVE = {
    'Discovery Paper':  0,    # purple  (original)
    'KCWI Data':        1,    # indigo  (Keck/KCWI, 0.35-0.56 um)
    'MUSE Data':        2,    # blue    (original, 0.47-0.93 um)
    'DEIMOS Data':      3,    # cyan    (Keck/DEIMOS, optical MOS)
    'FORS2 Data':       4,    # green   (original)
    'HST Data':         5,    # orange  (original)
    'ERIS Data':        6,    # red-orange (VLT/ERIS, NIR AO)
    'JWST Data':        7,    # red     (original)
    ARCHIVE_TITLE:      50,   # grey
    'Survey Coverage':  99,   # grey
    'Color Image':      100,  # spectrum stripe, after the surveys (tools/ancillary_color.py, kept as it is)
}
OLD_YEARS = 10
REPLACED = [t for t in WAVE if t not in ('Discovery Paper', 'Color Image')]   # hand-written cards with these titles are rebuilt

COLOURS = {  # class: (main, dark, rgb); classes already defined by a page keep the page's definition
    'card-blue':      ('#5e86f7', '#4870e0', '94, 134, 247'),   # MUSE   (original colour)
    'card-green':     ('#10b981', '#059669', '16, 185, 129'),   # FORS2  (original colour)
    'card-orange':    ('#f59e0b', '#d97706', '245, 158, 11'),   # HST    (original colour)
    'card-red':       ('#ef4444', '#dc2626', '239, 68, 68'),    # JWST   (original colour)
    'card-indigo':    ('#4338ca', '#3730a3', '67, 56, 202'),    # KCWI
    'card-cyan':      ('#0891b2', '#0e7490', '8, 145, 178'),    # DEIMOS
    'card-vermilion': ('#ea580c', '#c2410c', '234, 88, 12'),    # ERIS
    'card-stone':     ('#78716c', '#57534e', '120, 113, 108'),  # Archival Data (> 10 yr)
    'card-slate':     ('#475569', '#334155', '71, 85, 105'),    # Survey Coverage
}
CARD_CLASS = {'KCWI Data': 'card-indigo', 'MUSE Data': 'card-blue', 'DEIMOS Data': 'card-cyan',
              'FORS2 Data': 'card-green', 'HST Data': 'card-orange', 'ERIS Data': 'card-vermilion',
              'JWST Data': 'card-red'}

# ---------------------------------------------------------------- link helpers
def eso(pid):
    return ('https://archive.eso.org/wdb/wdb/eso/eso_archive_main/query?prog_id=' + quote(pid),
            f'ESO Archive Query ({pid})', 'search')

def mast_hst(t, pi):
    ra, dec = COORDS[t]
    return ('https://mast.stsci.edu/search/ui/#/hst/results?resolve=true&target='
            f'{ra}+{dec}&radius=3&radius_units=arcminutes&data_type=all&observations=S'
            '&active_instruments=stis,acs,wfc3,cos,fgs&legacy_instruments=foc,fos,ghrs,hsp,nicmos,wfpc,wfpc2'
            f'&pi_surname={pi.upper()}', 'MAST HST Search', 'search')

def mast_jwst(t, pi):
    ra, dec = COORDS[t]
    return ('https://mast.stsci.edu/search/ui/#/jwst/results?resolve=true&target='
            f'{ra}+{dec}&radius=3&radius_units=arcminutes&data_types=spectrum,timeseries,image,other'
            f'&instruments=MIRI,NIRCAM,NIRSPEC,NIRISS,FGS&pi_surname={pi}', 'MAST JWST Search', 'search')

def stsci(pid):
    return (f'https://www.stsci.edu/hst-program-info/program/?program={pid}', f'STScI Program {pid}', 'ext')

def stsci_jwst(pid):
    return (f'https://www.stsci.edu/jwst-program-info/program/?program={pid}', f'STScI Program {pid}', 'ext')

def koa():
    return ('https://koa.ipac.caltech.edu/cgi-bin/KOA/nph-KOAlogin', 'KOA Search', 'search')

def gemini(pid):
    return (f'https://archive.gemini.edu/searchform/{pid}', f'Gemini Archive ({pid})', 'search')

def sexa(t):
    ra, dec = COORDS[t]
    h = ra / 15; rh = int(h); rm = int((h - rh) * 60); rs = ((h - rh) * 60 - rm) * 60
    sd = '+' if dec >= 0 else '-'; d = abs(dec); dd = int(d); dm = int((d - dd) * 60); ds = ((d - dd) * 60 - dm) * 60
    return f'{rh:02d}:{rm:02d}:{rs:05.2f}', f'{sd}{dd:02d}:{dm:02d}:{ds:04.1f}'

def smoka(t, inst='SUP'):
    """SMOKA (Subaru archive) search, science frames within 3 arcmin."""
    ra, dec = sexa(t)
    url = ('https://smoka.nao.ac.jp/fssearch?object=&resolver=SIMBAD&coordsys=Equatorial&equinox=J2000&fieldofview=auto'
           f'&RadOrRec=radius&longitudeC={quote(ra)}&latitudeC={quote(dec)}&radius=3&asciitable=Table&frameorshot=Frame'
           f'&instruments={inst}&obs_mod=IMAG&data_typ=OBJECT&obs_cat=Science+Observation&bandwidth_type=FILTER'
           '&dispcol=default&orderby=FRAMEID&diff=100&output_equinox=J2000&from=0&action=Search')
    return (url, 'SMOKA Search', 'search')

def vizier(t, cat, rs):
    ra, dec = COORDS[t]
    return (f'https://vizier.cds.unistra.fr/viz-bin/VizieR-4?-source={cat}&-c={ra}%20{quote(f"{dec:+}")}&-c.rs={rs}')

# ---------------------------------------------------------------- program constructors
def badge(release):
    """'public' -> Public; anything else -> 'Proprietary until <release>' (or the text itself if it starts with 'Partly')."""
    if release == 'public':
        return ('Public', 'info')
    if release.startswith('Partly'):
        return (release, 'progress')
    return (f'Proprietary until {release}', 'progress')

def prog(pid, pi, extra, date, release, buttons, note=None, exposure=None, image=None):
    meta = [('PID', pid), ('PI', pi)] + list(extra) + [('Date', date)]
    if exposure:
        meta.append(('Exposure', exposure))
    return dict(title=f'Program {pid}', meta=meta, note=note, badge=badge(release), buttons=buttons, image=image)

def IMG(stem, caption, credit=None):
    """stem = 'images/<target>_VST/f160w_hst' (extension resolved per site: the one the page uses, else png, jpg)."""
    return dict(stem=stem, caption=caption, credit=credit)

def HST(t, pid, pi, inst, filters, date, release, note=None, image=None):
    return prog(pid, pi, [('Instrument', inst), ('Filters', filters)], date, release,
                [mast_hst(t, pi), stsci(pid)], note=note, image=image)

def JWST(t, pid, pi, inst, filters, date, release, note=None, image=None):
    return prog(pid, pi, [('Instrument', inst), ('Filters', filters)], date, release,
                [mast_jwst(t, pi), stsci_jwst(pid)], note=note, image=image)

def ESO(pid, pi, date, release, exposure=None, mode=None, note=None):
    extra = [('Mode', mode)] if mode else []
    return prog(pid, pi, extra, date, release, [eso(pid)], note=note, exposure=exposure)

def KECK(pid, pi, inst, date, release='public', note=None):
    return prog(pid, pi, [('Instrument', inst)], date, release, [koa()], note=note)

def A(facility, program, data, date, link, wave):
    """One row of the archival (> 10 yr) card; rows are sorted by wave (micron)."""
    return dict(facility=facility, program=program, data=data, date=date, link=link, wave=wave)

GAP = 'An HST Gap Program for lensed quasars.'
LYA = 'Narrow-band Ly&alpha; imaging of strongly lensed quasar host galaxies.'
TDC = 'Time-delay cosmography with strong cluster lenses.'
PEC = 'Credits to L. Pecoraro'

def also(*targets):
    links = [f'<a href="{t}_anc.html">{t}</a>' for t in targets]
    txt = links[0] if len(links) == 1 else ', '.join(links[:-1]) + ' and ' + links[-1]
    return f'This program also targets {txt}.'

def fors2(t, date, exposure, release, others):
    return ESO('116.299H', 'Grillo', date, release, exposure=exposure, mode='MXU multi-object spectroscopy',
               note=also(*others) + ' The program is completed (48 / 48 h executed).')

# ---------------------------------------------------------------- instrument cards per target
CARDS = {
 'J0123-0455': {
    'HST Data': [
        HST('J0123-0455', '17308', 'Lemon', 'ACS/WFC', 'F814W', '21 Oct 2023', 'public', note=GAP,
            image=IMG('images/J0123-0455_VST/f814w_hst', 'HST F814W image of J0123-0455.'))]},

 'J0335-1927': {
    'KCWI Data': [KECK('K472', "O'Meara", 'Keck II / KCWI (optical IFU)', '16 Sep 2023')],
    'MUSE Data': [
        ESO('115.282P', 'Acebron', '16 Sep 2025', 'public', exposure='4.0 h'),
        ESO('116.28NR', 'Acebron', '29 Nov 2025', '29 Nov 2026', exposure='0.8 h', note=also('J0542-2125'))],
    'FORS2 Data': [fors2('J0335-1927', 'Oct &ndash; Dec 2025', '27.7 h', 'Partly public (rest until Dec 2026)',
                         ['J0542-2125', 'J1029+2623'])],
    'HST Data': [
        HST('J0335-1927', '17726', 'Dahle', 'ACS/WFC', 'F435W, F475W, F625W', 'Oct 2025', 'public', note=TDC,
            image=IMG('images/J0335-1927_VST/f625w_hst', 'HST F625W image of J0335-1927.')),
        HST('J0335-1927', '17912', 'Bayliss', 'ACS/WFC', 'FR505N (ramp, Ly&alpha;)', 'Jul &ndash; Aug 2026',
            'Jan &ndash; Feb 2027', note=LYA)],
    'JWST Data': [
        JWST('J0335-1927', '6675', 'Dahle', 'NIRCam', 'F115W, F150W, F444W', '15 Jan 2025', 'public', note=TDC,
             image=IMG('images/J0335-1927_VST/f444w_jwst', 'JWST F444W image of J0335-1927.', PEC))]},

 'J0501-0733': {
    'MUSE Data': [ESO('114.27CU', 'Treister', 'Nov 2024 &ndash; Jan 2025', 'public', exposure='4.0 h')],
    'HST Data': [
        HST('J0501-0733', '17444', 'Tub&iacute;n-Arenas', 'ACS/WFC', 'F606W, F814W', 'Jul &ndash; Aug 2024', 'public',
            note='Mapping the geometry of eRASS1 J050129.5-073309 with high-resolution imaging of the lens and quasar host.'),
        HST('J0501-0733', '17308', 'Lemon', 'ACS/WFC', 'F814W', '12 Nov 2023', 'public', note=GAP)]},

 'J0542-2125': {
    'KCWI Data': [KECK('N169', 'Gladders', 'Keck II / KCWI (optical IFU)', '2 Mar 2025',
                       note='KCWI spectroscopy of wide-separation lensed quasars.')],
    'MUSE Data': [
        ESO('116.28NR', 'Acebron', 'Nov 2025 &ndash; Jan 2026', 'Nov 2026 &ndash; Jan 2027', exposure='3.5 h',
            note=also('J0335-1927')),
        ESO('114.27PL', 'Sharon', '24 Nov 2024', 'public', exposure='0.7 h',
            note='Field centred on the western cluster component; the 1&prime; &times; 1&prime; MUSE field also covers the '
                 'eastern component and the lensed quasar (about 21&Prime; from the field centre).')],
    'FORS2 Data': [fors2('J0542-2125', 'Oct &ndash; Dec 2025', '27.7 h', 'Oct &ndash; Dec 2026',
                         ['J0335-1927', 'J1029+2623'])],
    'HST Data': [
        HST('J0542-2125', '17243', 'Napier', 'ACS/WFC, WFC3/UVIS, WFC3/IR', 'F390W, F606W, F814W, F105W, F160W',
            'Sep 2023 &ndash; Feb 2024', 'public',
            note='DECALS J0542-2125: the dynamical state of an extraordinary cluster merger at z = 0.61.',
            image=IMG('images/J0542-2125_VST/f160w_hst', 'HST F160W image of J0542-2125.'))],
    'JWST Data': [
        JWST('J0542-2125', '6675', 'Dahle', 'NIRCam', 'F115W, F150W, F444W', '4 Dec 2024', 'public', note=TDC,
             image=IMG('images/J0542-2125_VST/f444w_jwst', 'JWST F444W image of J0542-2125.', PEC))]},

 'J0722-3901': {
    'HST Data': [
        HST('J0722-3901', '17916', 'Treu', 'WFC3/IR', 'F160W', '13 Jun 2025', 'public',
            note='HST imaging of quadruply imaged quasars (dark matter, H<sub>0</sub>, stellar IMF).',
            image=IMG('images/J0722-3901_VST/f160w_hst', 'HST F160W image of J0722-3901.'))]},

 'J1029+2623': {
    'MUSE Data': [ESO('0102.A-0642(A)', 'Grillo', 'Mar &ndash; May 2019', 'public', exposure='4.8 h')],
    'FORS2 Data': [fors2('J1029+2623', 'Dec 2025 &ndash; Mar 2026', '25.8 h', 'Dec 2026 &ndash; Mar 2027',
                         ['J0335-1927', 'J0542-2125'])],
    'HST Data': [
        HST('J1029+2623', '12195', 'Oguri', 'ACS/WFC, WFC3/IR', 'F475W, F814W, F160W', 'Apr &ndash; May 2011', 'public',
            note='Understanding the largest quasar lens SDSS J1029+2623.',
            image=IMG('images/J1029+2623_VST/f160w_hst', 'HST F160W image of J1029+2623.')),
        HST('J1029+2623', '17912', 'Bayliss', 'ACS/WFC', 'FR388N (ramp, Ly&alpha;)', '19 Nov 2025', 'public', note=LYA)],
    'JWST Data': [
        JWST('J1029+2623', '6675', 'Dahle', 'NIRCam', 'F115W, F150W, F444W', 'Dec 2024', 'public', note=TDC,
             image=IMG('images/J1029+2623_VST/f444w_jwst', 'JWST F444W image of J1029+2623.', PEC))]},

 'J1330+1810': {
    'DEIMOS Data': [KECK('U081', 'Fassnacht', 'Keck II / DEIMOS (multi-object spectroscopy)', '13&ndash;14 Jun 2021',
                         note='Spectroscopy of the lens environment for time-delay cosmography.')],
    'HST Data': [
        HST('J1330+1810', '15320', 'Treu', 'WFC3/UVIS, WFC3/IR', 'F475X, F814W, F160W', '15 Aug 2018', 'public',
            note='Probing the dark universe with quadruply imaged quasars.',
            image=IMG('images/J1330+1810_VST/f160w_hst', 'HST F160W image of J1330+1810.'))]},

 'J2107-1611': {
    'MUSE Data': [ESO('111.264M', 'Lemon', '21 Jul 2023', 'public', exposure='1.3 h')],
    'HST Data': [
        HST('J2107-1611', '17601', 'Dux', 'WFC3/UVIS, WFC3/IR', 'F475X, F814W, F160W', 'May &ndash; Jun 2024', 'public',
            note='The first changing-multiplicity lensed quasar.',
            image=IMG('images/J2107-1611_VST/f160w_hst', 'HST F160W image of J2107-1611.')),
        HST('J2107-1611', '17308', 'Lemon', 'ACS/WFC', 'F814W', '23 Jun 2024', 'public', note=GAP)],
    'ERIS Data': [ESO('111.264M', 'Lemon', '30 Jun 2023', 'public', mode='ERIS/NIX AO imaging')],
    'JWST Data': [
        JWST('J2107-1611', '2046', 'Nierenberg', 'MIRI', 'F560W, F1280W, F1800W, F2550W', '4 May 2023', 'public',
             note='A definitive test of the dark matter paradigm on small scales.',
             image=IMG('images/J2107-1611_VST/f560w_jwst', 'JWST F560W image of J2107-1611.')),
        JWST('J2107-1611', '5553', 'Lemon', 'NIRSpec IFU', 'G140M/F100LP, G235M/F170LP', '15 Oct 2025', 'public',
             note='The first changing-multiplicity lensed quasar: a sub-parsec-scale probe of a quasar at cosmic noon.')]},

 'J2329-1258': {
    'HST Data': [
        HST('J2329-1258', '17308', 'Lemon', 'ACS/WFC', 'F814W', '7 Sep 2024', 'public', note=GAP,
            image=IMG('images/J2329-1258_VST/f814w_hst', 'HST F814W image of J2329-1258.'))]},
}

# ---------------------------------------------------------------- archival programs (> 10 yr) not in the cards above
ARCHIVE = {
 'J1029+2623': [
    A('Subaru / Suprime-Cam', '&mdash;', 'g, r, i imaging', 'Jan 2008', smoka('J1029+2623'), 0.60),
    A('HST / WFPC2', '11289 (Kneib, SL2S)', 'F606W imaging', 'Nov 2008', mast_hst('J1029+2623', 'Kneib'), 0.61),
    A('Gemini-N / GMOS', 'GN-2010A-C-4 (Oguri)', 'Multi-object spectroscopy (R150) + i imaging', 'Mar 2010',
      gemini('GN-2010A-C-4'), 0.64),
    A('Gemini-N / GMOS', 'GN-2015A-C-2 (Wilson)', 'Multi-object spectroscopy (R400)', 'Feb 2015',
      gemini('GN-2015A-C-2'), 0.64)],
 'J1330+1810': [
    A('HST / WFC3-IR', '13732 (Nierenberg)', 'F105W imaging + G102 grism', 'Jul 2015', mast_hst('J1330+1810', 'Nierenberg'), 1.0),
    A('Keck I / OSIRIS', 'U021OL, U019OL (Treu)', 'AO-assisted NIR IFU spectroscopy', 'Apr &ndash; May 2015', koa(), 1.8)],
 'J2329-1258': [
    A('Keck II / NIRC2', 'U128N2L (Treu)', 'LGS-AO imaging', 'Sep 2016', koa(), 2.1)],
}

SDSS_SPEC = {
 'J1029+2623': 'SDSS spectrum (2006) and BOSS spectra (2013&ndash;2018).',
 'J1330+1810': 'SDSS spectrum (2007).',
}

# ---------------------------------------------------------------- surveys: bands with detections within 30" of each target
BANDS = {
 'J0123-0455': [('des', 'g r i z Y'), ('ls', 'g r i z'), ('ps1', 'g r i z y'), ('sdss', 'u g r i z'), ('smss', 'g r i z'),
                ('vhs', 'J H K<sub>s</sub>'), ('gaia', 'G, BP, RP')],
 'J0335-1927': [('des', 'g r i z Y'), ('ls', 'g r i z'), ('ps1', 'g r i z y'), ('smss', 'g r i z'), ('atlas', 'u g r i z'),
                ('vhs', 'J K<sub>s</sub>'), ('gaia', 'G, BP, RP')],
 'J0501-0733': [('ls', 'g r i z'), ('ps1', 'g r i z y'), ('smss', 'u v g r i z'), ('vhs', 'J K<sub>s</sub>'), ('gaia', 'G, BP, RP')],
 'J0542-2125': [('des', 'g r i z Y'), ('ls', 'g r i z'), ('ps1', 'g r i z y'), ('smss', 'u v g r i z'),
                ('vhsraw', 'J K<sub>s</sub> &ndash; raw frames (Dec 2018), not in the public releases'), ('gaia', 'G, BP, RP')],
 'J0722-3901': [('delve', 'g r i z'), ('smss', 'v g r i z'), ('vhs', 'J K<sub>s</sub>'), ('gaia', 'G, BP, RP')],
 'J1029+2623': [('ls', 'g r i z'), ('ps1', 'g r i z y'), ('sdss', 'u g r i z'), ('uhs', 'J H K'), ('gaia', 'G, BP, RP')],
 'J1330+1810': [('ls', 'g r i z'), ('ps1', 'g r i z y'), ('sdss', 'u g r i z'), ('uhs', 'J H K'), ('gaia', 'G, BP, RP')],
 'J2107-1611': [('ls', 'g i'), ('ps1', 'g r i z y'), ('smss', 'u v g r i z'), ('vhs', 'Y J K<sub>s</sub>'), ('gaia', 'G, BP, RP')],
 'J2329-1258': [('ls', 'g r i z'), ('ps1', 'g r i z y'), ('smss', 'u v g r i z'), ('atlas', 'u g r i z'),
                ('vhs', 'Y J K<sub>s</sub>'), ('gaia', 'G, BP, RP')],
}

def SURVEYS(t):
    ra, dec = COORDS[t]
    return {
        'des':   ('DES DR2', f'https://www.legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=des-dr2&zoom=16'),
        'ls':    ('DESI Legacy Surveys DR10', f'https://www.legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=ls-dr10&zoom=16'),
        'delve': ('DELVE DR3', 'https://datalab.noirlab.edu/data/delve'),
        'ps1':   ('Pan-STARRS1', f'https://ps1images.stsci.edu/cgi-bin/ps1cutouts?pos={ra}+{dec}&filter=color&size=240'),
        'sdss':  ('SDSS', f'https://skyserver.sdss.org/dr18/VisualTools/navi?ra={ra}&dec={dec}&scale=0.2'),
        'smss':  ('SkyMapper DR4', vizier(t, 'II/379/smssdr4', 30)),
        'vhs':   ('VISTA VHS DR5', vizier(t, 'II/367/vhs_dr5', 30)),
        'gaia':  ('Gaia DR3', vizier(t, 'I/355/gaiadr3', 15)),
        'atlas': ('VST-ATLAS', f'https://archive.eso.org/scienceportal/home?pos={ra},{dec}&r=0.001&sort=-obs_date'),
        'uhs':   ('UKIRT UHS DR3', 'http://wsa.roe.ac.uk:8080/wsa/WSASQL?database=UHSDR3&programmeID=107&from=source'
                  f'&formaction=region&ra={ra}&dec={dec}&sys=J&name=&radius=0.5&xSize=&ySize=&boxAlignment=RADec'
                  '&emailAddress=&format=HTML&compress=NONE&rows=30&select=default&where='),
        'vhsraw': ('VISTA VHS (raw)', 'https://archive.eso.org/wdb/wdb/eso/eso_archive_main/query?prog_id=179.A-2010'
                   f'&ra={ra}&dec={dec}&deg_or_hour=degrees&box=01+00+00'),
    }

# ---------------------------------------------------------------- HTML
I = ' ' * 24   # indentation of a <section> inside the container

def button(b, ind):
    url, label, kind = b
    cls = 'button icon solid fa-search' if kind == 'search' else 'button alt icon solid fa-external-link-alt'
    return (f'{ind}<a href="{escape(url)}" target="_blank" class="{cls}">\n'
            f'{ind}    {escape(label)}\n{ind}</a>\n')

def resolve_image(stem, page, site_dir):
    m = re.search(r'src="(' + re.escape(stem) + r'(?:_nup)?\.(?:png|jpg|jpeg))"', page)   # _nup = north-up version (tools/ancillary_register.py)
    if m:
        return m.group(1)
    for ext in ('png', 'jpg', 'jpeg'):
        if os.path.exists(os.path.join(site_dir, f'{stem}.{ext}')):
            return f'{stem}.{ext}'
    raise SystemExit(f'image {stem}.* not found in {site_dir}')

def prog_html(p, ind, ctx):
    b, bcls = p['badge']
    s = f'{ind}<div class="prog-block{" prog-with-image" if p["image"] else ""}">\n'
    j = ind + '    '
    if p['image']:
        s += f'{j}<div class="prog-info">\n'
        j += '    '
    s += f'{j}<h3 class="prog-title">{p["title"]} <span class="status-badge {bcls}" style="margin-left: 8px;">{b}</span></h3>\n'
    if p['note']:
        s += f'{j}<p class="prog-note">{p["note"]}</p>\n'
    s += f'{j}<div class="meta-grid">\n'
    for k, v in p['meta']:
        s += f'{j}    <div class="meta-item"><span class="meta-label">{k}:</span> {v}</div>\n'
    s += f'{j}</div>\n{j}<div class="btn-group">\n'
    for bt in p['buttons']:
        s += button(bt, j + '    ')
    s += f'{j}</div>\n'
    if p['image']:
        im = p['image']
        src = resolve_image(im['stem'], *ctx)
        alt = re.sub(r'<[^>]+>|\.$', '', im['caption'])
        credit = f'\n{j}        <br><span class="status-badge credit">{im["credit"]}</span>' if im['credit'] else ''
        s += (f'{ind}    </div>\n{ind}    <figure class="data-figure">\n'
              f'{ind}        <img src="{src}" alt="{alt}">\n'
              f'{ind}        <figcaption>{im["caption"]}{credit}\n{ind}        </figcaption>\n'
              f'{ind}    </figure>\n')
    s += f'{ind}</div>\n'
    return s

def card_html(title, progs, ctx):
    J = I + '    '
    sep = f'{J}<hr class="prog-sep">\n'
    body = sep.join(prog_html(p, J, ctx) for p in progs)
    return (f'{I}<section class="dataset-card {CARD_CLASS[title]}" data-anc-extra="1">\n'
            f'{I}    <div class="dataset-header">\n{I}        <h2>{title}</h2>\n{I}    </div>\n'
            + body + f'{I}</section>\n')

def archive_html(rows):
    J = I + '    '
    s = (f'{I}<section class="dataset-card card-stone" data-anc-extra="1">\n'
         f'{I}    <div class="dataset-header">\n{I}        <h2>{ARCHIVE_TITLE}</h2>\n{I}    </div>\n'
         f'{J}<p class="prog-note">Older programs, observed more than {OLD_YEARS} years ago (ordered by wavelength).</p>\n'
         f'{J}<div class="arch-wrap">\n{J}    <table class="arch-table">\n'
         f'{J}        <thead><tr><th>Telescope / Instrument</th><th>Program (PI)</th><th>Data</th><th>Date</th><th>Archive</th></tr></thead>\n'
         f'{J}        <tbody>\n')
    for r in sorted(rows, key=lambda r: r['wave']):
        url, label, _ = r['link']
        s += (f'{J}            <tr><td data-label="Telescope / Instrument">{r["facility"]}</td>'
              f'<td data-label="Program (PI)">{r["program"]}</td><td data-label="Data">{r["data"]}</td>'
              f'<td data-label="Date">{r["date"]}</td>'
              f'<td data-label="Archive"><a href="{escape(url)}" target="_blank" class="arch-link">{escape(label)}</a></td></tr>\n')
    s += f'{J}        </tbody>\n{J}    </table>\n{J}</div>\n{I}</section>\n'
    return s

def survey_html(t, spec):
    sv = SURVEYS(t)
    s = (f'{I}<section class="dataset-card card-slate" data-anc-extra="1">\n'
         f'{I}    <div class="dataset-header">\n{I}        <h2>Survey Coverage</h2>\n{I}    </div>\n'
         f'{I}    <p class="prog-note">Wide-field optical/NIR surveys that cover this target, with the available bands '
         f'(catalogue detections within 30&Prime; or survey images).</p>\n'
         f'{I}    <div class="survey-grid">\n')
    for k, bands in BANDS[t]:
        name, url = sv[k]
        s += (f'{I}        <a class="survey-chip" href="{escape(url)}" target="_blank">'
              f'<span class="survey-name">{name}</span><span class="survey-bands">{bands}</span></a>\n')
    s += f'{I}    </div>\n'
    if spec:
        ra, dec = COORDS[t]
        url = f'https://skyserver.sdss.org/dr18/VisualTools/explore/summary?ra={ra}&dec={dec}'
        s += (f'{I}    <p class="prog-note" style="margin-top: 15px;"><strong>Spectroscopy:</strong> {spec} '
              f'<a href="{escape(url)}" target="_blank">SDSS SkyServer</a></p>\n')
    s += f'{I}</section>\n'
    return s

CSS_RE = re.compile(r'[ \t]*/\* anc-extra-css:start \*/.*?/\* anc-extra-css:end \*/\n', re.S)

def css_block(page):
    out = ['            /* anc-extra-css:start */']
    for cls, (c, dark, rgb) in COLOURS.items():
        if re.search(r'\.' + cls + r'\s*\{', page):
            continue  # already defined by the page itself
        out += [f'            .{cls} {{',
                f'                border-left: 6px solid {c};',
                f'                background: linear-gradient(135deg, rgba({rgb}, 0.05) 0%, #ffffff 100%);',
                '            }',
                f'            .{cls} .dataset-header h2 {{ color: {dark}; }}',
                f'            .{cls} .dataset-header {{ border-bottom-color: rgba({rgb}, 0.2); }}',
                f'            .{cls} .button {{ background-color: {c} !important; color: #ffffff !important; border: none; }}',
                f'            .{cls} .button:hover {{ background-color: {dark} !important; }}']
    if '.status-badge {' not in page and '.status-badge{' not in page:
        out += ['            .status-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.8em; font-weight: 600; }']
    if '.status-badge.info' not in page:
        out += ['            .status-badge.info { background-color: #e0f2fe; color: #075985; }',
                '            .status-badge.progress { background-color: #fee2e2; color: #991b1b; }']
    if '.status-badge.credit' not in page:
        out += ['            .status-badge.credit { background-color: #ffe4e6; color: #9f1239; border: 1px solid #fecdd3; }']
    for sel, rule in (('figure.data-figure', '            figure.data-figure { margin: 0; text-align: center; }\n'
                       '            figure.data-figure img { max-width: 100%; height: auto; border-radius: 6px; }'),
                      ('figcaption', '            figcaption { font-size: 0.85em; color: #718096; margin-top: 8px; }')):
        if sel + ' {' not in page and sel + '{' not in page:
            out.append(rule)
    out += ['            .prog-title { margin: 0 0 6px 0; font-size: 1.2em; font-weight: 600; }',
            '            .prog-note { font-size: 0.9em; color: #4a5568; margin-bottom: 8px; }',
            '            .prog-block .meta-grid { margin-top: 8px; }',
            '            .prog-with-image { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; align-items: center; }',
            '            @media (max-width: 768px) { .prog-with-image { grid-template-columns: 1fr; } }',
            '            hr.prog-sep { border: none; border-top: 1px solid #e2e8f0; margin: 25px 0; }',
            '            .survey-grid { display: flex; flex-wrap: wrap; gap: 12px; }',
            '            .survey-chip { display: flex; flex-direction: column; gap: 2px; padding: 10px 14px; min-width: 150px;',
            '                background: rgba(255, 255, 255, 0.85); border: 1px solid #e2e8f0; border-radius: 6px;',
            '                text-decoration: none; color: inherit; transition: border-color 0.2s ease; }',
            '            .survey-chip:hover { border-color: #475569; }',
            '            .survey-name { font-weight: 700; color: #334155; font-size: 0.95em; }',
            '            .survey-bands { font-size: 0.8em; color: #718096; }',
            '            .arch-wrap { overflow-x: auto; }',
            '            .arch-table { width: 100%; border-collapse: collapse; font-size: 0.9em; margin: 0; }',
            '            .arch-table th { text-align: left; font-weight: 700; color: #57534e; border-bottom: 2px solid rgba(120, 113, 108, 0.25);',
            '                padding: 8px 10px; white-space: nowrap; }',
            '            .arch-table td { padding: 8px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; color: #4a5568; }',
            '            .arch-table tbody tr:last-child td { border-bottom: none; }',
            '            .arch-table td:first-child { font-weight: 600; color: #334155; white-space: nowrap; }',
            '            .arch-link { color: #57534e; font-weight: 600; white-space: nowrap; }',
            '            @media (max-width: 768px) {',
            '                .arch-table thead { display: none; }',
            '                .arch-table, .arch-table tbody, .arch-table tr, .arch-table td { display: block; width: 100%; }',
            '                .arch-table tr { border-bottom: 1px solid #e2e8f0; padding: 8px 0; }',
            '                .arch-table td { border: none; padding: 2px 0; }',
            '                .arch-table td:not(:first-child)::before { content: attr(data-label) ": "; font-weight: 600; color: #718096; }',
            '                .dataset-card .button { white-space: normal; line-height: 1.35; padding: 0.85em 1em; font-size: 0.95em; letter-spacing: 0.04em; }',
            '                .prog-title { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; }',
            '                .prog-title .status-badge { margin-left: 0 !important; }',
            '            }',
            '            /* anc-extra-css:end */']
    return '\n'.join(out) + '\n'

# a card = optional comment line + <section class="dataset-card ..."> ... </section>
CARD_RE = re.compile(r'(?:[ \t]*<!--[^\n]*-->\n)?[ \t]*<section class="dataset-card[^"]*"[^>]*>.*?</section>\n', re.S)
LEGACY_RE = re.compile(r'\n?[ \t]*<!-- anc-extra:start -->.*?<!-- anc-extra:end -->\n', re.S)  # first version

def order_cards(page, new_cards):
    """Drop generated and REPLACED cards, add new_cards, sort everything by WAVE."""
    page = LEGACY_RE.sub('', page)
    cards = list(CARD_RE.finditer(page))
    if not cards:
        raise SystemExit('no dataset cards found')
    a, b = cards[0].start(), cards[-1].end()
    between = CARD_RE.sub('', page[a:b])
    if between.strip():
        raise SystemExit('unexpected content between cards: ' + between.strip()[:80])
    keep = []
    for m in cards:
        blk = m.group(0)
        title = re.search(r'<h2>(.*?)</h2>', blk).group(1).strip()
        if 'data-anc-extra="1"' in blk or title in REPLACED:
            continue
        keep.append(blk)
    blocks = keep + new_cards
    def key(block):
        title = re.search(r'<h2>(.*?)</h2>', block).group(1).strip()
        if title not in WAVE:
            raise SystemExit(f'card title {title!r} missing from WAVE')
        return WAVE[title]
    blocks.sort(key=key)
    return page[:a] + '\n'.join(blocks) + page[b:]

def build(page, t, site_dir):
    ctx = (page, site_dir)
    new = [card_html(title, progs, ctx) for title, progs in CARDS.get(t, {}).items()]
    if ARCHIVE.get(t):
        new.append(archive_html(ARCHIVE[t]))
    new.append(survey_html(t, SDSS_SPEC.get(t)))
    page = CSS_RE.sub('', page)
    i = page.index('</style>')
    i = page.rfind('\n', 0, i) + 1
    page = page[:i] + css_block(page) + page[i:]
    return order_cards(page, new)

def main(argv):
    dirs = [a for a in argv if os.path.isdir(a)] or ['.']
    targets = [a for a in argv if a in COORDS] or list(COORDS)
    for d in dirs:
        for t in targets:
            fn = os.path.join(d, f'{t}_anc.html')
            raw = open(fn, 'rb').read().decode('utf-8')
            crlf = '\r\n' in raw
            page = raw.replace('\r\n', '\n')
            new = build(page, t, d)
            if crlf:
                new = new.replace('\n', '\r\n')
            if new != raw:
                open(fn, 'wb').write(new.encode('utf-8'))
                print('updated  ', fn)
            else:
                print('unchanged', fn)

if __name__ == '__main__':
    main(sys.argv[1:])
