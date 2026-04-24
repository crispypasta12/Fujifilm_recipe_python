#!/usr/bin/env python3
"""
scrape_recipes.py — scrape X-Trans V film simulation recipes from fujixweekly.com

Saves one JSON file per recipe to recipes/builtin/
Downloads one sample image per recipe to recipes/builtin/images/

Usage:
    pip install requests beautifulsoup4
    python scrape_recipes.py [--dry-run] [--limit N]

Options:
    --dry-run   Print discovered URLs without fetching/saving anything
    --limit N   Only scrape the first N recipes (useful for testing)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INDEX_URL = "https://fujixweekly.com/fujifilm-x-trans-v-recipes/"
OUTPUT_DIR = Path("recipes/builtin/x-trans-v")
IMAGE_DIR = OUTPUT_DIR / "images"
REQUEST_DELAY = 1.5   # seconds between requests — be polite

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Map text key variants → canonical JSON key
PARAM_MAP: dict[str, str] = {
    "film simulation":        "filmSimulation",
    "dynamic range":          "dynamicRange",
    "d-range priority":       "dRangePriority",
    "d range priority":       "dRangePriority",
    "grain effect":           "grainEffect",
    "grain roughness":        "grainRoughness",
    "color chrome effect":    "colorChrome",
    "color chrome fx blue":   "colorChromeFxBlue",
    "white balance":          "whiteBalance",
    "highlight":              "highlight",
    "shadow":                 "shadow",
    "color":                  "color",
    "sharpness":              "sharpness",
    "high iso nr":            "noiseReduction",
    "noise reduction":        "noiseReduction",
    "clarity":                "clarity",
    "iso":                    "iso",
    "exposure compensation":  "exposureCompensation",
    "smooth skin effect":     "smoothSkin",
    "smooth skin":            "smoothSkin",
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def get_soup(url: str, session: requests.Session) -> BeautifulSoup:
    resp = session.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser")


def download_image(url: str, dest: Path, session: requests.Session) -> bool:
    """Download image bytes to *dest*. Returns True on success."""
    if not url:
        return False
    try:
        resp = session.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except Exception as exc:
        print(f"    [!]  Image download failed ({exc})")
        return False


# ---------------------------------------------------------------------------
# Index page scraping
# ---------------------------------------------------------------------------

# Matches individual recipe pages:
#   /2024/03/27/some-slug/             — dated path (most recipes)
#   /1971-kodak-a-fujifilm-recipe-for-x-trans-v-cameras/  — undated, newer format
# Explicitly excludes category index pages like /fujifilm-x-trans-v-recipes/
_RECIPE_PATH_RE = re.compile(
    r"^https://fujixweekly\.com/"
    r"(?:"
    r"\d{4}/\d{2}/\d{2}/[^/?#]+"          # dated path
    r"|"
    r"[^/?#]+-fujifilm-recipe-for-[^/?#]*" # undated "X-fujifilm-recipe-for-Y" format
    r")/?$"
)


def get_recipe_urls(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Return [(recipe_url, thumbnail_url), …] from the index page."""
    seen: set[str] = set()
    results: list[tuple[str, str]] = []

    for a in soup.find_all("a", href=True):
        href: str = a["href"].rstrip("/") + "/"
        if href in seen:
            continue
        if not _RECIPE_PATH_RE.match(href):
            continue

        # Best thumbnail: the <img> immediately before this <a> in the DOM
        thumb = ""
        prev = a.find_previous_sibling()
        if isinstance(prev, Tag) and prev.name == "img":
            src = prev.get("src", "")
            thumb = src.split("?")[0]   # drop resize query params
        else:
            # Also check inside any wrapper: look for a child/sibling img
            for img in a.find_all_previous("img", limit=3):
                src = img.get("src", "")
                if "wp-content/uploads" in src or "i0.wp.com" in src:
                    thumb = src.split("?")[0]
                    break

        seen.add(href)
        results.append((href, thumb))

    return results


# ---------------------------------------------------------------------------
# Recipe page scraping
# ---------------------------------------------------------------------------

def get_article_content(soup: BeautifulSoup) -> Tag | None:
    """Return the main article content div."""
    return (
        soup.find("div", class_="entry-content")
        or soup.find("div", class_="post-content")
        or soup.find("article")
    )


def parse_params(soup: BeautifulSoup) -> dict[str, str]:
    """
    Extract recipe parameters from the article body.

    The site formats parameters like:
        <strong>Film Simulation: Provia/Standard</strong><br/>
        <strong>White Balance: Auto, +1 Red & -2 Blue<br/>
        Highlight: -1<br/>
        Shadow: -2</strong>

    We get all text from the article, split on newlines, then parse
    lines matching  "Key: Value".
    """
    content = get_article_content(soup)
    if content is None:
        content = soup

    params: dict[str, str] = {}

    for p in content.find_all("p"):
        # get_text with newline separator handles <br/> correctly in bs4
        raw = p.get_text(separator="\n")
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

        for line in lines:
            # "Key: Value" or "Key:Value"
            m = re.match(r"^([A-Za-z][A-Za-z0-9 \-/()]+?):\s*(.+)$", line)
            if not m:
                continue
            key_raw = m.group(1).strip().lower()
            value = m.group(2).strip()

            canonical = PARAM_MAP.get(key_raw)
            if canonical and canonical not in params:
                params[canonical] = value

    return params


