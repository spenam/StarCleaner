import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from starcleaner.github import GitHubClient


class GitHubClientTests(unittest.TestCase):
    def test_paginates_until_a_short_page(self):
        client = GitHubClient("test-token")
        first_page = [{"full_name": f"org/repo-{i}"} for i in range(100)]
        second_page = [{"full_name": "org/last-repo"}]
        with patch.object(client, "_request", side_effect=[first_page, second_page]) as request:
            repositories = client.list_starred_repositories()
        self.assertEqual(len(repositories), 101)
        self.assertEqual(request.call_count, 2)
        self.assertIn("page=1", request.call_args_list[0].args[0])
        self.assertIn("page=2", request.call_args_list[1].args[0])

    def test_unstar_uses_delete_and_quotes_repository_path(self):
        client = GitHubClient("test-token")
        with patch.object(client, "_request") as request:
            client.unstar("owner/repo with spaces")
        request.assert_called_once_with("/user/starred/owner/repo%20with%20spaces", method="DELETE")

    def test_unstar_rejects_malformed_name(self):
        client = GitHubClient("test-token")
        with self.assertRaises(ValueError):
            client.unstar("not-a-full-name")


if __name__ == "__main__":
    unittest.main()
