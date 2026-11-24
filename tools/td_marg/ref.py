# Reference: run the real PyCS3 comb.py (pycs3.gen.util stubbed) on given estimates, 4b-style.
import sys, types, json, importlib.util, pickle, numpy as np, logging
logging.disable(logging.CRITICAL)
COMB = sys.argv[1]
for m in ['pycs3', 'pycs3.gen', 'pycs3.gen.util', 'pycs3.tdcomb']:
    sys.modules[m] = types.ModuleType(m)
spec = importlib.util.spec_from_file_location('pycs3.tdcomb.comb', COMB)
comb = importlib.util.module_from_spec(spec); sys.modules['pycs3.tdcomb.comb'] = comb
spec.loader.exec_module(comb)
sys.modules['pycs3'].tdcomb = sys.modules['pycs3.tdcomb']; sys.modules['pycs3.tdcomb'].comb = comb

def run(ests, tau, testmode, seed):
    np.random.seed(seed)
    labels = ['L%d' % i for i in range(len(ests[0]['medians']))]
    groups = [comb.Group(labels, list(e['medians']), list(e['up']), list(e['down']), e['name']) for e in ests]
    nb = 500 if testmode else 5000
    M = np.array([g.medians for g in groups]); U = np.array([g.errors_up for g in groups]); D = np.array([g.errors_down for g in groups])
    bl = [np.linspace(M[:, i].min() - 10 * D[:, i].min(), M[:, i].max() + 10 * U[:, i].max(), nb) for i in range(len(labels))]
    for g in groups:
        g.binslist = bl; g.linearize(testmode=testmode, verbose=False)
    c, _ = comb.combine_estimates(groups, sigmathresh=tau, verbose=False, testmode=testmode)
    return [float(c.medians[0]), float(c.errors_down[0]), float(c.errors_up[0]), c.name]

if __name__ == '__main__':
    cases = json.load(open(sys.argv[2]))
    out = []
    for cs in cases:
        if 'pkl' in cs:
            gs = pickle.load(open(cs['pkl'], 'rb'))
            cs['ests'] = [{'name': g.name, 'medians': [float(x) for x in g.medians], 'up': [float(x) for x in g.errors_up],
                           'down': [float(x) for x in g.errors_down]} for g in gs]
        res = [run(cs['ests'], cs['tau'], cs['testmode'], s) for s in range(cs.get('nseed', 5))]
        out.append({'case': cs['label'], 'ests': cs['ests'], 'tau': cs['tau'], 'testmode': cs['testmode'], 'py': res})
    json.dump(out, open(sys.argv[3], 'w'))
