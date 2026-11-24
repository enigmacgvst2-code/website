# Live time-delay marginalisation (test, 24 Nov 2026)

CURRENT TEST PAGE = BOTH METHODS with a switch (td_marg_both_widget.js + td_marg_both.css; loads td_gmarg.js AND td_marg.js):
  cd ~/Sites/website; python3 tools/td_marg/build_test_both.py ../vst-squared.github.io
  JSON options: "method": "gauss"|"pycs3" (start tab), "methods": [...] (which tabs), "sigmathresh", "testmode".
  PyCS3 tab: tau slider, weights disabled, members drawn at 1/K (PyCS3's iterative sum = equal weights of the members).


CURRENT method = ~/VST/gaussian_marginalization.py (Gaussian mixture, equal or given weights):
- td_gmarg.js         port of marginalize(): same 200001-point grid, median 16-84%, mode + 68.27% HPD, mean +- mixture std
- td_gmarg_widget.js  box on the page (plot like make_plot, three summary chips, table; data-editable="1" for inputs)
- td_gmarg.css
- build_test_g.py     writes ../../../vst-squared.github.io/td_marg_test.html (DUMMY values; git-excluded there)
                      run: cd ~/Sites/website; python3 tools/td_marg/build_test_g.py ../vst-squared.github.io
- gref.py + gcases.json  check against the Python script (JS = Python to 1e-15)

PyCS3 combine_estimates port (used by the 'PyCS3' tab) with tau threshold (td_marg.js, td_marg_widget.js, td_marg.css,
build_test.py, ref.py, cmp.js, cases.json, py_out.json).
