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

// Christmas: Santa hat on the logo + tiny tree on the Home banner (Nov 2026; snow removed 27 Nov).
// Shows only 27 Nov – 6 Jan. Preview any day with ?xmas=1, hide with ?xmas=0.
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
		'#header-wrapper-home .xmas-tree{position:absolute;left:43.5%;top:91%;width:1.8%;min-width:22px;' +
		'transform:translate(-50%,-100%);pointer-events:none;z-index:2;filter:drop-shadow(0 0 3px rgba(255,214,120,.35))}' +
		'#header-wrapper-home .xmas-tree svg{display:block;width:100%;height:auto}' +
		'@media (prefers-reduced-motion:no-preference){#header-wrapper-home .xmas-tree .tw{animation:xmasTw 2.4s ease-in-out infinite}' +
		'#header-wrapper-home .xmas-tree .tw2{animation-delay:-1.2s}}' +
		'@keyframes xmasTw{0%,100%{opacity:1}50%{opacity:.35}}' +
		'@media screen and (max-width:736px){#header-wrapper-home .xmas-tree{display:none}}';
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
	// Tiny tree on the rocks of the Home banner, between the VST and Rubin.
	var hero = document.getElementById('header-wrapper-home');
	if (hero) {
		hero.insertAdjacentHTML('beforeend',
			'<span class="xmas-tree" aria-hidden="true"><svg viewBox="0 0 30 46">' +
			'<rect x="13" y="38" width="4" height="7" fill="#5a3a22"/>' +
			'<path d="M15 6 L4 22 H10 L2 32 H9 L0 40 H30 L21 32 H28 L20 22 H26 Z" fill="#1f6b3a"/>' +
			'<path d="M15 6 L20 22 H26 L15 6 Z M20 22 L28 32 H21 Z M21 32 L30 40 H22 Z" fill="#17552d"/>' +
			'<circle class="tw" cx="11" cy="20" r="1.4" fill="#ff5a5a"/>' +
			'<circle class="tw tw2" cx="18" cy="27" r="1.4" fill="#ffd25a"/>' +
			'<circle class="tw" cx="9" cy="33" r="1.4" fill="#6ec3ff"/>' +
			'<circle class="tw tw2" cx="21" cy="36" r="1.4" fill="#ff5a5a"/>' +
			'<circle class="tw tw2" cx="14" cy="14" r="1.2" fill="#6ec3ff"/>' +
			'<path d="M15 0.5 L16.4 4.3 L20.3 4.3 L17.1 6.6 L18.3 10.4 L15 8.1 L11.7 10.4 L12.9 6.6 L9.7 4.3 L13.6 4.3 Z" fill="#ffd84a"/>' +
			'</svg></span>');
	}
})();
