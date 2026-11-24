# Build the local test page <public>/td_marg_test.html with DUMMY values (listed in .git/info/exclude: never published).
# Method: ~/VST/gaussian_marginalization.py (td_gmarg.js).
import os, re, sys, json
PUB = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(PUB, 'data.html'), encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in src else '\n'
CSS = open(os.path.join(HERE, 'td_gmarg.css')).read()
JS = open(os.path.join(HERE, 'td_gmarg.js')).read() + '\n' + open(os.path.join(HERE, 'td_gmarg_widget.js')).read()
assert '</script' not in JS.lower(), 'JS must not contain a closing script tag'
DATA = {"label": "A-B", "values": [12.0, 13.1, 12.4], "errors": [0.5, 0.6, 0.8], "weights": None,
        "names": ["Estimate 1 (dummy)", "Estimate 2 (dummy)", "Estimate 3 (dummy)"]}
content = '''<!-- Hero Section -->
                            <div class="hero-brand-section">
                                <h1 class="hero-title"><span class="dark-text">Time Delays</span></h1>
                            </div>
                            <div class="tdm-page">
                                <div class="tdm-test">TEST PAGE &middot; dummy values, not a measurement &middot; local only, not published.
                                Edit the numbers in the table: the marginalisation is recomputed in the browser.</div>
                                <article class="tdm-card">
                                    <div class="tdm-head"><h3>J0542-2125</h3><span class="tdp-badge">P3-P4 Monitoring</span></div>
                                    <p class="tdm-sub">Two lensed images (A, B) &middot; marginalised time delay</p>
                                    <script type="application/json" id="tdg-J0542-2125">%s</script>
                                    <div class="tdg" data-src="tdg-J0542-2125" data-editable="1"></div>
                                </article>
                            </div>
<!-- End Data Sections -->''' % json.dumps(DATA)
a, b = src.index('<!-- Hero Section -->'), src.index('<!-- End Data Sections -->') + len('<!-- End Data Sections -->')
page = src[:a] + content.replace('\n', nl) + src[b:]
page = re.sub(r'<title>.*?</title>', '<title>(VST)&#178; - Time Delays (test)</title>', page, count=1)
page = page.replace('<li class="current_page_item" ><a href="data.html">Data</a></li>', '<li><a href="data.html">Data</a></li>')
i = page.index('</style>'); page = page[:i] + CSS + nl + '    ' + page[i:]
i = page.rindex('</body>'); page = page[:i] + '<script>' + nl + JS + nl + '</script>' + nl + page[i:]
out = os.path.join(PUB, 'td_marg_test.html')
open(out, 'w', encoding='utf-8', newline='').write(page); print('wrote', out)
