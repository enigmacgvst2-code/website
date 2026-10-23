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
