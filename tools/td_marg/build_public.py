# Public site: "Tools" dropdown (Marginalization) on every page, last item after Data, + CSS fix in assets/css/main.css + <public>/marginalization.html (empty calculator, no values).
#   cd ~/Sites/website; python3 tools/td_marg/build_public.py ../vst-squared.github.io
# Idempotent. Rerun after ~/VST/build_website.sh (regenerated _lc pages come without the Tools menu).
import os, re, sys, glob, subprocess
PUB = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); OUT = 'marginalization.html'
ITEM = '<li><a href="%s">Marginalization</a></li>' % OUT
DATA_LI = re.compile(r'[ \t]*<li(\s+class="[^"]*")?\s*>\s*<a href="data.html">Data</a>\s*</li>')

# A dropdown as the LAST menu item: dropotron (detach:false) shifts it off-screen near the right window edge
# (left:-692px at 1280 px) -> CSS below pins the last dropdown to the right edge of the menu.
CSS_FIX = ('/* tools-menu:start  Tools dropdown is the last menu item: dropotron (detach:false) pushes it off-screen near '
           'the right edge, so pin it to the right of the menu */\n'
           '#nav > ul > li:last-child > ul.dropotron { left: auto !important; right: 0 !important; }\n/* tools-menu:end */\n')
TOOLS_BLK = re.compile(r'[ \t]*<li> \r?\n[ \t]*<a href="#">Tools</a> \r?\n[ \t]*<ul> \r?\n.*?</ul> \r?\n[ \t]*</li> \r?\n', re.S)

def add_tools(h):
    if '<nav id="nav">' not in h: return h
    nl = '\r\n' if '\r\n' in h else '\n'
    h = TOOLS_BLK.sub('', h)                      # drop any existing Tools dropdown
    h = re.sub(r'[ \t]*<li(\s+class="[^"]*")?><a href="%s">Marginalization</a></li>[ \t]*\r?\n' % OUT, '', h)  # and an old top-level link
    m = DATA_LI.search(h)
    if not m: return h
    eol = h.index('\n', m.end()) + 1                 # after Data (keeps Data's line as it is)
    ind = ' ' * 28
    block = nl.join([ind + '<li> ', ind + '    <a href="#">Tools</a> ', ind + '    <ul> ',
                     ind + '        ' + ITEM + ' ', ind + '    </ul> ', ind + '</li> ']) + nl
    return h[:eol] + block + h[eol:]

css = os.path.join(PUB, 'assets', 'css', 'main.css')
c = open(css, encoding='utf-8', newline='').read()
if 'tools-menu:start' not in c:
    open(css, 'a', encoding='utf-8', newline='').write(('' if c.endswith('\n') else '\n') + '\n' + CSS_FIX); print('CSS fix appended to', css)

n = 0
for f in sorted(glob.glob(os.path.join(PUB, '*.html'))):
    if f.endswith('_backup.html') or os.path.basename(f) == OUT: continue
    h = open(f, encoding='utf-8', newline='').read(); h2 = add_tools(h)
    if h2 != h: open(f, 'w', encoding='utf-8', newline='').write(h2); n += 1
print('Tools menu added/updated in', n, 'pages', flush=True)
subprocess.check_call([sys.executable, os.path.join(HERE, 'build_test_both.py'), PUB, OUT, 'Marginalization'])  # takes the menu from data.html
