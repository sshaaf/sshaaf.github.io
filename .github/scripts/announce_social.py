#!/usr/bin/env python3
"""
Announce newly added Hugo posts on social platforms with canonical links.

Supported channels:
- Bluesky
- Mastodon
- Discord (via webhook)

By default, on push this script announces new files added under content/post/*.md.
Use --force to include modified files.

- Per-post channel toggles: `social_bluesky`, `social_mastodon`, `social_discord`.
  (used as opt-in unless SOCIAL_ANNOUNCE_ALL is set)
- Explicit `social: false` always skips a post.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Missing PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


DEFAULT_SITE_BASE_URL = "https://shaaf.dev"
DEFAULT_CHANNELS = ("bluesky", "mastodon")
POSTS_DIR = "content/post"


@dataclass
class PostCandidate:
    rel_path: str
    title: str
    url: str
    teaser: str
    tags: list[str]
    channels: list[str]


def default_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in (here, *here.parents):
        if (p / "config.toml").is_file() or (p / "hugo.toml").is_file():
            return p
    raise RuntimeError(f"Could not find Hugo config above {here}")


def truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [x.strip() for x in raw.split(",") if x.strip()]
    elif isinstance(raw, list):
        items = [str(x).strip() for x in raw if str(x).strip()]
    else:
        items = [str(raw).strip()]
    seen: list[str] = []
    for item in items:
        if item.lower() not in {x.lower() for x in seen}:
            seen.append(item)
    return seen


def hashtagify(tags: list[str], max_count: int = 3) -> str:
    out: list[str] = []
    for tag in tags:
        cleaned = "".join(ch for ch in tag if ch.isalnum())
        if not cleaned:
            continue
        out.append(f"#{cleaned}")
        if len(out) >= max_count:
            break
    return " ".join(out)


def load_front_matter_and_body(path: Path) -> tuple[dict[str, Any], str] | None:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return None
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise RuntimeError(f"YAML error in {path}: {exc}") from exc
    body = parts[2].lstrip("\n")
    return fm, body


def first_teaser(description: str | None, body: str, limit: int = 180) -> str:
    if description:
        text = " ".join(description.split())
    else:
        text = " ".join(body.strip().split())
    if not text:
        return "New post is live on my blog."
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def hugo_permalinks(repo_root: Path) -> dict[str, tuple[str, bool]]:
    run = subprocess.run(
        ["hugo", "list", "all"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        print(run.stderr, file=sys.stderr)
        raise RuntimeError("`hugo list all` failed")
    rows = csv.DictReader(io.StringIO(run.stdout))
    out: dict[str, tuple[str, bool]] = {}
    for row in rows:
        rel = (row.get("path") or "").strip()
        permalink = (row.get("permalink") or "").strip()
        draft = (row.get("draft") or "").strip().lower() == "true"
        if rel and permalink:
            out[rel] = (permalink.rstrip("/"), draft)
    return out


def git_changed_post_files(repo_root: Path, before: str, after: str, force: bool) -> list[str]:
    if not before or not after:
        return []
    run = subprocess.run(
        ["git", "diff", "--name-status", before, after, "--", f"{POSTS_DIR}/*.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        print(run.stderr, file=sys.stderr)
        raise RuntimeError("git diff failed")
    out: list[str] = []
    for line in run.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0].strip()
        path = parts[-1].strip()
        if not path.endswith(".md"):
            continue
        include = status.startswith("A") or status.startswith("R")
        if force and (status.startswith("M") or status.startswith("C")):
            include = True
        if include:
            out.append(path)
    return sorted(set(out))


def choose_channels(fm: dict[str, Any]) -> list[str]:
    announce_all = truthy(os.environ.get("SOCIAL_ANNOUNCE_ALL"))
    fm_channels = fm.get("social_channels")
    if fm_channels is not None:
        channels = normalize_tags(fm_channels)
    else:
        if announce_all:
            raw = os.environ.get("SOCIAL_DEFAULT_CHANNELS", ",".join(DEFAULT_CHANNELS))
            channels = [x.strip() for x in raw.split(",") if x.strip()]
        else:
            channels = []

    # Per-post channel toggles. In non-global mode these act as opt-in switches.
    # In global mode they can be used to add or remove specific channels.
    channel_flags = {
        "bluesky": fm.get("social_bluesky"),
        "mastodon": fm.get("social_mastodon"),
        "discord": fm.get("social_discord"),
    }
    for channel, flag in channel_flags.items():
        if flag is True and channel not in channels:
            channels.append(channel)
        elif flag is False and channel in channels:
            channels.remove(channel)

    valid = {"bluesky", "mastodon", "discord"}
    return [x.lower() for x in channels if x.lower() in valid]


def should_announce(fm: dict[str, Any]) -> bool:
    if fm.get("social") is False:
        return False
    if truthy(os.environ.get("SOCIAL_ANNOUNCE_ALL")):
        return True
    if fm.get("social_channels") is not None:
        return True
    return any(
        fm.get(key) is True
        for key in ("social_bluesky", "social_mastodon", "social_discord")
    )


def build_post_candidates(
    repo_root: Path,
    rel_files: list[str],
    base_url: str,
) -> list[PostCandidate]:
    permalink_map = hugo_permalinks(repo_root)
    candidates: list[PostCandidate] = []
    for rel in rel_files:
        path = repo_root / rel
        if not path.exists():
            continue
        loaded = load_front_matter_and_body(path)
        if not loaded:
            print(f"skip (missing YAML front matter): {rel}", file=sys.stderr)
            continue
        fm, body = loaded
        if not should_announce(fm):
            print(f"skip (social: false): {rel}", file=sys.stderr)
            continue
        if rel not in permalink_map:
            print(f"skip (not in hugo list): {rel}", file=sys.stderr)
            continue
        permalink, is_draft = permalink_map[rel]
        if is_draft:
            print(f"skip (draft): {rel}", file=sys.stderr)
            continue
        title = str(fm.get("title") or "").strip()
        if not title:
            print(f"skip (missing title): {rel}", file=sys.stderr)
            continue
        teaser = str(fm.get("social_text") or "").strip()
        if not teaser:
            teaser = first_teaser(str(fm.get("description") or "").strip(), body)
        tags = normalize_tags(fm.get("social_tags") or fm.get("tags"))
        url = permalink if permalink.startswith("http") else base_url.rstrip("/") + permalink
        channels = choose_channels(fm)
        if not channels:
            print(f"skip (no channels configured): {rel}", file=sys.stderr)
            continue
        candidates.append(
            PostCandidate(
                rel_path=rel,
                title=title,
                url=url,
                teaser=teaser,
                tags=tags,
                channels=channels,
            )
        )
    return candidates


def trim_message(message: str, limit: int) -> str:
    if len(message) <= limit:
        return message
    return message[: limit - 1].rstrip() + "…"


def build_message(post: PostCandidate, channel: str) -> str:
    hashtags = hashtagify(post.tags)
    parts = [f"New post: {post.title}", post.teaser, f"Read: {post.url}"]
    if hashtags:
        parts.append(hashtags)
    joined = "\n\n".join(parts)
    limits = {"bluesky": 300, "mastodon": 500, "discord": 1900}
    return trim_message(joined, limits.get(channel, 500))


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, Any]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=headers or {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else None
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {body}") from exc


def http_form(
    method: str,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, str]:
    encoded = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        method=method,
        headers=headers or {},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {body}") from exc


def wait_until_live(url: str, timeout_seconds: int, sleep_seconds: int = 20) -> bool:
    start = time.time()
    while time.time() - start <= timeout_seconds:
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=15) as resp:
                if 200 <= resp.status < 400:
                    return True
        except Exception:
            pass
        time.sleep(sleep_seconds)
    return False


def byte_index(text: str, char_index: int) -> int:
    return len(text[:char_index].encode("utf-8"))


def url_facet(text: str, url: str) -> dict[str, Any] | None:
    pos = text.find(url)
    if pos < 0:
        return None
    return {
        "index": {
            "byteStart": byte_index(text, pos),
            "byteEnd": byte_index(text, pos + len(url)),
        },
        "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
    }


def post_bluesky(message: str, canonical_url: str) -> None:
    identifier = os.environ.get("BLUESKY_IDENTIFIER", "").strip()
    app_password = os.environ.get("BLUESKY_APP_PASSWORD", "").strip()
    pds = os.environ.get("BLUESKY_PDS_URL", "https://bsky.social").rstrip("/")
    if not identifier or not app_password:
        raise RuntimeError("Missing BLUESKY_IDENTIFIER or BLUESKY_APP_PASSWORD")

    _, session = http_json(
        "POST",
        f"{pds}/xrpc/com.atproto.server.createSession",
        payload={"identifier": identifier, "password": app_password},
        headers={"Content-Type": "application/json"},
    )
    access_jwt = session.get("accessJwt")
    did = session.get("did")
    if not access_jwt or not did:
        raise RuntimeError("Bluesky session response missing accessJwt or did")

    facet = url_facet(message, canonical_url)
    record: dict[str, Any] = {
        "$type": "app.bsky.feed.post",
        "text": message,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if facet:
        record["facets"] = [facet]

    http_json(
        "POST",
        f"{pds}/xrpc/com.atproto.repo.createRecord",
        payload={
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": record,
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_jwt}",
        },
    )


def post_mastodon(message: str) -> None:
    base = os.environ.get("MASTODON_BASE_URL", "").strip().rstrip("/")
    token = os.environ.get("MASTODON_ACCESS_TOKEN", "").strip()
    if not base or not token:
        raise RuntimeError("Missing MASTODON_BASE_URL or MASTODON_ACCESS_TOKEN")
    http_form(
        "POST",
        f"{base}/api/v1/statuses",
        payload={"status": message, "visibility": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )


def post_discord(message: str) -> None:
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL")
    http_json(
        "POST",
        webhook,
        payload={"content": message},
        headers={"Content-Type": "application/json"},
    )


def dispatch_post(post: PostCandidate, dry_run: bool) -> None:
    for channel in post.channels:
        message = build_message(post, channel)
        if dry_run:
            print(f"[dry-run] {channel}: {post.rel_path}\n{message}\n")
            continue
        if channel == "bluesky":
            post_bluesky(message, post.url)
        elif channel == "mastodon":
            post_mastodon(message)
        elif channel == "discord":
            post_discord(message)
        else:
            raise RuntimeError(f"Unsupported channel: {channel}")
        print(f"ok: {channel} <- {post.rel_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Announce Hugo posts to social platforms with canonical links"
    )
    parser.add_argument("--repo-root", type=Path, default=default_repo_root())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--post",
        action="append",
        default=[],
        help="Specific content/post file(s) to announce, relative to repo root",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Include modified files (not just newly added) during push diff mode",
    )
    parser.add_argument(
        "--wait-for-live",
        action="store_true",
        help="Wait for each canonical URL to return 2xx/3xx before posting",
    )
    parser.add_argument(
        "--wait-timeout-seconds",
        type=int,
        default=600,
        help="Timeout while waiting for canonical URL to be live",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root
    dry_run = args.dry_run or truthy(os.environ.get("DRY_RUN"))
    base_url = os.environ.get("SITE_BASE_URL", DEFAULT_SITE_BASE_URL).rstrip("/")

    rel_files: list[str] = []
    if args.post:
        rel_files = sorted(set(args.post))
    else:
        event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
        before = os.environ.get("GITHUB_EVENT_BEFORE", "").strip()
        after = os.environ.get("GITHUB_SHA", "").strip()
        if event_name != "push":
            print("No --post files provided and event is not push; nothing to do.")
            return 0
        rel_files = git_changed_post_files(repo_root, before, after, force=args.force)

    if not rel_files:
        print("No candidate posts to announce.")
        return 0

    posts = build_post_candidates(repo_root, rel_files, base_url=base_url)
    if not posts:
        print("No eligible posts to announce after filtering.")
        print(
            "Tip: set social_bluesky/social_mastodon/social_discord: true (or set SOCIAL_ANNOUNCE_ALL=1)."
        )
        return 0

    for post in posts:
        if args.wait_for_live:
            print(f"Waiting for canonical URL to be live: {post.url}")
            is_live = wait_until_live(post.url, timeout_seconds=args.wait_timeout_seconds)
            if not is_live:
                raise RuntimeError(f"Timed out waiting for URL to go live: {post.url}")
        dispatch_post(post, dry_run=dry_run)

    print(f"Done. Announced {len(posts)} post(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
