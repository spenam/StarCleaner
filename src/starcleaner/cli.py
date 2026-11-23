"""Command-line interface for StarCleaner."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .core import CACHE_FILE, build_scan, load_scan, save_scan
from .github import GitHubAPIError, GitHubClient
from .report import render_markdown, render_text


def _token(cli_token: str | None) -> str | None:
    return cli_token or os.environ.get("STARCLEANER_TOKEN") or os.environ.get("GITHUB_TOKEN")


def _client(cli_token: str | None) -> GitHubClient:
    token = _token(cli_token)
    if not token:
        raise ValueError(
            "Missing GitHub token. Set STARCLEANER_TOKEN (recommended) or pass --token.\n"
            "Use Starring: read to scan; use Starring: write plus Metadata: read to unstar."
        )
    return GitHubClient(token)


def _cache_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--cache-file",
        type=Path,
        default=CACHE_FILE,
        help=f"Local scan file (default: {CACHE_FILE})",
    )


def _scan(client: GitHubClient, stale_days: int, cache_file: Path) -> dict[str, Any]:
    raw = client.list_starred_repositories()
    scan = build_scan(raw, stale_days)
    save_scan(scan, cache_file)
    return scan


def command_scan(args: argparse.Namespace) -> int:
    client = _client(args.token)
    scan = _scan(client, args.stale_days, args.cache_file)
    print(render_text(scan))
    print(f"  Saved local scan to: {args.cache_file}\n")
    return 0


def command_report(args: argparse.Namespace) -> int:
    scan = load_scan(args.cache_file)
    if args.format == "json":
        print(json.dumps(scan, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(scan))
    else:
        print(render_text(scan))
    return 0


def command_clean(args: argparse.Namespace) -> int:
    client = _client(args.token)
    try:
        previous = load_scan(args.cache_file)
        stale_days = args.stale_days if args.stale_days is not None else previous.get("stale_days", 365)
    except FileNotFoundError:
        stale_days = args.stale_days if args.stale_days is not None else 365

    # Refresh first so cleanup decisions are based on current GitHub data.
    scan = _scan(client, stale_days, args.cache_file)
    candidates = [repo for repo in scan["repositories"] if repo["status"] in {"stale", "archived"}]
    if args.category == "stale":
        candidates = [repo for repo in candidates if repo["status"] == "stale"]
    elif args.category == "archived":
        candidates = [repo for repo in candidates if repo["status"] == "archived"]

    if not candidates:
        print("No repositories match this cleanup filter. Your stars are looking tidy!\n")
        return 0

    print(f"\nFound {len(candidates)} cleanup candidate(s). This command will ask before each removal.\n")
    print("A stale repository only means it has had no push in the configured time window; it may still be useful.\n")
    removed = 0
    skipped = 0
    failed = 0
    for repo in candidates:
        name = repo["full_name"]
        age = repo.get("days_since_push")
        age_label = f"last pushed {age} days ago" if age is not None else "archived"
        if repo["status"] == "archived":
            age_label = "archived by its owner"
        answer = input(f"Unstar {name} ({age_label})? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            skipped += 1
            continue
        try:
            client.unstar(name)
            removed += 1
            scan["repositories"] = [item for item in scan["repositories"] if item["full_name"] != name]
            scan["total"] = len(scan["repositories"])
            save_scan(scan, args.cache_file)
            print(f"  ✓ Unstarred {name}")
        except GitHubAPIError as exc:
            failed += 1
            print(f"  ! Could not unstar {name}: {exc}", file=sys.stderr)
    scan["total"] = len(scan["repositories"])
    save_scan(scan, args.cache_file)
    print(f"\nDone. Removed: {removed} · Kept/skipped: {skipped} · Failed: {failed}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="starcleaner",
        description="Find stale and archived repositories in your GitHub stars.",
    )
    parser.add_argument("--version", action="version", version=f"StarCleaner {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan and categorize your starred repositories")
    scan_parser.add_argument("--token", help=argparse.SUPPRESS)
    scan_parser.add_argument("--stale-days", type=int, default=365, help="Mark repositories stale after this many days without a push (default: 365)")
    _cache_arg(scan_parser)
    scan_parser.set_defaults(handler=command_scan)

    report_parser = subparsers.add_parser("report", help="Show the most recently saved scan")
    report_parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    _cache_arg(report_parser)
    report_parser.set_defaults(handler=command_report)

    clean_parser = subparsers.add_parser("clean", help="Interactively unstar stale or archived repositories")
    clean_parser.add_argument("--token", help=argparse.SUPPRESS)
    clean_parser.add_argument("--interactive", action="store_true", help="Confirm each removal (this is always enabled)")
    clean_parser.add_argument("--category", choices=("all", "stale", "archived"), default="all")
    clean_parser.add_argument("--stale-days", type=int, default=None, help="Override the inactivity threshold (default: saved scan setting, or 365 days)")
    _cache_arg(clean_parser)
    clean_parser.set_defaults(handler=command_clean)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "stale_days", None) is not None and args.stale_days < 1:
        parser.error("--stale-days must be at least 1")
    try:
        return args.handler(args)
    except (GitHubAPIError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
