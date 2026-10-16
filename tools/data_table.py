#!/usr/bin/env python3
"""Rebuild the "Target Coordinates" table on the Data page (data.html).

  python3 tools/data_table.py                    # this site
  python3 tools/data_table.py . ../VST_P3_P4     # this site and the public one

Positions come from COORDS below (from the ancillary pages). The period badge next to each target is
computed from data.json (P3 = nights up to 30 Sep 2025, P4 = Oct 2025 - Sep 2026, P5 = from Oct 2026),
written into the page, and refreshed from data.json in the browser when it can be read.
Only the <table class="data-table"> block (and its intro sentence) is replaced. Line endings are preserved.
"""
import re, os, sys, json

TARGETS = ['J0123-0455','J0335-1927','J0501-0733','J0542-2125','J0722-3901','J1029+2623','J1330+1810','J2107-1611','J2329-1258']
# Precise positions (from the ancillary pages; J0123-0455 Dec sign corrected: the anc page says +4.93266)
COORDS = {'J0123-0455': (20.84084, -4.93266), 'J0335-1927': (53.7668333, -19.46390), 'J0501-0733': (75.3729, -7.5525),
          'J0542-2125': (85.7392, -21.4261), 'J0722-3901': (110.6773750, -39.03310), 'J1029+2623': (157.3026604, 26.3924),
          'J1330+1810': (202.57772, 18.17581), 'J2107-1611': (316.9685, -16.19210), 'J2329-1258': (352.49114, -12.98306)}
def rw(path, func):
    raw = open(path, 'rb').read(); crlf = b'\r\n' in raw
    s = raw.decode('utf-8').replace('\r\n', '\n'); out = func(s)
    if crlf: out = out.replace('\n', '\r\n')
    return out.encode('utf-8')

def hms(ra):
    h = ra / 15; H = int(h); m = (h - H) * 60; M = int(m); sec = (m - M) * 60
    return f'{H:02d}<sup>h</sup>{M:02d}<sup>m</sup>{sec:05.2f}<sup>s</sup>'
def dms(dec):
    sg = '−' if dec < 0 else '+'; d = abs(dec); D = int(d); m = (d - D) * 60; M = int(m); sec = (m - M) * 60
    return f'{sg}{D:02d}°{M:02d}′{sec:04.1f}″'
def period_rule_js():
    return '''
<script>
/* Monitoring periods from data.json: P3 = up to 30 Sep 2025, P4 = Oct 2025 - Sep 2026, P5 = from Oct 2026 */
function vstPeriods(cb) {
  fetch('data.json').then(function (r) { return r.json(); }).then(function (j) {
    var out = {};
    (j.data || []).forEach(function (row) {
      var m = /(\\d{4}[+-]\\d{4})/.exec(row[0] || ''); if (!m) return;
      var night = row[5] || (row[2] || '').slice(0, 10), p = night <= '2025-09-30' ? 3 : (night <= '2026-09-30' ? 4 : 5);
      var k = 'J' + m[1], o = out[k] || (out[k] = { pmin: 9, pmax: 0, nights: {}, last: '' });
      o.pmin = Math.min(o.pmin, p); o.pmax = Math.max(o.pmax, p); o.nights[night] = 1; if (night > o.last) o.last = night;
    });
    Object.keys(out).forEach(function (k) { var o = out[k]; o.label = 'P' + o.pmin + (o.pmax > o.pmin ? '-P' + o.pmax : ''); o.n = Object.keys(o.nights).length; });
    cb(out);
  }).catch(function () {});
}
</script>'''

def static_periods(path='data.json'):
    import json, re as _re
    out = {}
    for row in json.load(open(path))['data']:
        m = _re.search(r'(\d{4}[+-]\d{4})', row[0] or '')
        if not m: continue
        night = row[5] or (row[2] or '')[:10]
        p = 3 if night <= '2025-09-30' else (4 if night <= '2026-09-30' else 5)
        o = out.setdefault('J' + m.group(1), [9, 0]); o[0] = min(o[0], p); o[1] = max(o[1], p)
    return {k: f'P{a}' + (f'-P{b}' if b > a else '') for k, (a, b) in out.items()}

def data_table(s, data_json='data.json'):
    PER = static_periods(data_json)
    rows = []
    for t in TARGETS:
        ra, dec = COORDS[t]
        badge = f'<span class="period-badge">{PER[t]}</span>' if t in PER else ''
        rows.append(f'''                                                <tr data-target="{t}">
                                                    <td><span class="target-badge">{t}</span>{badge}</td>
                                                    <td>{hms(ra)}<span class="deg">{ra:.5f}°</span></td>
                                                    <td>{dms(dec)}<span class="deg">{"−" if dec < 0 else "+"}{abs(dec):.5f}°</span></td>
                                                </tr>''')
    table = '''<table class="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Target ID</th>
                                                    <th>Right Ascension (J2000)</th>
                                                    <th>Declination (J2000)</th>
                                                </tr>
                                            </thead>
                                            <tbody>
''' + '\n'.join(rows) + '''
                                            </tbody>
                                        </table>
<style>
  .data-table .deg { display: block; font-size: 0.8em; color: #94a3b8; font-variant-numeric: tabular-nums; }
  .data-table td { font-variant-numeric: tabular-nums; }
  .period-badge { display: inline-block; margin-left: 8px; padding: 1px 8px; border-radius: 10px; background: #eff6ff; color: #2563eb;
    border: 1px solid #dbeafe; font-size: 0.72em; font-weight: 600; vertical-align: 1px; }
</style>''' + period_rule_js() + '''
<script>
vstPeriods(function (P) {
  document.querySelectorAll('.data-table tr[data-target]').forEach(function (tr) {
    var o = P[tr.dataset.target], b = tr.querySelector('.period-badge'); if (o && b) b.textContent = o.label;
  });
});
</script>'''
    block = '<!-- data-table:start -->\n' + table + '\n<!-- data-table:end -->'
    if '<!-- data-table:start -->' in s:      # already generated: replace the whole marked block
        s2, n = re.subn(r'<!-- data-table:start -->.*?<!-- data-table:end -->', lambda m: block, s, count=1, flags=re.S)
    else:                                     # first time: the table plus any style/scripts a previous version added after it
        s2, n = re.subn(r'<table class="data-table">.*?</table>(?:\s*<style>\s*\.data-table \.deg.*?</style>\s*<script>.*?</script>\s*<script>\s*vstPeriods.*?</script>)?',
                        lambda m: block, s, count=1, flags=re.S)
    assert n == 1
    s2 = s2.replace('<p>Below is the summary of the targets monitored in our campaign along with their Right Ascension (RA) and Declination (Dec) coordinates.</p>',
                    '<p>Below is the summary of the targets monitored in our campaign, with their J2000 coordinates and monitoring periods.</p>', 1)
    return s2


if __name__ == '__main__':
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for site in (sys.argv[1:] or [here]):
        site = os.path.abspath(site); f = os.path.join(site, 'data.html')
        new = rw(f, lambda s: data_table(s, os.path.join(site, 'data.json')))   # read + transform first
        assert len(new) > 15000, 'refusing to write a suspiciously small file'
        tmp = f + '.tmp'; open(tmp, 'wb').write(new); os.replace(tmp, f)
        print('updated', f)
