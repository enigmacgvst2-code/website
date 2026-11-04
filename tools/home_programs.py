"""Home page "Observing Programs" block (timeline-bar design, 3 Nov 2026).

Inserts/refreshes the block between the hero title and "Targets Overview"
on index.html of both sites. Idempotent; keeps CRLF.
Usage: python3 tools/home_programs.py index.html ../VST_P3_P4/index.html
Text from (VST)^2-I (COOL J0542-2125), Sect. 2.4.
"""
import sys, re
HTML = '''<!-- programs:start -->
<section class="programs-block" aria-labelledby="programs-heading">
    <h3 id="programs-heading">Observing Programs</h3>
    <div class="ptl">
        <div class="ptl-bar" aria-hidden="true">
            <div class="ptl-seg ptl-pilot" style="flex: 1"><span>Pilot</span></div>
            <div class="ptl-seg ptl-inkind" style="flex: 7"><span class="ptl-long">Rubin-LSST Italian In-kind contribution</span><span class="ptl-short">In-Kind</span></div>
        </div>
        <div class="ptl-ticks" aria-hidden="true"><span style="left: 0"><b>Oct </b>2024</span><span style="left: 12.5%"><b>Oct </b>2025</span><span style="right: 0">2032</span></div>
        <div class="ptl-cols">
            <div class="ptl-col ptl-c-pilot">
                <h4>Pilot program <small>P3 &middot; Oct 2024 &ndash; Sep 2025</small></h4>
                <p>Proprietary VST program designed to target recently studied lensed quasars.</p>
                <p class="ptl-facts">ESO 114.27U3 &middot; PI C. Grillo<br>606 h allocated, 491 h observed</p>
            </div>
            <div class="ptl-col ptl-c-inkind">
                <h4><a class="ptl-h-link" href="https://sites.google.com/inaf.it/rubin-lsst-italy/italian-in-kind-contributions" target="_blank" rel="noopener">Rubin-LSST Italian In-kind contribution<span class="ptl-arrow" aria-hidden="true"> &#8599;</span></a> <small>P4 &ndash; P10 &middot; from Oct 2025</small></h4>
                <p>&ldquo;Exploiting the synergy between LSST and VST to investigate the cosmos: the expansion rate and the geometry of the Universe measured through the time delays of strongly lensed variable sources&rdquo;</p>
                <p class="ptl-facts">PI C. Grillo &middot; 4620 VST hours over the first seven years of LSST</p>
            </div>
        </div>
    </div>
</section>
<!-- programs:end -->'''
CSS = '''/* programs-css:start */
.programs-block { margin: 0 0 2.5rem; padding-bottom: 2.2rem; border-bottom: 1px solid var(--border-color); }
.ptl { text-align: left; }
.ptl-bar { display: flex; gap: 4px; height: 34px; border-radius: 9999px; overflow: hidden; }
.ptl-seg { display: flex; align-items: center; padding: 0 14px; font-weight: 700; font-size: 0.85rem; line-height: 1; text-shadow: none; white-space: nowrap; overflow: hidden;
    background: rgba(var(--rgb), 0.14); box-shadow: inset 0 0 0 1px rgba(var(--rgb), 0.30); border-radius: 9999px; }
.ptl-pilot { --rgb: 163, 165, 236; color: #6366c9; }
.ptl-bar .ptl-pilot { background: rgba(var(--rgb), 0.22); box-shadow: inset 0 0 0 1px rgba(var(--rgb), 0.7); }
.ptl-bar .ptl-inkind { background: rgba(var(--rgb), 0.42); box-shadow: inset 0 0 0 1px rgba(var(--rgb), 0.7); }
.ptl-inkind { --rgb: 76, 29, 149; color: #3b0f80; }
.ptl-short { display: none; }
.ptl-ticks { position: relative; height: 1.6em; font-size: 0.75rem; color: var(--text-muted); font-weight: 500; margin-top: 6px; }
.ptl-ticks span { position: absolute; top: 0; white-space: nowrap; }
.ptl-ticks b { font-weight: inherit; color: inherit; }
.ptl-cols { display: grid; grid-template-columns: 1fr 2fr; gap: 2rem; margin-top: 0.8rem; }
.ptl-col h4 { font-size: 1.05rem; text-transform: none; letter-spacing: 0; margin: 0 0 0.35rem; line-height: 1.35; }
.ptl-c-pilot h4 { color: #6366c9; }
.ptl-c-inkind h4 { color: #3b0f80; }
.ptl-col h4 small { display: block; color: var(--text-muted); font-weight: 600; font-size: 0.78rem; margin-top: 2px; }
.ptl-col p { font-size: 0.92rem; line-height: 1.55; color: #334155; margin: 0 0 0.5rem; }
.ptl-col p.ptl-facts { font-size: 0.85rem; color: var(--text-muted); margin: 0; }
.ptl-col h4 a.ptl-h-link { color: inherit; text-decoration: none; border-bottom: 1px solid transparent; transition: border-color 0.2s; }
.ptl-col h4 a.ptl-h-link:hover { border-bottom-color: currentColor; }
.ptl-arrow { font-size: 0.8em; opacity: 0.7; }
@media (max-width: 768px) {
    .ptl-cols { grid-template-columns: 1fr; gap: 1.2rem; }
    .ptl-long { display: none; }
    .ptl-short { display: inline; }
    .ptl-ticks b { display: none; }
}
/* programs-css:end */'''
for path in sys.argv[1:]:
    s = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    s = re.sub(r'[ \t]*<!-- programs:start -->.*?<!-- programs:end -->\r?\n(\r?\n)?', '', s, flags=re.S)
    s = re.sub(r'[ \t]*/\* programs-css:start \*/.*?/\* programs-css:end \*/\r?\n', '', s, flags=re.S)
    ind = ' ' * 28
    block = nl.join((ind + l) if l else l for l in HTML.split('\n')) + nl + nl
    anchor = ind + '<h3 style="margin-top: 1rem;">Targets Overview</h3>'
    assert s.count(anchor) == 1, path
    s = s.replace(anchor, block + anchor, 1)
    cind = ' ' * 8
    cblock = nl.join(cind + l for l in CSS.split('\n')) + nl
    i = s.index('</style>')
    j = s.rfind(nl, 0, i) + len(nl)
    s = s[:j] + cblock + s[j:]
    open(path, 'w', encoding='utf-8', newline='').write(s)
    print('ok', path)
