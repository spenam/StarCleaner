import os
from pathlib import Path


def load_env(env_file: Path | None = None) -> None:
    env_file = env_file or Path(__file__).resolve().parents[2] / ".env"

    if not env_file.is_file():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)