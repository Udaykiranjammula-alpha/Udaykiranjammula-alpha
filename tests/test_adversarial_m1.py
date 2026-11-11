#!/usr/bin/env python3
"""
tests/test_adversarial_m1.py
Adversarial challenge test suite for Milestone 1 (Visual Branding and Tokyo Night HUD Assets).
Evaluates stress conditions, boundary overflows, font metrics under wide monospace rendering,
corrupted inputs, XML parsing resilience, and Camo sanitization safety.
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
SCRIPTS_DIR = ROOT / "scripts"
DATA_DIR = ROOT / "data"


class TestHeatmapStressAndBounds(unittest.TestCase):
    """Stress tests and boundary checks for scripts/render_heatmap.py and assets/contrib-heatmap.svg."""

    def setUp(self):
        self.render_script = SCRIPTS_DIR / "render_heatmap.py"
        self.heatmap_svg = ASSETS_DIR / "contrib-heatmap.svg"

    def _run_renderer(self, payload: dict | str) -> tuple[int, str, str, Path]:
        """Helper to run render_heatmap.py with given payload and return (code, stdout, stderr, out_path)."""
        tmp_in = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
        if isinstance(payload, str):
            tmp_in.write(payload)
        else:
            json.dump(payload, tmp_in)
        tmp_in.close()
        in_path = Path(tmp_in.name)

        tmp_out = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".svg", delete=False)
        tmp_out.close()
        out_path = Path(tmp_out.name)

        try:
            proc = subprocess.run(
                [sys.executable, str(self.render_script), "--input", str(in_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return proc.returncode, proc.stdout, proc.stderr, out_path
        finally:
            in_path.unlink(missing_ok=True)

    def test_heatmap_rejects_empty_dict(self):
        """Stress test: Empty JSON object {} must be rejected cleanly (exit code 1)."""
        code, _, stderr, out_path = self._run_renderer({})
        out_path.unlink(missing_ok=True)
        self.assertEqual(code, 1, f"Expected returncode 1, got {code}. stderr: {stderr}")

    def test_heatmap_rejects_corrupted_json_syntax(self):
        """Stress test: Malformed JSON syntax must be rejected cleanly."""
        code, _, stderr, out_path = self._run_renderer('{"username": "test", "days": [')
        out_path.unlink(missing_ok=True)
        self.assertEqual(code, 1, f"Expected returncode 1, got {code}. stderr: {stderr}")

    def test_heatmap_rejects_missing_days_field(self):
        """Stress test: Missing 'days' key must be rejected cleanly."""
        code, _, stderr, out_path = self._run_renderer({"username": "test"})
        out_path.unlink(missing_ok=True)
        self.assertEqual(code, 1, f"Expected returncode 1, got {code}. stderr: {stderr}")

    def test_heatmap_rejects_empty_days_list(self):
        """Stress test: Empty days list [] must be rejected cleanly."""
        code, _, stderr, out_path = self._run_renderer({"username": "test", "days": []})
        out_path.unlink(missing_ok=True)
        self.assertEqual(code, 1, f"Expected returncode 1, got {code}. stderr: {stderr}")

    def test_heatmap_rejects_invalid_date_format_and_values(self):
        """Stress test: Invalid date formats and non-existent dates (e.g. 2024-02-30) must be rejected."""
        invalid_dates = ["2024-02-30", "01/01/2024", "not-a-date", "2024-13-01", ""]
        for bad_date in invalid_dates:
            code, _, _, out_path = self._run_renderer({"username": "test", "days": [{"date": bad_date, "count": 1}]})
            out_path.unlink(missing_ok=True)
            self.assertEqual(code, 1, f"Expected rejection for date '{bad_date}'")

    def test_heatmap_rejects_negative_or_non_integer_counts(self):
        """Stress test: Negative counts, floats, and string counts must be rejected."""
        bad_counts = [-1, -999, 1.5, "5", None]
        for bad_count in bad_counts:
            code, _, _, out_path = self._run_renderer(
                {"username": "test", "days": [{"date": "2024-01-01", "count": bad_count}]}
            )
            out_path.unlink(missing_ok=True)
            self.assertEqual(code, 1, f"Expected rejection for count '{bad_count}'")

    def test_heatmap_rejects_duplicate_dates(self):
        """Stress test: Duplicate dates within the days list must be rejected."""
        payload = {
            "username": "test",
            "days": [
                {"date": "2024-01-01", "count": 1},
                {"date": "2024-01-01", "count": 2},
            ],
        }
        code, _, _, out_path = self._run_renderer(payload)
        out_path.unlink(missing_ok=True)
        self.assertEqual(code, 1, "Duplicate dates must be rejected")

    def test_heatmap_zero_commits_all_days(self):
        """Boundary test: 0 commits across all days must render valid SVG without division by zero."""
        payload = {
            "username": "zero_user",
            "days": [
                {"date": "2024-01-01", "count": 0},
                {"date": "2024-01-02", "count": 0},
                {"date": "2024-01-03", "count": 0},
            ],
        }
        code, _, stderr, out_path = self._run_renderer(payload)
        try:
            self.assertEqual(code, 0, f"Renderer failed on all zero counts: {stderr}")
            root = ET.parse(out_path).getroot()
            self.assertTrue(root.tag.endswith("svg"))
            # All day rects should have level-0
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
            day_rects = [r for r in rects if "day" in r.attrib.get("class", "")]
            self.assertGreaterEqual(len(day_rects), 3)
            for r in day_rects:
                self.assertIn("level-0", r.attrib.get("class", ""))
        finally:
            out_path.unlink(missing_ok=True)

    def test_heatmap_leap_year_boundary(self):
        """Boundary test: Leap year day (Feb 29) must render cleanly."""
        payload = {
            "username": "leap_user",
            "days": [
                {"date": "2024-02-28", "count": 2},
                {"date": "2024-02-29", "count": 10},
                {"date": "2024-03-01", "count": 4},
            ],
        }
        code, _, stderr, out_path = self._run_renderer(payload)
        try:
            self.assertEqual(code, 0, f"Failed on leap year data: {stderr}")
            root = ET.parse(out_path).getroot()
            self.assertTrue(root.tag.endswith("svg"))
            leap_rects = [r for r in root.iter("{http://www.w3.org/2000/svg}rect") if r.attrib.get("data-date") == "2024-02-29"]
            self.assertEqual(len(leap_rects), 1)
            self.assertIn("level-4", leap_rects[0].attrib.get("class", ""))
        finally:
            out_path.unlink(missing_ok=True)

    def test_heatmap_xml_escaping_in_username(self):
        """Security test: Special XML characters in username must be escaped properly."""
        payload = {
            "username": "uday<script>&'\"",
            "days": [{"date": "2024-01-01", "count": 5}],
        }
        code, _, stderr, out_path = self._run_renderer(payload)
        try:
            self.assertEqual(code, 0, f"Failed to escape special username characters: {stderr}")
            content = out_path.read_text(encoding="utf-8")
            self.assertNotIn("<script>", content)
            root = ET.parse(out_path).getroot()
            title = root.find(".//{http://www.w3.org/2000/svg}title")
            self.assertIsNotNone(title)
            self.assertIn("uday<script>&'\"", title.text or "")
        finally:
            out_path.unlink(missing_ok=True)

    def test_heatmap_cells_do_not_overflow_viewbox(self):
        """Boundary test: All rendered cells in contrib-heatmap.svg must remain within viewBox boundary."""
        self.assertTrue(self.heatmap_svg.is_file(), f"Missing {self.heatmap_svg}")
        root = ET.parse(self.heatmap_svg).getroot()
        vb_parts = [float(p) for p in root.attrib["viewBox"].split()]
        vb_width = vb_parts[2]

        overflowing_elements = []
        for elem in root.iter("{http://www.w3.org/2000/svg}rect"):
            if "x" in elem.attrib and "width" in elem.attrib:
                x = float(elem.attrib["x"])
                w = float(elem.attrib["width"])
                right_edge = x + w
                if right_edge > vb_width:
                    overflowing_elements.append((elem.attrib.get("class"), elem.attrib.get("data-date"), right_edge))

        self.assertEqual(
            overflowing_elements,
            [],
            f"Found {len(overflowing_elements)} elements overflowing viewBox width ({vb_width}px): {overflowing_elements}",
        )


class TestFontMetricsAndBoundaryOverflow(unittest.TestCase):
    """Stress tests font metrics and right boundary margins across standard and wide monospace rendering."""

    def setUp(self):
        self.info_card = ASSETS_DIR / "info-card.svg"
        self.tech_core = ASSETS_DIR / "tech-core.svg"

    def _check_text_margins(self, svg_path: Path, char_ratio: float, min_margin: float):
        """Helper to calculate safety margin across all text elements given character width ratio."""
        root = ET.parse(svg_path).getroot()
        vb = [float(p) for p in root.attrib["viewBox"].split()]
        vb_width = vb[2]

        overflows = []
        for node in root.iter("{http://www.w3.org/2000/svg}text"):
            text = (node.text or "").strip()
            if not text:
                continue
            x = float(node.attrib.get("x", 0))
            anchor = node.attrib.get("text-anchor", "start")
            fs_str = node.attrib.get("font-size", "11")
            font_size = float(re.sub(r"[^\d.]", "", fs_str) or "11")

            estimated_width = len(text) * font_size * char_ratio
            if anchor == "middle":
                right_edge = x + estimated_width / 2.0
                left_edge = x - estimated_width / 2.0
                margin = min(x - left_edge, vb_width - right_edge)
            elif anchor == "end":
                right_edge = x
                margin = vb_width - right_edge
            else:  # start
                right_edge = x + estimated_width
                margin = vb_width - right_edge

            if margin < min_margin:
                overflows.append({
                    "text": text[:35],
                    "x": x,
                    "anchor": anchor,
                    "font_size": font_size,
                    "estimated_right": right_edge,
                    "margin": margin,
                    "viewBox_width": vb_width,
                })
        return overflows

    def test_info_card_standard_monospace_margins(self):
        """Verify info-card.svg maintains >= 15px margin under standard monospace ratio 0.65."""
        overflows = self._check_text_margins(self.info_card, char_ratio=0.65, min_margin=15.0)
        self.assertEqual(overflows, [], f"info-card.svg has insufficient safety margins at ratio 0.65: {overflows}")

    def test_info_card_wide_monospace_stress(self):
        """Stress test: info-card.svg under wide monospace font rendering (ratio 0.70 - 0.72)."""
        # Under wide monospace (ratio 0.70), elements must not clip past the viewBox width (margin >= 0)
        overflows = self._check_text_margins(self.info_card, char_ratio=0.70, min_margin=0.0)
        self.assertEqual(overflows, [], f"info-card.svg clips text under wide monospace ratio 0.70: {overflows}")

    def test_tech_core_standard_monospace_margins(self):
        """Verify tech-core.svg text maintains positive margins under ratio 0.65."""
        overflows = self._check_text_margins(self.tech_core, char_ratio=0.65, min_margin=5.0)
        self.assertEqual(overflows, [], f"tech-core.svg overflows right boundary at ratio 0.65: {overflows}")

    def test_tech_core_wide_monospace_stress(self):
        """Stress test: tech-core.svg under wide monospace rendering (ratio 0.70)."""
        overflows = self._check_text_margins(self.tech_core, char_ratio=0.70, min_margin=0.0)
        self.assertEqual(overflows, [], f"tech-core.svg clips text under wide monospace ratio 0.70: {overflows}")


class TestXmlParsingResilienceAndCamo(unittest.TestCase):
    """Stress tests XML parser resilience and GitHub Camo sanitization compatibility."""

    def test_all_svgs_strict_xml_parse(self):
        """All SVGs in assets/ must parse strictly without errors or unescaped entities."""
        svg_files = glob.glob(str(ASSETS_DIR / "*.svg"))
        self.assertGreaterEqual(len(svg_files), 4)
        for svg_path in svg_files:
            try:
                tree = ET.parse(svg_path)
                root = tree.getroot()
                self.assertTrue(root.tag.endswith("svg"), f"Root tag not svg in {Path(svg_path).name}")
            except ET.ParseError as err:
                self.fail(f"XML parse failure in {Path(svg_path).name}: {err}")

    def test_camo_disallowed_tags_and_protocols(self):
        """GitHub Camo proxy strips unsafe tags, remote protocols, and unneeded external assets."""
        svg_files = glob.glob(str(ASSETS_DIR / "*.svg"))
        disallowed_tags = ["script", "foreignobject", "iframe", "object", "embed", "applet", "link"]
        disallowed_attrs = ["onload", "onerror", "onclick", "onmouseover", "onfocus", "onblur"]

        for svg_path in svg_files:
            content = Path(svg_path).read_text(encoding="utf-8").lower()
            for tag in disallowed_tags:
                self.assertNotIn(f"<{tag}", content, f"Disallowed tag <{tag}> in {Path(svg_path).name}")
            for attr in disallowed_attrs:
                self.assertNotIn(f"{attr}=", content, f"Disallowed attribute '{attr}' in {Path(svg_path).name}")
            # Ensure no external URLs are loaded via <image href="...">
            self.assertNotIn("href=\"http://", content)
            self.assertNotIn("href=\"https://", content)
            self.assertNotIn("xlink:href=\"http://", content)
            self.assertNotIn("xlink:href=\"https://", content)

    def test_matrix_rain_generator_deterministic_xml(self):
        """Verify that gen_rain.ps1 generates valid XML without unescaped tokens."""
        # Check current matrix-rain.svg
        matrix_path = ASSETS_DIR / "matrix-rain.svg"
        self.assertTrue(matrix_path.is_file())
        tree = ET.parse(matrix_path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))
        # Ensure no raw unescaped '<' or '&' exist in text content
        raw_content = matrix_path.read_text(encoding="utf-8")
        raw_lt_matches = re.findall(r">[^<]*<(?![/a-zA-Z!?])", raw_content)
        self.assertEqual(raw_lt_matches, [], f"Raw unescaped '<' detected in matrix-rain.svg: {raw_lt_matches}")


if __name__ == "__main__":
    unittest.main()
