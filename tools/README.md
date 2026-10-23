# Website tools

Small scripts that (re)generate parts of the site. Run them from the website folder, e.g.
`python3 tools/build_td.py`. All of them only touch the part of each page they own, keep the
logo / menu / footer, preserve line endings, and are safe to re-run (a second run changes nothing).

| Script | What it does |
|---|---|
| `build_td.py` | Builds the time-delay pages `<target>_td.html`: summary (cutout + combined delays), tabbed plots, solution switch. **Delay values and plot file names live in the `T = {...}` table at the top.** `python3 tools/build_td.py` (all) or `python3 tools/build_td.py J0335-1927`. |
| `build_agn.py` | Builds the AGN pages `<target>_agn.html` (filter/sort toolbar, cards, expanded view). Reads the light curves from the page itself, either the old Vue format (`allDatasets: [...]`, e.g. a newly uploaded page) or the new `<script id="agn-data">` block. `python3 tools/build_agn.py` (all) or with target names. |
| `data_table.py` | Rebuilds the *Target Coordinates* table on `data.html` (precise RA/Dec + period badges). Coordinates are in `COORDS`; periods come from `data.json`. Use `python3 tools/data_table.py . ../VST_P3_P4` to update the internal and the public site together. |
| `coming_soon.py` | Creates a "Time delay not available yet" / "AGN light curves not available yet" page so a menu link never breaks: `python3 tools/coming_soon.py td J2107-1611`, `python3 tools/coming_soon.py agn J1330+1810`. Refuses to overwrite a real page. |
| `add_head_meta.py` | Adds the browser-tab icon (`images/favicon-32.png`, `images/apple-touch-icon.png`, made from `images/logo.png`) and a page description to every page's `<head>`. `python3 tools/add_head_meta.py . ../VST_P3_P4` for both sites. Run it after adding new pages. |
| `ancillary_extra.py` | Builds all data cards of the Ancillary pages `<target>_anc.html` from tables, so every instrument card (KCWI, MUSE, DEIMOS, FORS2, HST, ERIS, JWST) looks the same on every page: per program a title + Public/Proprietary badge, note, PID / PI / instrument or mode / filters / date / exposure, archive buttons and an optional image. Data in `CARDS`, programs older than 10 yr in `ARCHIVE` (one compact table card), survey bands in `BANDS`, card order (colour along the spectrum, greys last) in `WAVE`. Only the Discovery Paper card is left as written. `python3 tools/ancillary_extra.py . ../VST_P3_P4` for both sites. |

Also in the repo root: `sync_nav_from_index.py` copies the logo, menu and footer from `index.html`
to the other pages (run it after changing the menu). Note: run it on specific pages rather than the
whole folder if you want to keep `index.html`'s Windows line endings unchanged.

## Typical updates

- **New / updated delays for a target:** edit its entry in `T` in `build_td.py` (values from the black
  "combined τ = 0.50" row of the marginalisation plot; asymmetric errors as `'26.0/24.3'`), put the plots in
  `images/<target>_VST/`, run `python3 tools/build_td.py <target>`.
- **New AGN light curves:** upload/replace the `<target>_agn.html` page (old format is fine), then run
  `python3 tools/build_agn.py <target>`.
- **New target:** add it to the menu in `index.html` and run `sync_nav_from_index.py`; add its coordinates to
  `COORDS` in `data_table.py`; create placeholders with `coming_soon.py`; run `add_head_meta.py`.

## Monitoring periods

P3 = nights up to 30 Sep 2025, P4 = 1 Oct 2025 – 30 Sep 2026, P5 = from 1 Oct 2026 (used by `data_table.py`).
