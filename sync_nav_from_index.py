#!/usr/bin/env python3
"""
Sync <div class="logo">...</div>, <nav id="nav">...</nav>, and <footer>...</footer>
from index.html to all other *.html pages in a folder.
Also updates the "current_page_item" class to match each page's filename.

Usage:
  # dry-run
  python sync_nav_and_footer.py --dir /path/to/site

  # apply changes (creates .bak backups once)
  python sync_nav_and_footer.py --dir /path/to/site --write
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Tuple


LOGO_RE = re.compile(
    r'(<div\b[^>]*\bclass\s*=\s*["\']logo["\'][^>]*>)(.*?)(</div>)',
    re.IGNORECASE | re.DOTALL,
)

NAV_RE = re.compile(
    r'(<nav\b[^>]*\bid\s*=\s*["\']nav["\'][^>]*>)(.*?)(</nav>)',
    re.IGNORECASE | re.DOTALL,
)

FOOTER_RE = re.compile(
    r'(<footer\b[^>]*>)(.*?)(</footer>)',
    re.IGNORECASE | re.DOTALL,
)

LI_CLASS_RE = re.compile(
    r'(<li\b[^>]*\bclass\s*=\s*["\'])([^"\']*)(["\'][^>]*>)',
    re.IGNORECASE | re.DOTALL,
)

HREF_RE = re.compile(
    r'href\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def extract_logo(html: str) -> str:
    m = LOGO_RE.search(html)
    if not m:
        raise ValueError("Could not find <div class='logo'>...</div> block in index.html.")
    return m.group(0)  # whole logo block


def extract_nav(html: str) -> str:
    m = NAV_RE.search(html)
    if not m:
        raise ValueError("Could not find <nav id='nav'>...</nav> block in index.html.")
    return m.group(0)  # whole nav block


def extract_footer(html: str) -> str:
    m = FOOTER_RE.search(html)
    if not m:
        raise ValueError("Could not find <footer>...</footer> block in index.html.")
    return m.group(0)  # whole footer block


def replace_logo(html: str, new_logo: str) -> Tuple[str, bool]:
    m = LOGO_RE.search(html)
    if not m:
        return html, False
    old_logo = m.group(0)
    if old_logo == new_logo:
        return html, False
    return html[: m.start()] + new_logo + html[m.end() :], True


def replace_nav(html: str, new_nav: str) -> Tuple[str, bool]:
    m = NAV_RE.search(html)
    if not m:
        return html, False
    old_nav = m.group(0)
    if old_nav == new_nav:
        return html, False
    return html[: m.start()] + new_nav + html[m.end() :], True


def replace_footer(html: str, new_footer: str) -> Tuple[str, bool]:
    m = FOOTER_RE.search(html)
    if not m:
        return html, False
    old_footer = m.group(0)
    if old_footer == new_footer:
        return html, False
    return html[: m.start()] + new_footer + html[m.end() :], True


def set_current_page_item(nav_html: str, current_filename: str) -> str:
    """
    Ensures exactly one <li> has class current_page_item for the link matching current_filename.
    - Clears current_page_item everywhere
    - Adds it to the <li> that directly contains <a href="current_filename">
    """
    # 1) remove current_page_item from all li class attributes
    def _strip_current(m: re.Match) -> str:
        prefix, classes, suffix = m.group(1), m.group(2), m.group(3)
        parts = [c for c in re.split(r"\s+", classes.strip()) if c]
        parts = [c for c in parts if c != "current_page_item"]
        new_classes = " ".join(parts)
        return prefix + new_classes + suffix

    nav_clean = LI_CLASS_RE.sub(_strip_current, nav_html)

    # 2) add current_page_item to the li that contains an <a href="current_filename">
    target_re = re.compile(
        r'(<li\b(?:(?!</li>).)*?<a\b[^>]*\bhref\s*=\s*["\'](?:[^"\']*/)?'
        + re.escape(current_filename)
        + r'["\'][^>]*>)(?:(?!</li>).)*?</li>',
        re.IGNORECASE | re.DOTALL,
    )

    m = target_re.search(nav_clean)
    if not m:
        # If no match, just return nav with no "current" (safe fallback)
        return nav_clean

    li_block = m.group(0)

    # Add class="current_page_item" to the opening <li ...>
    if re.search(r"<li\b[^>]*\bclass\s*=", li_block, flags=re.IGNORECASE):
        li_block_new = re.sub(
            r'(<li\b[^>]*\bclass\s*=\s*["\'])([^"\']*)(["\'])',
            lambda mm: mm.group(1)
            + ("current_page_item " + mm.group(2)).strip()
            + mm.group(3),
            li_block,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
    else:
        li_block_new = re.sub(
            r"<li\b",
            '<li class="current_page_item"',
            li_block,
            count=1,
            flags=re.IGNORECASE,
        )

    return nav_clean[: m.start()] + li_block_new + nav_clean[m.end() :]


def sync(site_dir: Path, write: bool) -> None:
    index_path = site_dir / "index.html"
    if not index_path.exists():
        raise FileNotFoundError(f"index.html not found in {site_dir}")

    index_html = index_path.read_text(encoding="utf-8")
    logo_from_index = extract_logo(index_html)
    nav_from_index = extract_nav(index_html)
    footer_from_index = extract_footer(index_html)

    html_files = sorted(site_dir.glob("*.html"))
    if not html_files:
        print("No .html files found.")
        return

    for page in html_files:
        page_html = page.read_text(encoding="utf-8")

        # Replace logo
        updated, logo_changed = replace_logo(page_html, logo_from_index)

        # Replace nav
        updated, nav_changed = replace_nav(updated, nav_from_index)
        if not NAV_RE.search(updated):
            print(f"[SKIP] {page.name}: no <nav id='nav'> found")
            continue

        # Update the active tab highlighting
        new_nav = extract_nav(updated)
        new_nav = set_current_page_item(new_nav, page.name)
        updated, cur_changed = replace_nav(updated, new_nav)

        # Replace footer
        updated, footer_changed = replace_footer(updated, footer_from_index)

        changed = updated != page_html

        if changed:
            if write:
                bak = page.with_suffix(page.suffix + ".bak")
                if not bak.exists():
                    bak.write_text(page_html, encoding="utf-8")
                page.write_text(updated, encoding="utf-8")
                print(f"[UPDATED] {page.name} (backup: {bak.name})")
            else:
                what = []
                if logo_changed:
                    what.append("logo")
                if nav_changed:
                    what.append("nav")
                if footer_changed:
                    what.append("footer")
                if cur_changed:
                    what.append("current_page_item")
                print(f"[DRY-RUN] {page.name}: would update {', '.join(what) or 'content'}")
        else:
            print(f"[OK] {page.name}: already in sync")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".", help="Folder containing index.html and the other pages")
    ap.add_argument("--write", action="store_true", help="Apply changes (otherwise dry-run)")
    args = ap.parse_args()

    site_dir = Path(args.dir).expanduser().resolve()
    sync(site_dir, write=args.write)


if __name__ == "__main__":
    main()
