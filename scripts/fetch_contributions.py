#!/usr/bin/env python3
"""Fetch and validate GitHub's public contribution calendar."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as element_tree
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_USERNAME = "Udaykiranjammula-alpha"
CONTRIBUTIONS_URL = "https://github.com/users/{username}/contributions"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fetch_calendar(username: str) -> bytes:
    url = CONTRIBUTIONS_URL.format(username=username)
    curl = shutil.which("curl")
    if curl:
        fallback = subprocess.run(
            [curl, "--fail", "--location", "--silent", "--show-error", "--connect-timeout", "30", "--header", "Accept: image/svg+xml,text/html;q=0.9,*/*;q=0.8", "--user-agent", "UdayProfileContributionBot/1.0 (+https://github.com/Udaykiranjammula-alpha)", url],
            capture_output=True,
            check=False,
            timeout=45,
        )
        if fallback.returncode == 0 and fallback.stdout:
            return fallback.stdout
    request = urllib.request.Request(
        url,
        headers={"Accept": "image/svg+xml,text/html;q=0.9,*/*;q=0.8", "User-Agent": "UdayProfileContributionBot/1.0 (+https://github.com/Udaykiranjammula-alpha)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not fetch GitHub's public contribution calendar: {error}") from error
    if not payload:
        raise RuntimeError("GitHub returned an empty contribution calendar response.")
    return payload


def parse_calendar(payload: bytes) -> list[dict[str, int | str]]:
    try:
        root = element_tree.fromstring(payload)
    except element_tree.ParseError as error:
        raise RuntimeError("GitHub contribution response is not parseable XML/SVG.") from error
    counts_by_id: dict[str, int] = {}
    for element in root.iter():
        if element.tag != "tool-tip" or "for" not in element.attrib:
            continue
        label = " ".join(element.itertext()).strip()
        if label.startswith("No contributions"):
            counts_by_id[element.attrib["for"]] = 0
            continue
        match = re.search(r"\b(\d+) contributions?\b", label)
        if match:
            counts_by_id[element.attrib["for"]] = int(match.group(1))

    days, seen_dates = [], set()
    for element in root.iter():
        day = element.attrib.get("data-date")
        count = element.attrib.get("data-count") or counts_by_id.get(element.attrib.get("id", ""))
        if day is None or count is None:
            continue
        if not DATE_PATTERN.fullmatch(day):
            raise RuntimeError(f"GitHub returned an invalid contribution date: {day!r}")
        try:
            datetime.strptime(day, "%Y-%m-%d")
            contribution_count = int(count)
        except ValueError as error:
            raise RuntimeError(f"GitHub returned an invalid count for {day}: {count!r}") from error
        if contribution_count < 0 or day in seen_dates:
            raise RuntimeError(f"GitHub returned invalid or duplicate data for {day}.")
        seen_dates.add(day)
        days.append({"date": day, "count": contribution_count})
    if not days:
        raise RuntimeError("No contribution days were found. GitHub's public markup may have changed or access was limited.")
    return sorted(days, key=lambda item: str(item["date"]))


def write_json_atomic(destination: Path, document: dict[str, object]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False, suffix=".tmp") as stream:
        json.dump(document, stream, indent=2)
        stream.write("\n")
        temporary_path = Path(stream.name)
    temporary_path.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "contributions.json")
    arguments = parser.parse_args()
    try:
        days = parse_calendar(fetch_calendar(arguments.username))
        write_json_atomic(arguments.output, {"schema_version": 1, "username": arguments.username, "source": CONTRIBUTIONS_URL.format(username=arguments.username), "fetched_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "days": days})
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Saved {len(days)} real contribution days to {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
