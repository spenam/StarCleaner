# ⭐ StarCleaner

**Keep the stars. Lose the clutter.**

StarCleaner is a small, dependency-free CLI that scans your GitHub stars, finds archived or inactive repositories, and helps you review them before un-starring anything.

> Inactivity is measured by the repository's last push (`pushed_at`). A stale label is only a review signal — it does not mean a project is abandoned or useless.

## Features

- Fetch all repositories starred by your authenticated GitHub account.
- Categorize repositories as **active**, **stale**, **archived**, or **unknown**.
- Set your own inactivity threshold (365 days by default).
- Save a local JSON scan so you can view it again or export Markdown.
- Interactively unstar repositories, with a prompt for every repository.
- No third-party Python dependencies. No database server. No AI required.

## Requirements

- Python 3.10 or newer
- A GitHub personal access token

For a fine-grained personal access token, grant **Starring: read** to scan. To use the cleanup command, grant **Starring: write** and repository **Metadata: read**. Keep the token private.

## Install from a local checkout

```bash
git clone https://github.com/YOUR_USERNAME/starcleaner.git
cd starcleaner
python -m pip install .
```

Or run it without installing:

```bash
python -m pip install -e .
```

## Configure your token

Set the token as an environment variable. StarCleaner never writes it to the scan file.

macOS / Linux:

```bash
export STARCLEANER_TOKEN="github_pat_your_token_here"
```

Windows PowerShell:

```powershell
$env:STARCLEANER_TOKEN = "github_pat_your_token_here"
```

`GITHUB_TOKEN` is also accepted. You can alternatively pass `--token` to `scan` or `clean`, but an environment variable is safer because command-line arguments may be visible in process listings.

## Usage

Scan your stars (read-only):

```bash
starcleaner scan
```

Change the inactivity threshold to 180 days:

```bash
starcleaner scan --stale-days 180
```

View the latest saved scan:

```bash
starcleaner report
starcleaner report --format markdown
starcleaner report --format json
```

Review cleanup candidates. StarCleaner fetches a fresh scan first and asks before every removal:

```bash
starcleaner clean --interactive
```

Only review one category:

```bash
starcleaner clean --category stale
starcleaner clean --category archived
starcleaner clean --stale-days 180
```

The cleanup command is deliberately interactive. There is no bulk-delete or automatic-unstar mode.

## Local data

The latest scan is saved to:

```text
~/.starcleaner/last_scan.json
```

It contains repository metadata only — never your GitHub token. Override the location with `--cache-file`:

```bash
starcleaner scan --cache-file ./my-scan.json
starcleaner report --cache-file ./my-scan.json
```

## What the labels mean

| Label | Meaning |
|---|---|
| Active | The repository received a push within the configured number of days. |
| Stale | The repository has not received a push within the configured number of days. |
| Archived | The repository owner has archived it. |
| Unknown | GitHub did not provide a valid last-push timestamp. |

A repository can be perfectly useful even if it has not changed recently. Always review a candidate before un-starring it.

## Development

Run the tests with the standard library:

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- [x] Scan starred repositories
- [x] Classify archived and inactive repositories
- [x] Terminal and Markdown reports
- [x] Interactive, confirmation-based cleanup
- [ ] Better terminal formatting and progress indicator
- [ ] Optional SQLite history and before/after statistics

## License

MIT
