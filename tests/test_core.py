import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from starcleaner.core import analyze_repository, build_scan

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)


def repo(**overrides):
    value = {
        "full_name": "octocat/hello-world",
        "html_url": "https://github.com/octocat/hello-world",
        "description": "A sample repository",
        "language": "Python",
        "archived": False,
        "disabled": False,
        "stargazers_count": 42,
        "pushed_at": "2026-11-01T12:00:00Z",
    }
    value.update(overrides)
    return value


class AnalyzeRepositoryTests(unittest.TestCase):
    def test_recent_push_is_active(self):
        result = analyze_repository(repo(), stale_days=365, now=NOW)
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["days_since_push"], 22)

    def test_old_push_is_stale(self):
        result = analyze_repository(repo(pushed_at="2024-01-01T00:00:00Z"), stale_days=365, now=NOW)
        self.assertEqual(result["status"], "stale")

    def test_archived_takes_precedence(self):
        result = analyze_repository(repo(archived=True), stale_days=365, now=NOW)
        self.assertEqual(result["status"], "archived")
        self.assertEqual(result["days_since_push"], (NOW - datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)).days)

    def test_missing_push_date_is_unknown(self):
        result = analyze_repository(repo(pushed_at=None), stale_days=365, now=NOW)
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["days_since_push"])

    def test_future_push_date_is_zero_days(self):
        result = analyze_repository(repo(pushed_at="2026-12-01T00:00:00Z"), stale_days=365, now=NOW)
        self.assertEqual(result["days_since_push"], 0)

    def test_threshold_is_inclusive(self):
        result = analyze_repository(repo(pushed_at="2025-11-23T12:00:00Z"), stale_days=365, now=NOW)
        self.assertEqual(result["status"], "stale")


class BuildScanTests(unittest.TestCase):
    def test_scan_counts_all_repositories(self):
        scan = build_scan([repo(), repo(full_name="org/old", pushed_at="2020-01-01T00:00:00Z")], 365)
        self.assertEqual(scan["total"], 2)
        self.assertEqual(len(scan["repositories"]), 2)
        self.assertEqual(scan["repositories"][0]["status"], "stale")


if __name__ == "__main__":
    unittest.main()
