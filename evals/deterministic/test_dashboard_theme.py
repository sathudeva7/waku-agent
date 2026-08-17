"""DETERMINISTIC EVAL — the dashboard theme switch stays switchable.

The sidebar's theme button writes data-theme="light"|"dark" on <html>; with no
attribute the OS decides. Two things silently break that, and neither shows up
as an error in the browser:
  1. a page rule carries its OWN prefers-color-scheme block, so it keeps
     following the OS while the rest of the page obeys the button;
  2. the dark palette is duplicated on purpose (one media-query copy, one
     forced-theme copy) and someone edits a colour in only one of them.
"""

from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[2] / "waku" / "ops" / "static"
CSS = (STATIC / "style.css").read_text()
INDEX = (STATIC / "index.html").read_text()
MAIN_JS = (STATIC / "js" / "main.js").read_text()


def _vars(block: str) -> dict[str, str]:
    return dict(re.findall(r'(--[\w-]+)\s*:\s*([^;}]+)', block))


def _block_after(marker: str) -> str:
    """The declarations between `marker` and the first closing brace after it."""
    start = CSS.index(marker) + len(marker)
    return CSS[start:CSS.index("}", start)]


def test_only_the_palette_watches_the_os():
    """Every prefers-color-scheme rule must be scoped so an explicit choice wins.
    A bare `@media (prefers-color-scheme:dark){.foo{...}}` anywhere else ignores
    the button — put the colour in a token in the palette instead."""
    blocks = re.findall(r'@media\s*\(prefers-color-scheme:[^)]+\)\s*\{\s*([^\s{]+)', CSS)
    assert blocks == [':root:not([data-theme="light"])'], (
        f"prefers-color-scheme must only scope the palette, found: {blocks}"
    )


def test_the_two_dark_palettes_agree():
    """The media-query copy and the forced-dark copy are the same colours."""
    from_os = _vars(_block_after(':root:not([data-theme="light"]){'))
    forced = _vars(_block_after(':root[data-theme="dark"]{'))
    assert from_os, "no dark palette found under the media query"
    assert from_os == forced, "the OS-dark and forced-dark palettes drifted apart"


def test_light_pins_its_own_color_scheme():
    """Without this, forcing light on a dark OS leaves native scrollbars dark."""
    assert ':root[data-theme="light"]{color-scheme:light}' in CSS


def test_theme_is_restored_before_the_body_paints():
    """The restore is inline in <head> on purpose: main.js loads last, so doing
    it there flashes the OS theme first."""
    head = INDEX[: INDEX.index("<body")]
    assert 'localStorage.getItem("waku_theme")' in head
    assert 'setAttribute("data-theme"' in head
    assert 'id="theme-toggle"' in INDEX
    assert "function wireTheme()" in MAIN_JS
