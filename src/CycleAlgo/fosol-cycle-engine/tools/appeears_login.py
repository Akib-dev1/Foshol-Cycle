"""One-time AppEEARS login helper.

Prompts for NASA Earthdata credentials locally (password hidden), exchanges
them for an AppEEARS API token, and writes the token to a gitignored file.
The password is never stored or printed.

Run:
    python fosol-cycle-engine/tools/appeears_login.py
"""

from __future__ import annotations

import base64
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LOGIN_URL = "https://appeears.earthdatacloud.nasa.gov/api/login"
TOKEN_PATH = Path(__file__).resolve().parents[2] / "appeears_token.txt"


def main() -> int:
    username = os.environ.get("EARTHDATA_USERNAME") or input("Earthdata username: ").strip()
    password = os.environ.get("EARTHDATA_PASSWORD") or getpass.getpass("Earthdata password: ")
    if not username or not password:
        print("Username and password are required.", file=sys.stderr)
        return 1

    basic = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        LOGIN_URL,
        data=b"grant_type=client_credentials",
        method="POST",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        print(f"Login failed: HTTP {exc.code}. Check the Earthdata credentials.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - never echo credentials
        print(f"Login failed: {type(exc).__name__}.", file=sys.stderr)
        return 1

    token = payload.get("token")
    if not token:
        print("Login failed: no token in the response.", file=sys.stderr)
        return 1

    record = {
        "token": token,
        "expiration": payload.get("expiration"),
        "obtained_at": datetime.now(timezone.utc).isoformat(),
    }
    TOKEN_PATH.write_text(json.dumps(record), encoding="utf-8")
    print(f"AppEEARS token saved to {TOKEN_PATH}")
    print(f"Expires: {record['expiration']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