def get_first_article_image(soup: BeautifulSoup) -> str:
    """
    Return the URL of the first suitable sample photo in the article body.
    Strips WordPress resize query params so we get the original quality.
    """
    content = get_article_content(soup)
    if content is None:
        return ""

    for img in content.find_all("img"):
        src: str = img.get("src", "")
        if not src:
            continue
        # Must be a real upload, not a UI sprite / icon
        if "wp-content/uploads" in src or "i0.wp.com" in src:
            return src.split("?")[0]

    return ""


def get_title(soup: BeautifulSoup) -> str:
    """Best-effort page title extraction."""
    for selector in (
        ("h1", {"class": re.compile(r"entry-title|post-title")}),
        ("h2", {"class": re.compile(r"entry-title|post-title")}),
        ("h1", {}),
        ("h2", {}),
    ):
        tag, attrs = selector
        el = soup.find(tag, attrs) if attrs else soup.find(tag)
        if el:
            return el.get_text(strip=True)
    return ""


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def slug_from_url(url: str) -> str:
    """Derive a filesystem-safe slug from the recipe URL."""
    path = urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1]
    # Trim the camera/sensor suffix the site appends
    slug = re.sub(r"-fujifilm-.*", "", slug)
    slug = re.sub(r"-film-simulation.*", "", slug)
    # Sanitise
    slug = re.sub(r"[^a-z0-9\-]", "-", slug.lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:80]


def image_filename(slug: str, image_url: str) -> str:
    ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
    return f"{slug}{ext}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape X-Trans V recipes from fujixweekly.com")
    parser.add_argument("--dry-run", action="store_true", help="List URLs only, don't save")
    parser.add_argument("--limit", type=int, default=0, help="Max recipes to scrape (0 = all)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()

    # ---- Step 1: collect recipe URLs from index ----
    print(f"[*] Fetching index: {INDEX_URL}")
    index_soup = get_soup(INDEX_URL, session)
    all_urls = get_recipe_urls(index_soup)

    if args.limit:
        all_urls = all_urls[: args.limit]

    print(f"   Found {len(all_urls)} recipe links\n")

    if args.dry_run:
        for url, thumb in all_urls:
            print(f"  {url}")
            if thumb:
                print(f"    thumb: {thumb}")
        return

    # ---- Step 2: scrape each recipe ----
    saved_slugs: list[str] = []
    skipped = 0
    errors = 0

    for i, (url, thumb_url) in enumerate(all_urls, 1):
        slug = slug_from_url(url)
        out_path = OUTPUT_DIR / f"{slug}.json"

        if out_path.exists():
            print(f"[{i:>3}/{len(all_urls)}] [skip]  {slug}  (already scraped)")
            saved_slugs.append(slug)
            skipped += 1
            continue

        print(f"[{i:>3}/{len(all_urls)}] [>] {url}")

        try:
            time.sleep(REQUEST_DELAY)
            soup = get_soup(url, session)

            title = get_title(soup)
            params = parse_params(soup)
            img_url = get_first_article_image(soup) or thumb_url

            # Download image
            img_file = ""
            if img_url:
                img_file = image_filename(slug, img_url)
                img_dest = IMAGE_DIR / img_file
                if img_dest.exists():
                    print(f"    [img]  Image already on disk: {img_file}")
                elif download_image(img_url, img_dest, session):
                    print(f"    [img]  Downloaded: {img_file}")
                else:
                    img_file = ""

            recipe = {
                "slug": slug,
                "title": title,
                "source": url,
                "image": img_file,
                "params": params,
            }

            n_params = len(params)
            if n_params < 5:
                # Not a recipe page — article/roundup/tips post, skip it
                print(f"    [!]  Only {n_params} params — looks like a non-recipe page, skipping")
                errors += 1
                continue

            out_path.write_text(
                json.dumps(recipe, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"    [OK] Saved {slug}.json  ({n_params} params parsed)")
            saved_slugs.append(slug)

        except Exception as exc:
            print(f"    [ERR] ERROR: {exc}")
            errors += 1

    # ---- Step 3: write index ----
    index_file = OUTPUT_DIR / "_index.json"
    index_file.write_text(json.dumps(saved_slugs, indent=2), encoding="utf-8")

    print("\n" + "-" * 60)
    print(f"  Total recipes : {len(all_urls)}")
    print(f"  Saved         : {len(saved_slugs) - skipped}")
    print(f"  Skipped (dup) : {skipped}")
    print(f"  Errors        : {errors}")
    print(f"  Output dir    : {OUTPUT_DIR.resolve()}")
    print("-" * 60)


if __name__ == "__main__":
    main()
