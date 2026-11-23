"""Repository classification and local scan storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CACHE_FILE = Path.home() / ".starcleaner" / "last_scan.json"


def parse_github_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def analyze_repository(raw: dict[str, Any], stale_days: int, now: datetime | None = None) -> dict[str, Any]:
    """Convert a GitHub repository payload into StarCleaner's local record.

    Inactivity is measured using pushed_at (code activity), not updated_at
    (which can change for reasons unrelated to code changes).
    """
    now = now or datetime.now(timezone.utc)
    pushed_at = parse_github_date(raw.get("pushed_at"))
    days_since_push = max(0, (now - pushed_at).days) if pushed_at else None

    if raw.get("archived") is True:
        status = "archived"
    elif days_since_push is None:
        status = "unknown"
    else:
        status = "stale" if days_since_push >= stale_days else "active"

    owner = raw.get("owner") or {}
    full_name = raw.get("full_name") or f"{owner.get('login', 'unknown')}/{raw.get('name', 'unknown')}"
    return {
        "full_name": full_name,
        "html_url": raw.get("html_url") or f"https://github.com/{full_name}",
        "description": raw.get("description") or "",
        "language": raw.get("language"),
        "archived": bool(raw.get("archived", False)),
        "disabled": bool(raw.get("disabled", False)),
        "stargazers_count": int(raw.get("stargazers_count") or 0),
        "pushed_at": pushed_at.isoformat() if pushed_at else None,
        "days_since_push": days_since_push,
        "status": status,
    }


def build_scan(raw_repositories: list[dict[str, Any]], stale_days: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    repositories = [analyze_repository(repo, stale_days, now) for repo in raw_repositories]
    repositories.sort(
        key=lambda repo: (
            {"archived": 0, "stale": 1, "unknown": 2, "active": 3}[repo["status"]],
            -(repo["days_since_push"] or 0),
            repo["full_name"].lower(),
        )
    )
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "stale_days": stale_days,
        "total": len(repositories),
        "repositories": repositories,
    }


def save_scan(scan: dict[str, Any], path: Path = CACHE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(scan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_scan(path: Path = CACHE_FILE) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"No saved scan found at {path}. Run `starcleaner scan` first.")
    try:
        scan = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Saved scan at {path} is not valid JSON. Run `starcleaner scan` again.") from exc
    if scan.get("schema_version") != 1 or not isinstance(scan.get("repositories"), list):
        raise ValueError(f"Saved scan at {path} has an unsupported format. Run `starcleaner scan` again.")
    return scan
