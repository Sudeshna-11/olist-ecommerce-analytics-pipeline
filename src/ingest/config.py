"""Environment loading for the ingest pipeline.

Splits configuration into two files so secrets stay out of any context
where the rest of `.env` is read or shared:

  .env          - non-sensitive config (TARGET, hostnames, ports, usernames,
                  warehouse/database/schema/role). Safe to share, paste in
                  issue reports, paste in AI assistant chats, etc.
  .secrets.env  - passwords, API keys, tokens. Gitignored. Never paste
                  the contents of this file anywhere.

Both files are loaded into `os.environ`. `.secrets.env` is loaded with
`override=True` so a value in secrets always wins if both files define
the same key (typical migration footgun: leaving a stale POSTGRES_PASSWORD
in `.env` while the real one lives in `.secrets.env`).
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
SECRETS_FILE = PROJECT_ROOT / ".secrets.env"


def load_env() -> None:
    """Load .env then .secrets.env. Both files are optional; missing files
    are ignored silently."""
    load_dotenv(ENV_FILE, override=False)
    load_dotenv(SECRETS_FILE, override=True)
