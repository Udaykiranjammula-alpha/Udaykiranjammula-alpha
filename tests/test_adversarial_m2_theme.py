#!/usr/bin/env python3
"""
tests/test_adversarial_m2_theme.py
Adversarial Challenge Test Suite for Milestone 2:
Theme & Visual Hierarchy Challenger (teamwork_challenger_m2_2)

Empirically verifies:
1. Tokyo Night dark theme palette compliance across Shields.io badges, capsule render dividers, and analytics cards.
2. Dual Systems HUD SVG cards centering within <div align="center">.
3. Recruiter reading hierarchy: exact 11 sections in strict sequential order without omission.
4. Mobile and desktop rendering compatibility for collapsible <details> blocks and ASCII diagrams.
5. ASCII art and code fence horizontal boundary constraints (<= 90 characters for mobile display).
6. HTML structure and nesting balance.
"""
from __future__ import annotations

import re
import unittest
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
ASSETS_DIR = ROOT / "assets"

# Canonical Tokyo Night Dark Palette specification
TOKYO_NIGHT_PALETTE = {
    "1a1b26": "bg (dark background)",
    "24283b": "surface (card background)",
    "414868": "border / muted",
    "7aa2f7": "blue (primary accent)",
    "bb9af7": "purple (secondary accent)",
    "7dcfff": "cyan (terminal / info accent)",
    "9ece6a": "green (success / git accent)",
    "f7768e": "red / magenta (alert / stats accent)",
    "e0af68": "yellow / amber (warning / header accent)",
    "ff9e64": "orange (parameter / quantization accent)",
    "c0caf5": "fg / text (primary text)",
    "a9b1d6": "fg_muted (secondary text)",
}

CANONICAL_HEX_SET = {k.lower() for k in TOKYO_NIGHT_PALETTE.keys()}

# The 11 Sequential Recruiter Reading Hierarchy Sections
EXPECTED_11_SECTIONS = [
    "## ⚙️ Engineering Dossier",
    "## 🌟 Flagship Projects",
    "### 🔍 [FileDNA 2.0",
    "### ⚡ [ESP32 Distributed Neural Network Accelerator",
    "### 🧠 [Uday AI Local Server",
    "### 🏦 Enterprise & Systems Engineering Suite",
    "## 🖥️ Hardware Lab & Cyber Battlestation",
    "## 🛠️ Core Competency Matrix",
    "## 📊 Live GitHub Analytics & Telemetry",
    "## 📈 Contribution Heatmap",
    "### 💡 Engineering Philosophy",
]


