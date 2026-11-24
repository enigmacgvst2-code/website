import sys, json, importlib.util
spec = importlib.util.spec_from_file_location('gm', sys.argv[1]); gm = importlib.util.module_from_spec(spec); spec.loader.exec_module(gm)
K = ['median','err_minus','err_plus','mode','mode_err_minus','mode_err_plus','mean','std']
out = []
for c in json.load(open(sys.argv[2])):
    r = gm.marginalize(c['v'], c['e'], c.get('w'))
    out.append({'c': c, 'py': {k: float(r[k]) for k in K}})
json.dump(out, open(sys.argv[3], 'w'))
