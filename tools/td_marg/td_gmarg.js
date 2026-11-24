/*
 * td_gmarg.js - in-browser port of ~/VST/gaussian_marginalization.py (marginalize()).
 * Each estimate (mu_i, sigma_i) is a Gaussian; the marginal is the weighted sum
 *   p(x) = sum_i w_i N(x | mu_i, sigma_i),  sum_i w_i = 1   (equal weights by default)
 * Same grid (200001 points over [min(mu - 8 sigma), max(mu + 8 sigma)]) and the same summaries:
 * median with 16th/84th percentiles, mode with 68.27% HPD interval, mean with exact mixture std.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TDGMarg = factory();
}(this, function () {
  'use strict';
  var SQ2PI = Math.sqrt(2 * Math.PI);

  // numpy.interp(v, xp, fp) for increasing xp
  function interp(v, xp, fp) {
    var n = xp.length;
    if (v <= xp[0]) return fp[0];
    if (v >= xp[n - 1]) return fp[n - 1];
    var lo = 0, hi = n - 1;                       // last j with xp[j] <= v
    while (hi - lo > 1) { var m = (lo + hi) >> 1; if (xp[m] <= v) lo = m; else hi = m; }
    var d = xp[lo + 1] - xp[lo];
    return d === 0 ? fp[lo] : fp[lo] + (v - xp[lo]) * (fp[lo + 1] - fp[lo]) / d;
  }

  // hpd_interval(): narrowest interval holding `mass` (assumes unimodal)
  function hpd(x, pdf, mass) {
    var n = pdf.length, order = Float64Array.from(pdf).sort().reverse(), tot = 0, i;
    for (i = 0; i < n; i++) tot += pdf[i];
    var cum = 0, k = n - 1;
    for (i = 0; i < n; i++) { cum += order[i]; if (cum / tot >= mass) { k = i; break; } }   // searchsorted (left)
    var thr = order[k], lo = Infinity, hi = -Infinity;
    for (i = 0; i < n; i++) if (pdf[i] >= thr) { if (x[i] < lo) lo = x[i]; if (x[i] > hi) hi = x[i]; }
    return [lo, hi];
  }

  function marginalize(mu, sigma, weights, opts) {
    opts = opts || {};
    var nGrid = opts.nGrid || 200001, nSig = opts.nSigma || 8, n = mu.length, i, j;
    var w = mu.map(function (_, k) { return weights ? +weights[k] : 1; });
    var ws = w.reduce(function (a, b) { return a + b; }, 0);
    w = w.map(function (v) { return v / ws; });
    var a = Infinity, b = -Infinity;
    for (i = 0; i < n; i++) { a = Math.min(a, mu[i] - nSig * sigma[i]); b = Math.max(b, mu[i] + nSig * sigma[i]); }
    var x = new Float64Array(nGrid), step = (b - a) / (nGrid - 1);
    for (j = 0; j < nGrid; j++) x[j] = a + j * step;
    x[nGrid - 1] = b;
    var comps = [], pdf = new Float64Array(nGrid);
    for (i = 0; i < n; i++) {
      var c = new Float64Array(nGrid), norm = w[i] / (sigma[i] * SQ2PI);
      for (j = 0; j < nGrid; j++) { var z = (x[j] - mu[i]) / sigma[i]; c[j] = norm * Math.exp(-0.5 * z * z); pdf[j] += c[j]; }
      comps.push(c);
    }
    var cdf = new Float64Array(nGrid), s = 0;
    for (j = 0; j < nGrid; j++) { s += pdf[j]; cdf[j] = s; }
    for (j = 0; j < nGrid; j++) cdf[j] /= s;
    var p16 = interp(0.16, cdf, x), p50 = interp(0.50, cdf, x), p84 = interp(0.84, cdf, x);
    var mean = 0; for (i = 0; i < n; i++) mean += w[i] * mu[i];
    var v = 0; for (i = 0; i < n; i++) v += w[i] * (sigma[i] * sigma[i] + (mu[i] - mean) * (mu[i] - mean));
    var im = 0; for (j = 1; j < nGrid; j++) if (pdf[j] > pdf[im]) im = j;
    var mode = x[im], h = hpd(x, pdf, 0.6827);
    return { x: x, pdf: pdf, components: comps, weights: w,
             median: p50, p16: p16, p84: p84, err_plus: p84 - p50, err_minus: p50 - p16,
             mode: mode, hpd_lo: h[0], hpd_hi: h[1], mode_err_plus: h[1] - mode, mode_err_minus: mode - h[0],
             mean: mean, std: Math.sqrt(v) };
  }

  return { marginalize: marginalize };
}));
