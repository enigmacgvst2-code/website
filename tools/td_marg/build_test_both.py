# Build <site>/td_marg_test.html: empty calculator (no values in the page). Run for each site, e.g.
#   python3 tools/td_marg/build_test_both.py ../vst-squared.github.io   (git-excluded there: never published)
#   python3 tools/td_marg/build_test_both.py .                          (internal site)
# Both methods: ~/VST/gaussian_marginalization.py (td_gmarg.js) and PyCS3 combine_estimates (td_marg.js).
import os, re, sys, json
PUB = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(PUB, 'data.html'), encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in src else '\n'
CSS = open(os.path.join(HERE, 'td_marg_both.css')).read()
JS = '\n'.join(open(os.path.join(HERE, f)).read() for f in ('td_gmarg.js', 'td_marg.js', 'td_marg_both_widget.js'))
assert '</script' not in JS.lower(), 'JS must not contain a closing script tag'
DATA = {"label": "", "values": [None, None, None], "errors": [None, None, None], "weights": None, "names": None,
        "method": "gauss", "methods": ["gauss", "pycs3"], "sigmathresh": 0.5, "testmode": True}
content = '''<!-- Hero Section -->
                            <div class="hero-brand-section">
                                <h1 class="hero-title"><span class="dark-text">Time Delays marginalization</span></h1>
                            </div>
                            <div class="tdm-page">
                                <article class="tdm-card">
                                    <p class="tdm-sub tdm-sub0">Combine several estimates of the same time delay, each given as a value with its 1&sigma; error.</p>
                                    <script type="application/json" id="tdb-calc">%s</script>
                                    <div class="tdb" data-src="tdb-calc" data-editable="1"></div>
                                </article>
                            </div>
<!-- End Data Sections -->''' % json.dumps(DATA)
a, b = src.index('<!-- Hero Section -->'), src.index('<!-- End Data Sections -->') + len('<!-- End Data Sections -->')
page = src[:a] + content.replace('\n', nl) + src[b:]
page = page.replace('<li><a href="td_marg_test.html">Marginalisation</a></li>', '<li class="current_page_item"><a href="td_marg_test.html">Marginalisation</a></li>')
page = re.sub(r'<title>.*?</title>', '<title>(VST)&#178; - Time Delays marginalization</title>', page, count=1)
page = re.sub(r'<li class="current_page_item"\s*><a href="data.html">Data</a></li>', '<li><a href="data.html">Data</a></li>', page)
i = page.index('</style>'); page = page[:i] + CSS + nl + '    ' + page[i:]
i = page.rindex('</body>'); page = page[:i] + '<script>' + nl + JS + nl + '</script>' + nl + page[i:]
out = os.path.join(PUB, 'td_marg_test.html')
open(out, 'w', encoding='utf-8', newline='').write(page); print('wrote', out)
