"""Terminal and Markdown reports."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any


STATUS_LABELS = {
    "active": "ACTIVE",
    "stale": "STALE",
    "archived": "ARCHIVED",
    "unknown": "UNKNOWN",
}


def _age(repo: dict[str, Any]) -> str:
    days = repo.get("days_since_push")
    if days is None:
        return "unknown"
    if days == 0:
        return "today"
    return f"{days}d ago"


def _description(value: str, width: int = 42) -> str:
    value = " ".join((value or "").split())
    if len(value) <= width:
        return value
    return value[: width - 1].rstrip() + "…"


def render_text(scan: dict[str, Any]) -> str:
    repositories = scan["repositories"]
    counts = Counter(repo["status"] for repo in repositories)
    lines = [
        "",
        "  ⭐  STARCLEANER",
        "  Keep the stars. Lose the clutter.",
        "",
        f"  Scanned {len(repositories)} starred repositories",
        f"  Inactive threshold: {scan['stale_days']} days without a push",
        "",
        f"  🟢 Active       {counts['active']:>5}",
        f"  🟡 Stale        {counts['stale']:>5}",
        f"  🔴 Archived     {counts['archived']:>5}",
        f"  ⚪ Unknown      {counts['unknown']:>5}",
        "",
    ]
    if not repositories:
        lines.append("  No starred repositories were found.")
        return "\n".join(lines) + "\n"

    name_width = min(36, max(18, max(len(repo["full_name"]) for repo in repositories)))
    lines.append(f"  {'STATUS':<9} {'REPOSITORY':<{name_width}} {'LAST PUSH':>10}  DESCRIPTION")
    lines.append(f"  {'-' * 9} {'-' * name_width} {'-' * 10}  {'-' * 42}")
    for repo in repositories:
        name = repo["full_name"]
        if len(name) > name_width:
            name = name[: name_width - 1] + "…"
        status = STATUS_LABELS.get(repo["status"], "UNKNOWN")
        lines.append(
            f"  {status:<9} {name:<{name_width}} {_age(repo):>10}  {_description(repo['description'])}"
        )
    lines.extend(["", "  Tip: run `starcleaner clean --interactive` to review stale/archived stars.", ""])
    return "\n".join(lines)


def render_markdown(scan: dict[str, Any]) -> str:
    repositories = scan["repositories"]
    counts = Counter(repo["status"] for repo in repositories)
    generated = scan.get("generated_at", "unknown")
    try:
        generated = datetime.fromisoformat(generated).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        pass
    lines = [
        "# StarCleaner report",
        "",
        f"Generated: {generated}",
        f"Inactive threshold: **{scan['stale_days']} days** without a push",
        "",
        "| Status | Repositories |",
        "|---|---:|",
        f"| Active | {counts['active']} |",
        f"| Stale | {counts['stale']} |",
        f"| Archived | {counts['archived']} |",
        f"| Unknown | {counts['unknown']} |",
        "",
        "| Status | Repository | Last push | Description |",
        "|---|---|---:|---|",
    ]
    for repo in repositories:
        description = (repo.get("description") or "").replace("|", "\\|").replace("\n", " ")
        name = repo["full_name"]
        url = repo.get("html_url") or f"https://github.com/{name}"
        lines.append(
            f"| {STATUS_LABELS.get(repo['status'], 'UNKNOWN')} | [{name}]({url}) | {_age(repo)} | {description} |"
        )
    return "\n".join(lines) + "\n"
