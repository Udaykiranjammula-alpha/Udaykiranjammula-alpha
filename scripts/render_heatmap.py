#!/usr/bin/env python3
"""Render a self-hosted SVG contribution heatmap from normalized JSON."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import xml.etree.ElementTree as element_tree
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Tokyo Night palette: 0=empty, 1=low, 2=medium, 3=high, 4=peak
COLORS = ("#16161e", "#292e42", "#7aa2f7", "#bb9af7", "#7dcfff")


def load_days(source: Path) -> tuple[str, list[tuple[date, int]]]:
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
        username, raw_days = document["username"], document["days"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"Could not read valid contribution data from {source}: {error}") from error
    if not isinstance(username, str) or not isinstance(raw_days, list) or not raw_days:
        raise RuntimeError("Contribution JSON is missing a username or non-empty day list.")
    result, seen_dates = [], set()
    for item in raw_days:
        try:
            day, count = datetime.strptime(item["date"], "%Y-%m-%d").date(), item["count"]
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Contribution JSON has an invalid date entry.") from error
        if not isinstance(count, int) or count < 0 or day in seen_dates:
            raise RuntimeError("Contribution JSON has an invalid count or duplicate day.")
        seen_dates.add(day)
        result.append((day, count))
    return username, sorted(result)


def level(count: int, maximum: int) -> int:
    return 0 if count == 0 or maximum == 0 else min(4, max(1, (count * 4 + maximum - 1) // maximum))


def render_svg(username: str, days: list[tuple[date, int]]) -> str:
    first_day, last_day = days[0][0], days[-1][0]
    start = first_day - timedelta(days=(first_day.weekday() + 1) % 7)
    end = last_day + timedelta(days=6 - ((last_day.weekday() + 1) % 7))
    lookup, maximum = dict(days), max(count for _, count in days)
    cell, gap, x_origin, y_origin = 11, 4, 48, 76
    cells, current, index = [], start, 0
    while current <= end:
        column, row = (current - start).days // 7, (current.weekday() + 1) % 7
        count = lookup.get(current, 0)
        x, y = x_origin + column * (cell + gap), y_origin + row * (cell + gap)
        cells.append(f'<rect class="day level-{level(count, maximum)}" style="--delay:{min(index * 9, 2100)}ms" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" data-date="{current.isoformat()}" data-count="{count}"><title>{current.isoformat()}: {count} contributions</title></rect>')
        current, index = current + timedelta(days=1), index + 1
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="216" viewBox="0 0 860 216" role="img" aria-labelledby="title description"><title id="title">GitHub contribution calendar for {escape(username)}</title><desc id="description">A self-hosted visualization generated from GitHub's public contribution calendar.</desc><style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#7aa2f7;font-size:11px}}.panel{{fill:#1a1b26;stroke:#414868}}.header{{fill:#24283b}}.accent{{fill:#7dcfff}}.day{{opacity:0;animation:reveal 420ms ease-out forwards;animation-delay:var(--delay)}}.level-0{{fill:{COLORS[0]}}}.level-1{{fill:{COLORS[1]}}}.level-2{{fill:{COLORS[2]}}}.level-3{{fill:{COLORS[3]}}}.level-4{{fill:{COLORS[4]}}}@keyframes reveal{{from{{opacity:0;transform:scale(.65)}}to{{opacity:1;transform:scale(1)}}}}@media (prefers-reduced-motion:reduce){{.day{{animation:none;opacity:1}}}}</style><rect class="panel" x=".5" y=".5" width="859" height="215" rx="12"/><path class="header" d="M.5 12.5a12 12 0 0 1 12-12h835a12 12 0 0 1 12 12v33H.5z"/><circle class="accent" cx="28" cy="29" r="5"/><text x="43" y="33" fill="#c0caf5">uday@github:~$ git log --contributions</text><text x="760" y="33" fill="#7aa2f7">public data</text><line x1="20" y1="45.5" x2="840" y2="45.5" stroke="#414868"/><text x="22" y="95">Sun</text><text x="22" y="125">Tue</text><text x="22" y="155">Thu</text><text x="22" y="185">Sat</text>{''.join(cells)}<text x="666" y="194">less</text><rect x="702" y="185" width="11" height="11" rx="2" fill="{COLORS[0]}"/><rect x="717" y="185" width="11" height="11" rx="2" fill="{COLORS[1]}"/><rect x="732" y="185" width="11" height="11" rx="2" fill="{COLORS[2]}"/><rect x="747" y="185" width="11" height="11" rx="2" fill="{COLORS[3]}"/><rect x="762" y="185" width="11" height="11" rx="2" fill="{COLORS[4]}"/><text x="782" y="194">more</text></svg>\n'''



def write_text_atomic(destination: Path, content: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False, suffix=".tmp")
    temp_path = Path(temp_file.name)
    try:
        with temp_file as stream:
            stream.write(content)
        temp_path.replace(destination)
    except BaseException:
        if temp_path.exists():
            temp_path.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "contributions.json")
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "contrib-heatmap.svg")
    arguments = parser.parse_args()
    try:
        username, days = load_days(arguments.input)
        svg = render_svg(username, days)
        element_tree.fromstring(svg)
        write_text_atomic(arguments.output, svg)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Rendered {len(days)} contribution days to {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
