/*
 * td_gmarg_widget.js - live Gaussian marginalisation box for the (VST)^2 site (needs td_gmarg.js).
 * Markup: a JSON script element with id "tdg-<target>" holding
 *   { "label": "A-B", "values": [..], "errors": [..], "weights": null | [..], "names": null | [..] }
 * and a div with class "tdg" and data-src="tdg-<target>" (optional data-editable="1").
 * Figure and numbers follow ~/VST/gaussian_marginalization.py.
 */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var SUM = [  // name, keys, colour, dash  (as in make_plot)
    { name: 'Median, 16–84%', v: 'median', m: 'err_minus', p: 'err_plus', col: '#4287f5', dash: '' },
    { name: 'Mode, 68% HPD', v: 'mode', m: 'mode_err_minus', p: 'mode_err_plus', col: '#42daf5', dash: '7 4' },
    { name: 'Mean ± std', v: 'mean', m: 'std', p: 'std', col: '#b4edd3', dash: '2 4' }];
  var COMP_DASH = ['8 5', '10 4 2 4', '2 4', '8 3 2 3 2 3', '1 5'];

  function el(tag, attrs, parent, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text !== undefined) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function h(tag, cls, parent, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  }
  function f2(v) { return (v < 0 ? '&minus;' : '') + Math.abs(v).toFixed(2); }
  function t2(v) { return (v < 0 ? '−' : '') + Math.abs(v).toFixed(2); }
  function valErr(v, m, p) {
    return Math.abs(m - p) < 0.005 ? f2(v) + ' &plusmn; ' + p.toFixed(2)
      : f2(v) + '<span class="tdg-ud"><sup>+' + p.toFixed(2) + '</sup><sub>&minus;' + m.toFixed(2) + '</sub></span>';
  }
  function niceTicks(lo, hi, n) {
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log10(span / n))), r = n / span * step;
    if (r <= 0.15) step *= 10; else if (r <= 0.35) step *= 5; else if (r <= 0.75) step *= 2;
    var out = []; for (var v = Math.ceil(lo / step - 1e-9) * step; v <= hi + 1e-9 * step; v += step) out.push(+v.toFixed(10));
    return { ticks: out, step: step };
  }
  function tickTxt(v, step) { var d = step < 1 ? (step < 0.1 ? 2 : 1) : 0; return (v < 0 ? '−' : '') + Math.abs(v).toFixed(d); }

  function plot(box, d, r) {
    var W = Math.max(300, Math.min(760, Math.round(box.clientWidth || 760))), small = W < 520;
    var L = small ? 40 : 52, R = 8, T = 10, PH = small ? 170 : 230, BAR = 22, H = T + PH + 3 * BAR + 14 + 40;
    var mu = d.values, sg = d.errors, lo = Infinity, hi = -Infinity, i, j;
    for (i = 0; i < mu.length; i++) { lo = Math.min(lo, mu[i] - 4 * sg[i]); hi = Math.max(hi, mu[i] + 4 * sg[i]); }
    var top = 0; for (j = 0; j < r.pdf.length; j++) if (r.pdf[j] > top) top = r.pdf[j];
    var ytop = top * 1.12, y0 = T + PH;
    var X = function (v) { return L + (v - lo) / (hi - lo) * (W - L - R); };
    var Y = function (p) { return y0 - p / ytop * PH; };
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'tdg-svg', role: 'img',
      'aria-label': 'Probability density of the time delay: the estimates, their marginal and its summaries' }, box);
    // curve path, sampled on ~700 points inside the x range
    var x = r.x, i0 = 0, i1 = x.length - 1;
    while (i0 < i1 && x[i0] < lo) i0++;
    while (i1 > i0 && x[i1] > hi) i1--;
    var stride = Math.max(1, Math.floor((i1 - i0) / 700));
    function path(arr) {
      var s = '';
      for (var k = i0; k <= i1; k += stride) s += (k === i0 ? 'M' : 'L') + X(x[k]).toFixed(1) + ' ' + Y(arr[k]).toFixed(1);
      return s + 'L' + X(x[i1]).toFixed(1) + ' ' + Y(arr[i1]).toFixed(1);
    }
    // axes
    var yt = niceTicks(0, ytop, small ? 4 : 5);
    yt.ticks.forEach(function (v) {
      if (v > ytop) return;
      el('line', { x1: L - 5, x2: L, y1: Y(v), y2: Y(v), stroke: '#334155' }, svg);
      el('text', { x: L - 8, y: Y(v) + 4, 'text-anchor': 'end', class: 'tdg-ax' }, svg, tickTxt(v, yt.step));
    });
    el('text', { x: 12, y: T + PH / 2, class: 'tdg-ax', transform: 'rotate(-90 12 ' + (T + PH / 2) + ')', 'text-anchor': 'middle' },
       svg, small ? 'Prob. density' : 'Probability density');
    var yb = H - 40;
    el('line', { x1: L, x2: L, y1: T, y2: yb, stroke: '#334155' }, svg);
    el('line', { x1: L, x2: W - R, y1: yb, y2: yb, stroke: '#334155' }, svg);
    el('line', { x1: L, x2: W - R, y1: y0, y2: y0, stroke: '#0f172a', 'stroke-width': 0.8 }, svg);
    var xt = niceTicks(lo, hi, small ? 4 : 6);
    xt.ticks.forEach(function (v) {
      el('line', { x1: X(v), x2: X(v), y1: yb, y2: yb + 5, stroke: '#334155' }, svg);
      el('text', { x: X(v), y: yb + 18, 'text-anchor': 'middle', class: 'tdg-ax' }, svg, tickTxt(v, xt.step));
    });
    el('text', { x: (L + W - R) / 2, y: yb + 34, 'text-anchor': 'middle', class: 'tdg-axl' }, svg,
       'Time delay ' + d.label.replace(/-/g, '–') + ' (days)');
    // components (weighted, so they add up to the marginal) and marginal
    r.components.forEach(function (c, k) {
      el('path', { d: path(c), fill: 'none', stroke: '#8c8c8c', 'stroke-width': 2, 'stroke-dasharray': COMP_DASH[k % COMP_DASH.length] }, svg);
    });
    el('path', { d: path(r.pdf), fill: 'none', stroke: '#000', 'stroke-width': 2.6 }, svg);
    // summaries: vertical line up to the curve + error bar below the zero line
    SUM.forEach(function (s, k) {
      var v = r[s[ 'v' ]], em = r[s.m], ep = r[s.p], pv = 0;
      // np.interp(val, x, pdf)
      var a = 0, b = x.length - 1; while (b - a > 1) { var m = (a + b) >> 1; if (x[m] <= v) a = m; else b = m; }
      pv = r.pdf[a] + (v - x[a]) * (r.pdf[b] - r.pdf[a]) / (x[b] - x[a]);
      el('line', { x1: X(v), x2: X(v), y1: y0, y2: Y(pv), stroke: s.col, 'stroke-width': 2.5, 'stroke-dasharray': s.dash }, svg);
      var y = y0 + 14 + k * BAR;
      el('line', { x1: X(v - em), x2: X(v + ep), y1: y, y2: y, stroke: s.col, 'stroke-width': 2 }, svg);
      [v - em, v + ep].forEach(function (u) { el('line', { x1: X(u), x2: X(u), y1: y - 5, y2: y + 5, stroke: s.col, 'stroke-width': 2 }, svg); });
      el('circle', { cx: X(v), cy: y, r: 4.5, fill: s.col }, svg);
    });
  }

  function render(root, d) {
    var r = TDGMarg.marginalize(d.values, d.errors, d.weights);
    var res = root.querySelector('.tdg-res');
    res.innerHTML = '';
    SUM.forEach(function (s, k) {
      h('div', 'tdg-chip' + (k === 0 ? ' tdg-main' : ''), res,
        '<i style="background:' + s.col + '"></i><span class="tdg-sn">' + s.name + '</span> <span class="tdg-v">' +
        valErr(r[s.v], r[s.m], r[s.p]) + ' d</span>');
    });
    var pl = root.querySelector('.tdg-plot'); pl.innerHTML = ''; plot(pl, d, r);
    var lg = root.querySelector('.tdg-legend'); lg.innerHTML = '';
    d.values.forEach(function (v, k) {
      var it = h('span', 'tdg-li', lg), sv = el('svg', { width: 30, height: 10, 'aria-hidden': 'true' }, it);
      el('line', { x1: 0, x2: 30, y1: 5, y2: 5, stroke: '#8c8c8c', 'stroke-width': 2, 'stroke-dasharray': COMP_DASH[k % COMP_DASH.length] }, sv);
      it.appendChild(document.createTextNode((d.names && d.names[k] ? d.names[k] + ': ' : '') + t2(v) + ' ± ' + d.errors[k].toFixed(2)));
    });
    var it = h('span', 'tdg-li', lg), sv = el('svg', { width: 30, height: 10, 'aria-hidden': 'true' }, it);
    el('line', { x1: 0, x2: 30, y1: 5, y2: 5, stroke: '#000', 'stroke-width': 2.6 }, sv);
    it.appendChild(document.createTextNode('Marginal (sum)'));
    Array.prototype.forEach.call(root.querySelectorAll('.tdg-w'), function (c, k) { c.textContent = (100 * r.weights[k]).toFixed(0) + '%'; });
  }

  function build(root) {
    var d = JSON.parse(document.getElementById(root.getAttribute('data-src')).textContent);
    var editable = root.getAttribute('data-editable') === '1';
    if (!d.weights) d.weights = d.values.map(function () { return 1; });
    root.innerHTML = '';
    h('div', 'tdg-res', root);
    h('div', 'tdg-plot', root);
    h('div', 'tdg-legend', root);
    var tbl = h('table', 'tdg-tbl', root, '<thead><tr><th>Estimate</th><th>Time delay (days)</th><th>Error (days)</th>' +
      '<th>Weight</th><th></th></tr></thead><tbody></tbody>');
    var tb = tbl.querySelector('tbody');
    d.values.forEach(function (v, k) {
      var tr = h('tr', '', tb);
      h('td', 'tdg-name', tr, d.names && d.names[k] ? d.names[k] : 'Estimate ' + (k + 1));
      [['values', 'time delay'], ['errors', 'error'], ['weights', 'relative weight']].forEach(function (f) {
        var td = h('td', 'tdg-num', tr);
        if (!editable) { td.innerHTML = f[0] === 'weights' ? '' : f2(d[f[0]][k]); return; }
        var inp = h('input', 'tdg-in', td); inp.type = 'number'; inp.step = 'any'; inp.value = d[f[0]][k];
        inp.setAttribute('aria-label', (d.names && d.names[k] ? d.names[k] : 'Estimate ' + (k + 1)) + ' ' + f[1]);
        inp.addEventListener('input', function () {
          var x = parseFloat(inp.value);
          if (!isFinite(x) || (f[0] !== 'values' && x <= 0)) { inp.classList.add('bad'); return; }
          inp.classList.remove('bad'); d[f[0]][k] = x; render(root, d);
        });
      });
      h('td', 'tdg-w tdg-num', tr);
    });
    h('p', 'tdg-note', root,
      'Each estimate is a Gaussian; the marginal distribution is their weighted sum (equal weights unless stated). ' +
      'Grey curves: the weighted estimates, which add up to the marginal (black). Because the marginal is generally asymmetric, ' +
      'three summaries are given: median with 16th&ndash;84th percentiles, mode with the 68% highest-density interval, ' +
      'and mean with standard deviation. Computed live in your browser.');
    render(root, d);
    var lastW = root.clientWidth;
    window.addEventListener('resize', function () { if (Math.abs(root.clientWidth - lastW) > 30) { lastW = root.clientWidth; render(root, d); } });
  }

  function init() { Array.prototype.forEach.call(document.querySelectorAll('.tdg[data-src]'), build); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
