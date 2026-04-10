#!/usr/bin/env python3
"""
Sync selected Hugo posts (content/post) to dev.to via the Forem API.

- Uses `hugo list all` for canonical permalinks (must match published site).
- Opt-in per post: front matter `devto: true`, unless DEVTO_SYNC_ALL is set.
- Skips Hugo drafts and posts with `devto: false`.
- Matches existing dev.to articles by canonical_url (published + unpublished lists).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Missing PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

DEVTO_API = "https://dev.to/api"
ACCEPT = "application/vnd.forem.api-v1+json"
USER_AGENT = os.environ.get(
    "DEVTO_USER_AGENT",
    "sshaaf.github.io-devto-sync (+https://github.com/sshaaf/sshaaf.github.io)",
)


def default_repo_root() -> Path:
    """Resolve repo root (directory containing Hugo config) from this script location."""
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "config.toml").is_file() or (p / "hugo.toml").is_file():
            return p
    raise RuntimeError(
        f"Could not find config.toml or hugo.toml above {here}; pass --repo-root explicitly."
    )


def truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.strip().lower() in ("1", "true", "yes", "on")


def normalize_canonical(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    return u.rstrip("/")


def load_front_matter_and_body(path: Path) -> tuple[dict[str, Any], str] | None:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return None
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        print(f"YAML error in {path}: {e}", file=sys.stderr)
        return None
    body = parts[2]
    if body.startswith("\n"):
        body = body[1:]
    return fm, body


def hugo_permalinks(repo_root: Path) -> dict[str, tuple[str, bool]]:
    """path -> (permalink, is_draft) from `hugo list all` CSV."""
    r = subprocess.run(
        ["hugo", "list", "all"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise RuntimeError("`hugo list all` failed")
    reader = csv.DictReader(io.StringIO(r.stdout))
    out: dict[str, tuple[str, bool]] = {}
    for row in reader:
        p = row.get("path") or ""
        link = (row.get("permalink") or "").strip()
        draft = (row.get("draft") or "").strip().lower() == "true"
        if p and link:
            out[p] = (link, draft)
    return out


def normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [t.strip() for t in raw.split(",") if t.strip()]
    elif isinstance(raw, list):
        items = [str(t).strip() for t in raw if str(t).strip()]
    else:
        items = [str(raw).strip()]
    # dev.to allows max 4 tags
    seen: list[str] = []
    for t in items:
        if t.lower() not in {x.lower() for x in seen}:
            seen.append(t)
        if len(seen) >= 4:
            break
    return seen


def abs_site_url(base: str, ref: str) -> str:
    """Turn a root-relative or relative path into an absolute URL on the published site."""
    s = ref.strip()
    if not s:
        return s
    if s.startswith(("http://", "https://")):
        return s
    if s.startswith("//"):
        return "https:" + s
    if s.startswith("/"):
        return base.rstrip("/") + s
    return base.rstrip("/") + "/" + s.lstrip("/")


def abs_image_url(base: str, image: Any) -> str | None:
    if not image or not isinstance(image, str):
        return None
    s = abs_site_url(base, image)
    return s if s else None


def rewrite_markdown_root_relative_urls(body: str, base: str) -> str:
    """
    dev.to renders markdown on dev.to; paths like /images/... resolve there and 404.
    Rewrite root-relative URLs in prose (outside fenced code blocks) to absolute SITE_BASE_URL.
    """
    base = base.rstrip("/")

    def rewrite_segment(segment: str) -> str:
        s = segment

        # Markdown links and images: [text](/path) or ![alt](/path)
        def md_paren(m: re.Match[str]) -> str:
            prefix, path, suffix = m.group(1), m.group(2), m.group(3)
            if path.startswith("/") and not path.startswith("//"):
                path = abs_site_url(base, path)
            return prefix + path + suffix

        s = re.sub(r"(\]\()(/[^)\s]+)(\))", md_paren, s)

        # HTML: src="/..." or src='/...'
        def html_attr(m: re.Match[str]) -> str:
            prefix, path, suffix = m.group(1), m.group(2), m.group(3)
            if path.startswith("/") and not path.startswith("//"):
                path = abs_site_url(base, path)
            return prefix + path + suffix

        s = re.sub(r'(\ssrc\s*=\s*["\'])(/[^"\']+)(["\'])', html_attr, s)
        s = re.sub(r'(\shref\s*=\s*["\'])(/[^"\']+)(["\'])', html_attr, s)

        return s

    # Do not rewrite inside ``` fenced blocks (may contain literal ]( /path) examples)
    parts = re.split(r"(```[\s\S]*?```)", body)
    out: list[str] = []
    for part in parts:
        # Fenced blocks from split are left as-is (may contain literal URLs)
        if part.startswith("```"):
            out.append(part)
        else:
            out.append(rewrite_segment(part))
    return "".join(out)


def should_sync(fm: dict[str, Any]) -> bool:
    if fm.get("devto") is False:
        return False
    if truthy(os.environ.get("DEVTO_SYNC_ALL")):
        return True
    return fm.get("devto") is True


def api_headers(api_key: str, *, json_body: bool = False) -> dict[str, str]:
    h: dict[str, str] = {
        "api-key": api_key,
        "Accept": ACCEPT,
        "User-Agent": USER_AGENT,
    }
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def http_json(
    method: str,
    url: str,
    api_key: str,
    payload: dict | None = None,
    retries: int = 5,
) -> tuple[int, Any]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=api_headers(api_key, json_body=payload is not None),
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return resp.status, None
                return resp.status, json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = (2**attempt) + random.random()
                print(f"  rate limited, sleeping {wait:.1f}s …", file=sys.stderr)
                time.sleep(wait)
                continue
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(err_body)
            except json.JSONDecodeError:
                parsed = err_body
            raise RuntimeError(f"HTTP {e.code} {method} {url}: {parsed}") from e
    raise RuntimeError("unreachable")


def fetch_all_my_articles(api_key: str, status: str) -> list[dict[str, Any]]:
    """status: published | unpublished"""
    all_rows: list[dict[str, Any]] = []
    page = 1
    while True:
        url = f"{DEVTO_API}/articles/me/{status}?page={page}&per_page=1000"
        status_code, data = http_json("GET", url, api_key)
        if status_code != 200:
            raise RuntimeError(f"Unexpected {status_code} for {url}")
        if not isinstance(data, list) or len(data) == 0:
            break
        all_rows.extend(data)
        if len(data) < 1000:
            break
        page += 1
    return all_rows


def canonical_to_id_map(api_key: str) -> dict[str, int]:
    by_url: dict[str, int] = {}
    for status in ("published", "unpublished"):
        for art in fetch_all_my_articles(api_key, status):
            cid = art.get("canonical_url") or ""
            aid = art.get("id")
            if cid and aid is not None:
                by_url[normalize_canonical(str(cid))] = int(aid)
    return by_url


def build_article_payload(
    title: str,
    body_md: str,
    canonical: str,
    tags: list[str],
    description: str | None,
    main_image: str | None,
) -> dict[str, Any]:
    article: dict[str, Any] = {
        "title": title,
        "body_markdown": body_md,
        "published": True,
        "canonical_url": canonical,
    }
    if tags:
        article["tags"] = tags
    if description:
        article["description"] = description[:300]
    if main_image:
        article["main_image"] = main_image
    return {"article": article}


def first_description_snippet(body: str, limit: int = 200) -> str | None:
    text = body.strip()
    if not text:
        return None
    line = text.split("\n\n", 1)[0].strip()
    line = " ".join(line.split())
    if len(line) > limit:
        return line[: limit - 1] + "…"
    return line


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Hugo content/post to dev.to")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="Repository root (contains config.toml and content/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only; do not call write APIs",
    )
    args = parser.parse_args()
    repo_root: Path = args.repo_root

    dry_run = args.dry_run or truthy(os.environ.get("DRY_RUN"))
    api_key = os.environ.get("DEVTO_API_KEY", "").strip()
    if not api_key and not dry_run:
        print("DEVTO_API_KEY is required (or use --dry-run / DRY_RUN=1)", file=sys.stderr)
        return 1

    base_url = os.environ.get("SITE_BASE_URL", "https://shaaf.dev").rstrip("/")

    permalinks = hugo_permalinks(repo_root)

    post_dir = repo_root / "content" / "post"
    if not post_dir.is_dir():
        print(f"No directory {post_dir}", file=sys.stderr)
        return 1

    md_files = sorted(post_dir.glob("*.md"))
    to_process: list[tuple[str, str, str, str, list[str], str | None, str | None]] = []

    for path in md_files:
        rel = str(path.relative_to(repo_root)).replace(os.sep, "/")
        loaded = load_front_matter_and_body(path)
        if not loaded:
            continue
        fm, body = loaded
        if not should_sync(fm):
            continue
        if rel not in permalinks:
            print(f"skip (not in hugo list): {rel}", file=sys.stderr)
            continue
        permalink, hugo_draft = permalinks[rel]
        if hugo_draft:
            print(f"skip (Hugo draft): {rel}", file=sys.stderr)
            continue

        title = fm.get("title")
        if not title:
            print(f"skip (no title): {rel}", file=sys.stderr)
            continue
        title = str(title).strip()

        canonical = normalize_canonical(permalink)
        tags = normalize_tags(fm.get("tags"))
        desc = fm.get("description")
        if desc:
            desc = str(desc).strip()[:300]
        else:
            desc = first_description_snippet(body)
        main_image = abs_image_url(base_url, fm.get("image"))
        body_for_devto = rewrite_markdown_root_relative_urls(body, base_url)

        to_process.append(
            (rel, title, body_for_devto, canonical, tags, desc, main_image)
        )

    if not to_process:
        print("No posts to sync. Add devto: true to front matter (or set DEVTO_SYNC_ALL=1).")
        return 0

    url_map: dict[str, int] = {}
    if not dry_run:
        print("Fetching existing dev.to articles (by canonical_url)…", file=sys.stderr)
        url_map = canonical_to_id_map(api_key)

    ok = 0
    for rel, title, body, canonical, tags, desc, main_image in to_process:
        payload = build_article_payload(title, body, canonical, tags, desc, main_image)
        key = normalize_canonical(canonical)
        existing_id = url_map.get(key)

        if dry_run:
            action = f"UPDATE id={existing_id}" if existing_id else "CREATE"
            print(f"[dry-run] {action}  {rel}\n  canonical: {canonical}\n  title: {title}")
            ok += 1
            continue

        time.sleep(1.2)  # gentle rate limit
        if existing_id:
            print(f"PUT  {rel}  -> dev.to article {existing_id}", file=sys.stderr)
            http_json("PUT", f"{DEVTO_API}/articles/{existing_id}", api_key, payload)
        else:
            print(f"POST {rel}  -> new dev.to article", file=sys.stderr)
            status, created = http_json("POST", f"{DEVTO_API}/articles", api_key, payload)
            if status not in (200, 201) or not isinstance(created, dict):
                print(f"Unexpected response for {rel}: {status} {created}", file=sys.stderr)
                return 1
            new_id = created.get("id")
            if new_id is not None:
                url_map[key] = int(new_id)
        print(f"ok: {rel}")
        ok += 1

    print(f"Done. Synced {ok} post(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
