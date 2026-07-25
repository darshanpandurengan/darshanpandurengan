#!/usr/bin/env python3
"""
fetch_contributions.py

Pulls a real GitHub contribution calendar with NO token and NO GraphQL
API call. GitHub serves the calendar as a public HTML fragment at:

    https://github.com/users/<username>/contributions

This is the same fragment the profile page itself embeds, so it's
always in sync with what visitors see. We parse the day cells with
BeautifulSoup and pull the exact per-day count out of each cell's
accessible tooltip (the calendar's `data-level` attribute only gives a
0-4 bucket, not the real number).

Writes data/contributions.json:
    {
      "username": "...",
      "generated_at": "...",
      "total_contributions": 1234,
      "days": [{"date": "2026-07-20", "level": 0, "count": 0}, ...],
      "stats": {
        "current_streak": int,
        "longest_streak": int,
        "best_day": {"date": "...", "count": int},
        "monthly_totals": {"2026-07": int, ...}
      }
    }

Usage:
    python scripts/fetch_contributions.py
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "darshanpandurengan"

CONTRIB_URL = "https://github.com/users/{username}/contributions"
OUTPUT_PATH = Path("data/contributions.json")

COUNT_RE = re.compile(r"(\d[\d,]*|No)\s+contributions?\s+on", re.IGNORECASE)
TOTAL_RE = re.compile(r"([\d,]+)\s+contributions?\s+in the last year", re.IGNORECASE)


def fetch_html(username: str) -> str:
    url = CONTRIB_URL.format(username=username)
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Tooltips carry the exact count and are linked to their day cell
    # via `for="<cell-id>"`, since data-level is only a 0-4 bucket.
    tooltip_by_target = {}
    for tip in soup.select("tool-tip[for]"):
        tooltip_by_target[tip.get("for")] = tip.get_text(strip=True)

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        date = cell["data-date"]
        level = int(cell.get("data-level", 0))
        cell_id = cell.get("id")

        count = 0
        tooltip_text = tooltip_by_target.get(cell_id, "")
        m = COUNT_RE.search(tooltip_text)
        if m:
            raw = m.group(1).replace(",", "")
            count = 0 if raw.lower() == "no" else int(raw)

        days.append({"date": date, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def parse_total(html: str, days) -> int:
    m = TOTAL_RE.search(html)
    if m:
        return int(m.group(1).replace(",", ""))
    return sum(d["count"] for d in days)


def compute_stats(days):
    monthly_totals = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # "YYYY-MM"
        monthly_totals[month_key] += d["count"]

    best_day = max(days, key=lambda d: d["count"], default=None)
    best_day_out = (
        {"date": best_day["date"], "count": best_day["count"]}
        if best_day and best_day["count"] > 0
        else None
    )

    # Longest streak of consecutive days with count > 0.
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    # Current streak: walk backwards from the most recent day.
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day_out,
        "monthly_totals": dict(sorted(monthly_totals.items())),
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    if username == "YOUR_GITHUB_USERNAME":
        print(
            "Set USERNAME at the top of scripts/fetch_contributions.py "
            "(or pass it as an argument) before running.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Fetching contributions for '{username}'...")
    html = fetch_html(username)
    days = parse_days(html)

    if not days:
        print("No day cells parsed -- GitHub may have changed its markup.", file=sys.stderr)
        sys.exit(1)

    total = parse_total(html, days)
    stats = compute_stats(days)

    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_contributions": total,
        "days": days,
        "stats": stats,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH} ({len(days)} days, {total} total contributions)")


if __name__ == "__main__":
    main()
