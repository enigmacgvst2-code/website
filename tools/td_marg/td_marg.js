/*
 * td_marg.js - in-browser port of the PyCS3 time-delay combination
 * (pycs3/tdcomb/comb.py: Group.linearize, getcombweightslist, asgetresults,
 *  confinterval, get_bestprec, compute_sigmas, combine_estimates).
 * Same algorithm as script 4b/4d of the (VST)^2 pipeline (Bonvin et al. 2018,
 * Millon et al. 2020). Only difference: each Gaussian is put on the bins with
 * its exact probability per bin (Simpson rule) instead of 5e4/5e5 random
 * draws, so the result is deterministic.
 *
 * Input estimate: {name, medians:[..], up:[..], down:[..]}  (one entry per delay label)
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TDMarg = factory();
}(this, function () {
  'use strict';

  var SQ2PI = Math.sqrt(2 * Math.PI);
  function pdf(x, mu, s) { var z = (x - mu) / s; return Math.exp(-0.5 * z * z) / (s * SQ2PI); }

  function linspace(a, b, n) {               // numpy.linspace(a, b, n)
    var out = new Array(n), step = (b - a) / (n - 1);
    for (var i = 0; i < n; i++) out[i] = a + i * step;
    out[n - 1] = b;
    return out;
  }

  // bins as in 4b / group_estimate: [min(med) - 10 min(err_down), max(med) + 10 max(err_up)]
  function makeBins(ests, nlab, testmode) {
    var nbins = testmode ? 500 : 5000, out = [];
    for (var i = 0; i < nlab; i++) {
      var med = ests.map(function (e) { return e.medians[i]; });
      var dn = ests.map(function (e) { return e.down[i]; });
      var up = ests.map(function (e) { return e.up[i]; });
      out.push(linspace(Math.min.apply(null, med) - 10 * Math.min.apply(null, dn),
                        Math.max.apply(null, med) + 10 * Math.max.apply(null, up), nbins));
    }
    return out;
  }

  // Group.linearize: Gaussian(mean = median, sigma = (up+down)/2), mass per bin, normalised
  function linearize(g, binslist) {
    g.lins = binslist.map(function (b, i) {
      var mu = g.medians[i], s = (g.up[i] + g.down[i]) / 2, w = new Array(b.length - 1), tot = 0;
      for (var k = 0; k < b.length - 1; k++) {
        var a = b[k], c = b[k + 1];
        w[k] = (c - a) / 6 * (pdf(a, mu, s) + 4 * pdf((a + c) / 2, mu, s) + pdf(c, mu, s));
        tot += w[k];
      }
      for (k = 0; k < w.length; k++) w[k] /= tot;
      return w;
    });
    g.binslist = binslist;
    return g;
  }

  // numpy.histogram(xs, weights, bins=nb) with equal-width bins over [min, max]
  function histogram(xs, ws, nb) {
    var lo = Math.min.apply(null, xs), hi = Math.max.apply(null, xs);
    var edges = linspace(lo, hi, nb + 1), hist = new Array(nb).fill(0), norm = nb / (hi - lo);
    for (var j = 0; j < xs.length; j++) {
      var x = xs[j], k = Math.floor((x - lo) * norm);
      if (k === nb) k -= 1;
      if (x < edges[k]) k -= 1;
      if (x >= edges[k + 1] && k !== nb - 1) k += 1;
      hist[k] += ws[j];
    }
    return { hist: hist, edges: edges };
  }

  // comb.confinterval (non-cumulative): returns [median, err_down, err_up]
  function confinterval(xs, ws, testmode, conflevel) {
    conflevel = conflevel || 0.68;
    var h = histogram(xs, ws, testmode ? 500 : 10000), hist = h.hist, e = h.edges;
    var tot = 0, i; for (i = 0; i < hist.length; i++) tot += hist[i];
    function mid(ind) { var p = ind - 1 < 0 ? e.length - 1 : ind - 1; return (e[ind] + e[p]) / 2; }
    var frac = 0, med, lowv, topv, lim = (1 - conflevel) / 2;
    for (i = 0; i < hist.length; i++) { frac += hist[i]; if (frac / tot >= 0.5) { med = mid(i); break; } }
    frac = 0;
    for (i = 0; i < hist.length; i++) { frac += hist[i]; if (frac / tot > lim) { lowv = mid(i); break; } }
    frac = 0;
    for (i = 0; i < hist.length; i++) { frac += hist[i]; if (frac / tot > 1 - lim) { topv = mid(i); break; } }
    return [med, med - lowv, topv - med];
  }

  function centers(b) { var c = new Array(b.length - 1); for (var k = 0; k < c.length; k++) c[k] = 0.5 * (b[k] + b[k + 1]); return c; }

  // comb.asgetresults(getcombweightslist(groups)): bin-by-bin mean of the pdfs
  function sumGroups(list, testmode) {
    var b = list[0].binslist, g = { name: list.map(function (x) { return x.name; }).join('+'),
      medians: [], up: [], down: [], lins: [], binslist: b };
    for (var i = 0; i < b.length; i++) {
      var w = new Array(b[i].length - 1).fill(0);
      list.forEach(function (x) { for (var k = 0; k < w.length; k++) w[k] += x.lins[i][k]; });
      for (var k = 0; k < w.length; k++) w[k] /= list.length;
      var ci = confinterval(centers(b[i]), w, testmode);
      g.medians.push(ci[0]); g.down.push(ci[1]); g.up.push(ci[2]); g.lins.push(w);
    }
    return g;
  }

  // comb.get_bestprec (refimg = None)
  function bestprec(groups) {
    var n = groups[0].medians.length, avg = [], i;
    for (i = 0; i < n; i++) avg.push(groups.reduce(function (s, g) { return s + g.medians[i]; }, 0) / groups.length);
    var precs = groups.map(function (g) {
      var p = 0; for (var j = 0; j < n; j++) p += ((g.up[j] + g.down[j]) / 2) / Math.abs(avg[j]); return p;
    });
    return precs.indexOf(Math.min.apply(null, precs));
  }

  // comb.compute_sigmas
  function sigmas(ref, groups) {
    return groups.map(function (g) {
      return g.medians.map(function (m, i) {
        var r = ref.medians[i];
        return m < r ? Math.abs(m - r) / Math.sqrt(g.up[i] * g.up[i] + ref.down[i] * ref.down[i])
                     : Math.abs(m - r) / Math.sqrt(g.down[i] * g.down[i] + ref.up[i] * ref.up[i]);
      });
    });
  }

  function inTension(ref, groups, thresh) {
    var s = sigmas(ref, groups);
    return groups.filter(function (g, k) { return s[k].some(function (v) { return v > thresh; }); });
  }

  // comb.combine_estimates + the 4b steps around it (bins, linearize)
  function combine(estimates, opts) {
    opts = opts || {};
    var tau = opts.sigmathresh === undefined ? 0.5 : opts.sigmathresh;
    var testmode = opts.testmode === undefined ? true : opts.testmode;
    var nlab = estimates[0].medians.length;
    var bins = makeBins(estimates, nlab, testmode);
    var groups = estimates.map(function (e, k) {
      return linearize({ name: e.name, index: k, medians: e.medians.slice(), up: e.up.slice(), down: e.down.slice() }, bins);
    });
    var mygroups = groups.slice();
    var ref = groups[bestprec(groups)], members = [ref.index], steps = [];
    var thresh = inTension(ref, groups, tau), i = 1;
    steps.push({ ref: ref.name, sigmas: sigmas(ref, groups) });
    while (thresh.length > 0) {
      var add = thresh[bestprec(thresh)], tocombine = [];
      for (var j = 0; j < i; j++) tocombine.push(ref);
      tocombine.push(add);
      var comb = sumGroups(tocombine, testmode);
      comb.name = members.concat([add.index]).map(function (k) { return groups[k].name; }).join(' + ');
      members.push(add.index);
      mygroups = mygroups.filter(function (g) { return g !== add && g.name !== ref.name; });
      thresh = inTension(comb, mygroups, tau);
      steps.push({ ref: comb.name, sigmas: sigmas(comb, mygroups) });
      ref = comb; i++;
    }
    return { combined: { medians: ref.medians, up: ref.up, down: ref.down, lins: ref.lins },
             members: members, groups: groups, bins: bins, sigmathresh: tau, testmode: testmode, steps: steps };
  }

  return { combine: combine, sigmas: sigmas, confinterval: confinterval, linearize: linearize, makeBins: makeBins };
}));