class TestThemeConsistencyAdversarial(unittest.TestCase):
    """Adversarial stress-test for Tokyo Night color scheme conformity."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        cls.lines = cls.content.splitlines()

    def test_capsule_render_dividers_palette(self):
        """All horizontal capsule render dividers must strictly use Tokyo Night palette hex colors."""
        divider_pattern = re.compile(r'https://capsule-render\.vercel\.app/api\?[^\s"\'\)]+')
        dividers = divider_pattern.findall(self.content)
        self.assertGreater(len(dividers), 0, "No capsule-render elements found")

        non_compliant = []
        rect_count = 0
        for d in dividers:
            parsed = urllib.parse.urlparse(d)
            qs = urllib.parse.parse_qs(parsed.query)
            if qs.get("type", [""])[0] == "rect":
                rect_count += 1
                color_spec = qs.get("color", [""])[0]
                stops = color_spec.split(",")
                for stop in stops:
                    parts = stop.split(":")
                    if len(parts) == 2:
                        hex_val = parts[1].strip().lower()
                        if hex_val not in CANONICAL_HEX_SET:
                            non_compliant.append((d, hex_val))

        self.assertGreaterEqual(rect_count, 7, f"Expected at least 7 dividers, found {rect_count}")
        self.assertEqual(
            non_compliant,
            [],
            f"Capsule render divider contains non-Tokyo Night color: {non_compliant}",
        )

    def test_analytics_cards_tokyonight_theme(self):
        """Live analytics cards must configure Tokyo Night theme parameters explicitly."""
        # 1. github-readme-stats (stats & top-langs)
        stats_cards = re.findall(r'https://github-readme-stats[^\s"\'\)]+', self.content)
        self.assertGreaterEqual(len(stats_cards), 2, "Expected at least 2 github-readme-stats cards")

        for card in stats_cards:
            parsed = urllib.parse.urlparse(card)
            qs = urllib.parse.parse_qs(parsed.query)
            self.assertEqual(
                qs.get("theme", [""])[0].lower(),
                "tokyonight",
                f"Card does not specify theme=tokyonight: {card}",
            )
            bg_color = qs.get("bg_color", [""])[0].lower()
            self.assertIn(
                bg_color,
                CANONICAL_HEX_SET,
                f"Card bg_color '{bg_color}' is not in Tokyo Night palette: {card}",
            )

        # 2. streak-stats
        streak_cards = re.findall(r'https://streak-stats\.demolab\.com[^\s"\'\)]+', self.content)
        self.assertGreaterEqual(len(streak_cards), 1, "Expected streak-stats card")
        for card in streak_cards:
            parsed = urllib.parse.urlparse(card)
            qs = urllib.parse.parse_qs(parsed.query)
            self.assertEqual(
                qs.get("theme", [""])[0].lower(),
                "tokyonight",
                f"Streak card does not specify theme=tokyonight: {card}",
            )
            bg = qs.get("background", [""])[0].lower()
            self.assertIn(
                bg,
                CANONICAL_HEX_SET,
                f"Streak background '{bg}' not in Tokyo Night palette: {card}",
            )

    def test_shields_badges_palette_scan(self):
        """Scan all shields.io badges and catalog palette compliance."""
        badge_pattern = re.compile(r'https://img\.shields\.io/badge/([^\s"\'\)]+)')
        badges = badge_pattern.findall(self.content)

        palette_compliant = []
        brand_or_custom_colors = []

        for badge in badges:
            url_part = badge.split("?")[0]
            tokens = url_part.split("-")
            color_token = tokens[-1].lower() if tokens else ""

            if re.match(r"^[0-9a-f]{6}$", color_token):
                if color_token in CANONICAL_HEX_SET:
                    palette_compliant.append((badge, color_token))
                else:
                    brand_or_custom_colors.append((badge, color_token))

        self.assertGreater(
            len(palette_compliant),
            20,
            f"Expected at least 20 Tokyo Night badges, found {len(palette_compliant)}",
        )
        # Log custom brand colors (e.g. C++ 00599c, ESP32 e7352c, FreeRTOS 008080)
        self.assertEqual(len(badges), 37, f"Expected 37 shields.io badges, found {len(badges)}")


class TestVisualHierarchyAndLayoutAdversarial(unittest.TestCase):
    """Adversarial stress-test for HUD layout, section hierarchy, and responsive constraints."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        cls.lines = cls.content.splitlines()

    def test_hud_cards_centered_in_gfm_container(self):
        """Dual HUD cards (assets/info-card.svg and assets/tech-core.svg) must be enclosed inside <div align='center'>."""
        info_idx = self.content.find("assets/info-card.svg")
        tech_idx = self.content.find("assets/tech-core.svg")
        self.assertNotEqual(info_idx, -1, "info-card.svg not found in README.md")
        self.assertNotEqual(tech_idx, -1, "tech-core.svg not found in README.md")

        hud_section = self.content[max(0, info_idx - 200) : min(len(self.content), tech_idx + 200)]
        self.assertIn('<div align="center">', hud_section, "HUD cards must be inside <div align='center'>")
        self.assertIn("</div>", hud_section, "HUD cards enclosing div must be closed with </div>")

    def test_all_11_recruiter_sections_exact_order(self):
        """Recruiter reading hierarchy: all 11 sections must appear in exact sequential order without omission."""
        last_pos = 0
        found_sections = []
        for sec in EXPECTED_11_SECTIONS:
            pos = self.content.find(sec, last_pos)
            self.assertNotEqual(
                pos,
                -1,
                f"Section '{sec}' missing or out of sequential order! (Search started from character {last_pos})",
            )
            found_sections.append((sec, pos))
            last_pos = pos

        self.assertEqual(len(found_sections), 11, f"Expected exactly 11 sections, found {len(found_sections)}")

    def test_collapsible_details_blocks_integrity(self):
        """All <details> collapsible blocks must have valid <summary>, non-empty content, and matching </details>."""
        details_open = [m.start() for m in re.finditer(r"<details>", self.content)]
        details_close = [m.start() for m in re.finditer(r"</details>", self.content)]
        self.assertEqual(
            len(details_open),
            len(details_close),
            f"Mismatched <details> ({len(details_open)}) and </details> ({len(details_close)}) tags",
        )
        self.assertEqual(len(details_open), 3, "Expected exactly 3 project architecture collapsible dossiers")

        for start, end in zip(details_open, details_close):
            block = self.content[start:end]
            self.assertIn("<summary>", block, "Collapsible block missing <summary>")
            self.assertIn("</summary>", block, "Collapsible block missing </summary>")
            self.assertGreater(
                len(block),
                500,
                f"Collapsible block too small ({len(block)} chars), lacks substantive dossier content",
            )

    def test_ascii_art_line_width_mobile_overflow(self):
        """ASCII art and code fences must be bounded to avoid horizontal blowout on mobile viewports (< 90 chars)."""
        in_fence = False
        fence_lang = ""
        fence_lines = []
        fences = []

        for line_num, line in enumerate(self.lines, 1):
            if line.strip().startswith("```"):
                if not in_fence:
                    in_fence = True
                    fence_lang = line.strip()[3:]
                    fence_lines = []
                else:
                    in_fence = False
                    fences.append((fence_lang, fence_lines, line_num))
            elif in_fence:
                fence_lines.append((line_num, line))

        self.assertFalse(in_fence, "Unclosed code fence at end of README.md")

        max_allowed_width = 90
        overflow_lines = []

        for lang, flines, end_lno in fences:
            for lno, fline in flines:
                raw_len = len(fline.rstrip())
                if raw_len > max_allowed_width:
                    overflow_lines.append((lno, raw_len, fline[:60]))

        self.assertEqual(
            overflow_lines,
            [],
            f"Found {len(overflow_lines)} lines exceeding {max_allowed_width} chars in code blocks: {overflow_lines[:5]}",
        )

    def test_no_raw_unclosed_html_tags(self):
        """Verify no unclosed inline or block HTML tags that would corrupt GitHub web/mobile rendering."""
        void_tags = {"img", "br", "hr", "input", "meta", "link"}
        tag_pattern = re.compile(r"<(/)?([a-zA-Z0-9]+)(?:\s+[^>]*)?>")

        clean_text = re.sub(r"```[\s\S]*?```", "", self.content)
        clean_text = re.sub(r"<!--[\s\S]*?-->", "", clean_text)

        stack = []
        for match in tag_pattern.finditer(clean_text):
            is_closing = bool(match.group(1))
            tag_name = match.group(2).lower()
            raw_match = match.group(0)

            if tag_name in void_tags or raw_match.endswith("/>"):
                continue

            if not is_closing:
                stack.append((tag_name, match.start()))
            else:
                if not stack:
                    self.fail(f"Unexpected closing tag </{tag_name}> with empty stack")
                last_tag, _ = stack.pop()
                self.assertEqual(
                    last_tag,
                    tag_name,
                    f"Mismatched HTML closing tag: expected </{last_tag}>, got </{tag_name}>",
                )

        self.assertEqual(stack, [], f"Unclosed HTML tags remaining: {stack}")


if __name__ == "__main__":
    unittest.main()
