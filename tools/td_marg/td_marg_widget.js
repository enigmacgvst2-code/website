/*
 * td_marg_widget.js - live time-delay combination box for the (VST)^2 public site.
 * Needs td_marg.js (window.TDMarg). Markup:
 *   a JSON script element with id "tdm-<target>" holding
 *     { "labels": ["A-B"], "sigmathresh": 0.5, "testmode": true,
 *       "estimates": [ {"name": "...", "medians": [..], "up": [..], "down": [..]}, ... ] }
 *   and a div with class "tdm" and data-src="tdm-<target>" (optional data-editable="1", data-slider="0").
 */
(function () {
  'use strict';
  var COLORS = ['#4169e1', '#dc143c', '#2e8b57', '#9932cc', '#ff8c00', '#cd5c5c', '#800080', '#a52a2a'];
  var NS = 'http://www.w3.org/2000/svg';

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
  function dec(err) { return err < 1 ? 2 : 1; }
  function fmtVal(m, dn, up) {
    var d = dec(Math.min(dn, up)), sgn = m > 0 ? '+' : (m < 0 ? '&minus;' : '');
    var v = sgn + Math.abs(m).toFixed(d);
    if (Math.abs(up - dn) < Math.pow(10, -d) / 2) return v + ' &plusmn; ' + ((up + dn) / 2).toFixed(d);
    return v + '<span class="tdm-ud"><sup>+' + up.toFixed(d) + '</sup><sub>&minus;' + dn.toFixed(d) + '</sub></span>';
  }
  function fmtPrec(m, dn, up) {
    var p = 100 * (up + dn) / 2 / Math.abs(m);
    return (p < 10 ? p.toFixed(1) : p.toFixed(0)) + '%';
  }
  function niceTicks(lo, hi, n) {
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log10(span / n))), err = n / span * step;
    if (err <= 0.15) step *= 10; else if (err <= 0.35) step *= 5; else if (err <= 0.75) step *= 2;
    var out = []; for (var v = Math.ceil(lo / step) * step; v <= hi + 1e-9 * step; v += step) out.push(+v.toFixed(10));
    return { ticks: out, step: step };
  }
  function pairLabel(l) { return l.replace(/-/g, '–'); }

  function plot(box, r, li, label, est) {
    var W = Math.max(300, Math.min(720, Math.round(box.clientWidth || 720))), L = 4, R = 4, PDFH = W < 500 ? 64 : 78, ROW = 34, TOP = 8;
    var n = est.length, H = TOP + PDFH + 10 + (n + 1) * ROW + 40;
    var c = r.combined, cm = c.medians[li], cd = c.down[li], cu = c.up[li];
    var lo = cm - 4 * cd, hi = cm + 4 * cu;
    est.forEach(function (e) { lo = Math.min(lo, e.medians[li] - 1.6 * e.down[li]); hi = Math.max(hi, e.medians[li] + 1.6 * e.up[li]); });
    var pad = 0.04 * (hi - lo); lo -= pad; hi += pad;
    var X = function (v) { return L + (v - lo) / (hi - lo) * (W - L - R); };
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'tdm-svg', role: 'img',
      'aria-label': 'Time delay ' + pairLabel(label) + ': estimates and their combination' }, box);
    var yAxis = TOP + PDFH + 10 + (n + 1) * ROW + 4;

    // combined 1-sigma band + median line
    el('rect', { x: X(cm - cd), y: TOP, width: X(cm + cu) - X(cm - cd), height: yAxis - TOP, fill: '#0f172a', 'fill-opacity': 0.07 }, svg);
    el('line', { x1: X(cm), x2: X(cm), y1: TOP, y2: yAxis, stroke: '#0f172a', 'stroke-opacity': 0.45, 'stroke-dasharray': '4 4' }, svg);

    // PDF panel: binned pdfs as densities
    var b = r.bins[li], cen = [], wid = b[1] - b[0];
    for (var k = 0; k < b.length - 1; k++) cen.push(0.5 * (b[k] + b[k + 1]));
    var curves = r.groups.map(function (g) { return g.lins[li]; }).concat([c.lins[li]]);
    var ymax = 0; curves.forEach(function (w) { w.forEach(function (v) { if (v > ymax) ymax = v; }); });
    function path(w, close) {
      var d = '', first = true;
      for (var k = 0; k < cen.length; k++) {
        if (cen[k] < lo || cen[k] > hi) continue;
        var x = X(cen[k]).toFixed(1), y = (TOP + PDFH - w[k] / ymax * (PDFH - 6)).toFixed(1);
        if (first && close) d += 'M' + x + ' ' + (TOP + PDFH) + 'L' + x + ' ' + y;
        else d += (first ? 'M' : 'L') + x + ' ' + y;
        first = false; var lastx = x;
      }
      if (close) d += 'L' + lastx + ' ' + (TOP + PDFH) + 'Z';
      return d;
    }
    el('path', { d: path(c.lins[li], true), fill: '#0f172a', 'fill-opacity': 0.14, stroke: '#0f172a', 'stroke-width': 1.8 }, svg);
    r.groups.forEach(function (g, gi) {
      el('path', { d: path(g.lins[li], false), fill: 'none', stroke: COLORS[gi % COLORS.length], 'stroke-width': 1.4,
        'stroke-opacity': r.members.indexOf(gi) >= 0 ? 0.95 : 0.45, 'stroke-dasharray': r.members.indexOf(gi) >= 0 ? '' : '5 4' }, svg);
    });
    el('line', { x1: L, x2: W - R, y1: TOP + PDFH, y2: TOP + PDFH, stroke: '#cbd5e1' }, svg);

    // rows
    function row(i, m, dn, up, name, val, color, used, bold) {
      var y0 = TOP + PDFH + 10 + i * ROW, y = y0 + 23;
      el('text', { x: L, y: y0 + 11, class: 'tdm-t' + (bold ? ' tdm-b' : ''), fill: bold ? '#0f172a' : color }, svg, name);
      var tv = el('text', { x: W - R, y: y0 + 11, 'text-anchor': 'end', class: 'tdm-t tdm-num' + (bold ? ' tdm-b' : '') }, svg);
      tv.textContent = val;
      el('line', { x1: X(m - dn), x2: X(m + up), y1: y, y2: y, stroke: color, 'stroke-width': bold ? 2.4 : 1.8 }, svg);
      [m - dn, m + up].forEach(function (v) { el('line', { x1: X(v), x2: X(v), y1: y - 5, y2: y + 5, stroke: color, 'stroke-width': bold ? 2.4 : 1.8 }, svg); });
      el('circle', { cx: X(m), cy: y, r: bold ? 5.5 : 4.5, fill: used ? color : '#fff', stroke: color, 'stroke-width': 1.8 }, svg);
    }
    function txt(m, dn, up) {
      var d = dec(Math.min(dn, up)), s = (m > 0 ? '+' : m < 0 ? '−' : '') + Math.abs(m).toFixed(d);
      return Math.abs(up - dn) < Math.pow(10, -d) / 2 ? s + ' ± ' + ((up + dn) / 2).toFixed(d)
                                                       : s + ' +' + up.toFixed(d) + ' / −' + dn.toFixed(d);
    }
    est.forEach(function (e, gi) {
      row(gi, e.medians[li], e.down[li], e.up[li], e.name, txt(e.medians[li], e.down[li], e.up[li]),
          COLORS[gi % COLORS.length], r.members.indexOf(gi) >= 0, false);
    });
    row(n, cm, cd, cu, 'Combined (τ = ' + r.sigmathresh.toFixed(2) + ')', txt(cm, cd, cu), '#0f172a', true, true);

    // x axis
    el('line', { x1: L, x2: W - R, y1: yAxis, y2: yAxis, stroke: '#94a3b8' }, svg);
    var t = niceTicks(lo, hi, W < 500 ? 5 : 7);
    t.ticks.forEach(function (v) {
      el('line', { x1: X(v), x2: X(v), y1: yAxis, y2: yAxis + 5, stroke: '#94a3b8' }, svg);
      el('text', { x: X(v), y: yAxis + 18, 'text-anchor': 'middle', class: 'tdm-ax' }, svg,
         (v < 0 ? '−' : '') + Math.abs(v).toFixed(t.step < 1 ? (t.step < 0.1 ? 2 : 1) : 0));
    });
    el('text', { x: (L + W - R) / 2, y: yAxis + 34, 'text-anchor': 'middle', class: 'tdm-ax tdm-axl' }, svg,
       'Time delay ' + pairLabel(label) + ' (days)');
  }

  function render(root, data, tau) {
    var est = data.estimates;
    var r = TDMarg.combine(est, { sigmathresh: tau, testmode: data.testmode !== false });
    var res = root.querySelector('.tdm-res'), plots = root.querySelector('.tdm-plots'), tb = root.querySelector('.tdm-tbody');
    res.innerHTML = '';
    data.labels.forEach(function (l, li) {
      var c = r.combined;
      h('div', 'tdm-chip', res, '<span class="tdm-pair">' + pairLabel(l) + '</span> <span class="tdm-v">' +
        fmtVal(c.medians[li], c.down[li], c.up[li]) + ' days</span> <span class="tdm-p">' +
        fmtPrec(c.medians[li], c.down[li], c.up[li]) + '</span>');
    });
    plots.innerHTML = '';
    data.labels.forEach(function (l, li) { plot(h('div', 'tdm-plot', plots), r, li, l, est); });
    // tension of each estimate with the combined value (worst pair)
    var sig = TDMarg.sigmas(r.combined, r.groups);
    Array.prototype.forEach.call(tb.querySelectorAll('tr'), function (tr, gi) {
      tr.querySelector('.tdm-ten').textContent = Math.max.apply(null, sig[gi]).toFixed(2) + 'σ';
      var used = r.members.indexOf(gi) >= 0;
      tr.querySelector('.tdm-use').innerHTML = used ? '<span class="tdm-yes">Combined</span>' : '<span class="tdm-no">Not needed</span>';
    });
    root.querySelector('.tdm-tauv').textContent = tau.toFixed(2);
  }

  function build(root) {
    var data = JSON.parse(document.getElementById(root.getAttribute('data-src')).textContent);
    var tau0 = data.sigmathresh === undefined ? 0.5 : data.sigmathresh, editable = root.getAttribute('data-editable') === '1';
    root.innerHTML = '';
    h('div', 'tdm-res', root);
    if (root.getAttribute('data-slider') !== '0') {
      var ctl = h('div', 'tdm-ctl', root,
        '<label>Tension threshold &tau; = <b class="tdm-tauv"></b>' +
        '<input type="range" min="0" max="3" step="0.05" value="' + tau0 + '" aria-label="Tension threshold tau"></label>' +
        '<button type="button" class="tdm-reset">Reset to ' + tau0.toFixed(2) + '</button>');
    }
    h('div', 'tdm-plots', root);
    var tbl = h('table', 'tdm-tbl', root,
      '<thead><tr><th>Estimate</th>' + data.labels.map(function (l) { return '<th>' + pairLabel(l) + ' (days)</th>'; }).join('') +
      '<th>Tension</th><th></th></tr></thead><tbody class="tdm-tbody"></tbody>');
    var tb = tbl.querySelector('tbody');
    data.estimates.forEach(function (e, gi) {
      var tr = h('tr', '', tb), td = h('td', 'tdm-name', tr);
      td.innerHTML = '<i style="background:' + COLORS[gi % COLORS.length] + '"></i>';
      td.appendChild(document.createTextNode(e.name));
      data.labels.forEach(function (l, li) {
        var c = h('td', 'tdm-num', tr);
        if (!editable) { c.innerHTML = fmtVal(e.medians[li], e.down[li], e.up[li]); return; }
        [['medians', 'value'], ['up', '+ err'], ['down', '− err']].forEach(function (f) {
          var inp = h('input', 'tdm-in', c); inp.type = 'number'; inp.step = 'any'; inp.value = e[f[0]][li];
          inp.setAttribute('aria-label', e.name + ' ' + f[1]); inp.title = f[1];
          inp.addEventListener('input', function () {
            var v = parseFloat(inp.value);
            if (!isFinite(v) || (f[0] !== 'medians' && v <= 0)) { inp.classList.add('bad'); return; }
            inp.classList.remove('bad'); e[f[0]][li] = v; update();
          });
        });
      });
      h('td', 'tdm-ten tdm-num', tr); h('td', 'tdm-use', tr);
    });
    h('p', 'tdm-note', root,
      'Each estimate is treated as a Gaussian. Starting from the most precise estimate, any estimate in tension with it by more than ' +
      '&tau;&sigma; is marginalised over (their probability distributions are summed), and the check is repeated on the result. ' +
      '&tau; = 0 sums all estimates. Same procedure as PyCS3 (Bonvin et al. 2018; Millon et al. 2020), computed live in your browser. ' +
      'Filled symbols: estimates that enter the combination. Tension: distance of each estimate from the combined value, in units of the two errors added in quadrature.');
    var slider = root.querySelector('input[type=range]');
    function update() { render(root, data, slider ? parseFloat(slider.value) : tau0); }
    var lastW = root.clientWidth;
    window.addEventListener('resize', function () {
      if (Math.abs(root.clientWidth - lastW) > 30) { lastW = root.clientWidth; update(); }
    });
    if (slider) {
      slider.addEventListener('input', update);
      root.querySelector('.tdm-reset').addEventListener('click', function () { slider.value = tau0; update(); });
    }
    update();
  }

  function init() { Array.prototype.forEach.call(document.querySelectorAll('.tdm[data-src]'), build); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
