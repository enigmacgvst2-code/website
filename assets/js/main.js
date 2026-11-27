/*
	ZeroFour by HTML5 UP
	html5up.net | @ajlkn
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
*/

(function($) {

	var	$window = $(window),
		$body = $('body');

	// Breakpoints.
		breakpoints({
			xlarge:  [ '1281px',  '1680px' ],
			large:   [ '981px',   '1280px' ],
			medium:  [ '737px',   '980px'  ],
			small:   [ null,      '736px'  ]
		});

	// Play initial animations on page load.
		$window.on('load', function() {
			window.setTimeout(function() {
				$body.removeClass('is-preload');
			}, 100);
		});

	// Dropdowns.
		$('#nav > ul').dropotron({
			offsetY: -22,
			mode: 'fade',
			noOpenerFade: true,
			speed: 300,
			detach: false
		});

	// Nav.

		// Title Bar.
			$(
				'<div id="titleBar">' +
					'<a href="#navPanel" class="toggle"></a>' +
					'<span class="title">' + $('#logo').html() + '</span>' +
				'</div>'
			)
				.appendTo($body);

		// Panel.
			$(
				'<div id="navPanel">' +
					'<nav>' +
						$('#nav').navList() +
					'</nav>' +
				'</div>'
			)
				.appendTo($body)
				.panel({
					delay: 500,
					hideOnClick: true,
					hideOnSwipe: true,
					resetScroll: true,
					resetForms: true,
					side: 'left',
					target: $body,
					visibleClass: 'navPanel-visible'
				});

})(jQuery);
// Home header: labels and credit for the VST + Rubin banner (Oct 2026).
(function () {
	var w = document.getElementById('header-wrapper-home');
	if (!w || w.querySelector('.hero-credit')) return;
	w.setAttribute('role', 'img');
	w.setAttribute('aria-label', 'VST and Vera C. Rubin Observatory');
	w.insertAdjacentHTML('beforeend',
		'<span class="hero-label" style="left:22.2%">VST<small>VLT Survey Telescope</small></span>' +
		'<span class="hero-label" style="left:67.3%">Rubin Observatory</span>' +
		'<p class="hero-credit">COOL J0542&minus;2125<span class="bands"> &middot; ' +
		'<b style="color:#c4aaff">u</b> DECam &middot; ' +
		'<b style="color:#6ebeff">g</b>, <b style="color:#ffb95a">i</b>, <b style="color:#ff786e">z</b> Legacy Surveys DR10 &middot; ' +
		'<b style="color:#82e682">r</b> VST/OmegaCAM</span><br>Image: M. Annunziatella</p>');
})();

// Christmas: snowfall + Santa hat on the logo (Nov 2026).
// Shows only 27 Nov – 6 Jan. Preview any day with ?xmas=1, hide with ?xmas=0.
// Snow is skipped when the visitor prefers reduced motion.
(function () {
	var q = location.search, d = new Date(), m = d.getMonth();
	var on = (m === 10 && d.getDate() >= 27) || m === 11 || (m === 0 && d.getDate() <= 6);
	if (/[?&]xmas=1/.test(q)) on = true;
	if (/[?&]xmas=0/.test(q)) on = false;
	if (!on || document.getElementById('xmas-style')) return;

	var css = document.createElement('style');
	css.id = 'xmas-style';
	css.textContent =
		'#logo{position:relative}' +
		'#logo .xmas-hat{position:absolute;left:30px;top:-17px;width:46px;height:40px;' +
		'transform:rotate(22deg);pointer-events:none;z-index:3;filter:drop-shadow(0 2px 2px rgba(0,0,0,.45))}' +
		'#xmas-snow{position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:9999}';
	document.head.appendChild(css);

	// Santa hat on the round logo in the header.
	var logo = document.getElementById('logo');
	if (logo && logo.querySelector('img')) {
		logo.insertAdjacentHTML('afterbegin',
			'<svg class="xmas-hat" viewBox="0 0 46 40" aria-hidden="true">' +
			'<path d="M6 30 C10 14 20 4 32 5 C38 6 42 12 41 20 C38 15 34 13 31 15 C33 20 36 25 38 30 Z" fill="#d62a2a"/>' +
			'<path d="M31 15 C34 13 38 15 41 20 L38 30 C36 25 33 20 31 15 Z" fill="#a81d1d"/>' +
			'<rect x="3" y="28" width="38" height="9" rx="4.5" fill="#f6f6f6"/>' +
			'<circle cx="41" cy="21" r="5" fill="#f6f6f6"/>' +
			'</svg>');
	}

	// Gentle snowfall.
	if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
	var cv = document.createElement('canvas');
	cv.id = 'xmas-snow';
	cv.setAttribute('aria-hidden', 'true');
	document.body.appendChild(cv);
	var ctx = cv.getContext('2d'), W, H, dpr, flakes = [], N;

	function size() {
		dpr = Math.min(window.devicePixelRatio || 1, 2);
		W = window.innerWidth; H = window.innerHeight;
		cv.width = W * dpr; cv.height = H * dpr;
		ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		N = W < 736 ? 35 : 80;
		while (flakes.length < N) flakes.push(flake(true));
		flakes.length = N;
	}
	function flake(anyY) {
		var r = 1 + Math.random() * 2.4;
		return { x: Math.random() * W, y: anyY ? Math.random() * H : -5,
			r: r, vy: 0.25 + r * 0.22, a: 0.35 + Math.random() * 0.45,
			ph: Math.random() * 6.28, sw: 0.3 + Math.random() * 0.6 };
	}
	var t = 0;
	function frame() {
		if (!document.hidden) {
			t += 0.01;
			ctx.clearRect(0, 0, W, H);
			for (var i = 0; i < flakes.length; i++) {
				var f = flakes[i];
				f.y += f.vy;
				f.x += Math.sin(t + f.ph) * f.sw * 0.5;
				if (f.y > H + 5 || f.x < -10 || f.x > W + 10) { flakes[i] = flake(false); continue; }
				ctx.beginPath();
				ctx.arc(f.x, f.y, f.r, 0, 6.2832);
				ctx.fillStyle = 'rgba(255,255,255,' + f.a + ')';
				ctx.fill();
				ctx.strokeStyle = 'rgba(120,145,200,' + (f.a * 0.6) + ')';
				ctx.lineWidth = 0.8;
				ctx.stroke();
			}
		}
		requestAnimationFrame(frame);
	}
	size();
	window.addEventListener('resize', size);
	requestAnimationFrame(frame);
})();
