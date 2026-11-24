const T = require('./td_marg.js'), out = require('./py_out.json');
for (const c of out) {
  const t0 = Date.now();
  const r = T.combine(c.ests, { sigmathresh: c.tau, testmode: c.testmode });
  const ms = Date.now() - t0, cb = r.combined;
  const py = c.py.map(p => p.slice(0, 3));
  const mean = k => py.reduce((s, p) => s + p[k], 0) / py.length;
  const span = k => Math.max(...py.map(p => p[k])) - Math.min(...py.map(p => p[k]));
  console.log(`\n== ${c.case}  (${c.ests.length} estimates, ${ms} ms)`);
  console.log(`  JS : ${cb.medians[0].toFixed(3)} -${cb.down[0].toFixed(3)} +${cb.up[0].toFixed(3)}   members: ${r.members.map(k => c.ests[k].name).join(', ')}`);
  console.log(`  Py : ${mean(0).toFixed(3)} -${mean(1).toFixed(3)} +${mean(2).toFixed(3)}   (seed spread ${span(0).toFixed(3)}/${span(1).toFixed(3)}/${span(2).toFixed(3)})   members: ${[...new Set(c.py.map(p => p[3]))].join(' | ')}`);
}
