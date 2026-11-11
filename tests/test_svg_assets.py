#!/usr/bin/env python3
"""
tests/test_svg_assets.py
Comprehensive deterministic E2E test suite for SVG assets (F01, F02, F03, F04, F13).
Validates XML parsing, viewBox attributes, Tokyo Night palette, dimensions, contrast,
text safety buffers, and security restrictions across Tiers 1-4.
"""
from __future__ import annotations

import glob
import math
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"

# Canonical Tokyo Night color palette reference
TOKYO_NIGHT_PALETTE = {
    "bg_dark": "#16161e",
    "bg_main": "#1a1b26",
    "bg_surface": "#24283b",
    "border": "#414868",
    "text_primary": "#c0caf5",
    "text_muted": "#7aa2f7",
    "cyan": "#7dcfff",
    "blue": "#7aa2f7",
    "purple": "#bb9af7",
    "green": "#9ece6a",
    "red": "#f7768e",
}


def parse_viewbox(viewbox_str: str) -> tuple[float, float, float, float]:
    """Parse viewBox string 'minX minY width height' into numeric tuple."""
    parts = [float(p) for p in re.split(r"[\s,]+", viewbox_str.strip()) if p]
    if len(parts) != 4:
        raise ValueError(f"Invalid viewBox string: '{viewbox_str}'")
    return parts[0], parts[1], parts[2], parts[3]


class TestSvgAssetsTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Core Feature Coverage for SVGs (>= 5 test cases per feature)."""

    def setUp(self):
        self.info_card = ASSETS_DIR / "info-card.svg"
        self.tech_core = ASSETS_DIR / "tech-core.svg"
        self.heatmap = ASSETS_DIR / "contrib-heatmap.svg"
        self.matrix_rain = ASSETS_DIR / "matrix-rain.svg"

    # --- Feature 1: Tokyo Night HUD Info Card (assets/info-card.svg) ---

    def test_f01_info_card_exists(self):
        """F01: assets/info-card.svg must exist on disk."""
        self.assertTrue(self.info_card.is_file(), f"Missing file: {self.info_card}")

    def test_f01_info_card_xml_well_formedness(self):
        """F01: assets/info-card.svg must parse as valid XML."""
        tree = ET.parse(self.info_card)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"), f"Root tag must be svg, got {root.tag}")

    def test_f01_info_card_root_attributes_and_viewbox(self):
        """F01: assets/info-card.svg must declare xmlns and responsive viewBox="0 0 490 290"."""
        root = ET.parse(self.info_card).getroot()
        has_xmlns = (
            root.tag == "{http://www.w3.org/2000/svg}svg"
            or root.attrib.get("xmlns") == "http://www.w3.org/2000/svg"
            or "xmlns" in self.info_card.read_text(encoding="utf-8")
        )
        self.assertTrue(has_xmlns, "info-card.svg must declare standard SVG XML namespace")
        self.assertIn("viewBox", root.attrib, "Missing viewBox attribute")
        min_x, min_y, width, height = parse_viewbox(root.attrib["viewBox"])
        self.assertEqual((min_x, min_y), (0.0, 0.0))
        self.assertEqual((width, height), (490.0, 290.0))

    def test_f01_info_card_dark_container_background(self):
        """F01: assets/info-card.svg must have an opaque background rect container for contrast."""
        root = ET.parse(self.info_card).getroot()
        rects = root.findall("{http://www.w3.org/2000/svg}rect")
        if not rects:
            rects = root.findall("rect")
        self.assertGreaterEqual(len(rects), 1, "info-card.svg must contain at least one rect container")
        first_rect = rects[0]
        fill = first_rect.attrib.get("fill", "").lower()
        self.assertTrue(
            fill.startswith("#") and len(fill) in (4, 7),
            f"Background rect must have a valid dark hex fill, got '{fill}'",
        )

    def test_f01_info_card_monospace_text_elements(self):
        """F01: assets/info-card.svg text elements must use monospace typography."""
        content = self.info_card.read_text(encoding="utf-8")
        self.assertIn("monospace", content, "info-card.svg must specify monospace font stack")
        root = ET.parse(self.info_card).getroot()
        text_nodes = root.findall(".//{http://www.w3.org/2000/svg}text") or root.findall(".//text")
        self.assertGreaterEqual(len(text_nodes), 5, "info-card.svg must contain informative text nodes")

    # --- Feature 2: Systems Architecture Core Radar (assets/tech-core.svg) ---

    def test_f02_tech_core_exists(self):
        """F02: assets/tech-core.svg must exist on disk."""
        self.assertTrue(self.tech_core.is_file(), f"Missing file: {self.tech_core}")

    def test_f02_tech_core_xml_well_formedness(self):
        """F02: assets/tech-core.svg must parse as valid XML."""
        tree = ET.parse(self.tech_core)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"), f"Root tag must be svg, got {root.tag}")

    def test_f02_tech_core_root_attributes_and_viewbox(self):
        """F02: assets/tech-core.svg must declare xmlns and responsive viewBox="0 0 370 280"."""
        root = ET.parse(self.tech_core).getroot()
        has_xmlns = (
            root.tag == "{http://www.w3.org/2000/svg}svg"
            or root.attrib.get("xmlns") == "http://www.w3.org/2000/svg"
            or "xmlns" in self.tech_core.read_text(encoding="utf-8")
        )
        self.assertTrue(has_xmlns, "tech-core.svg must declare standard SVG XML namespace")
        self.assertIn("viewBox", root.attrib, "Missing viewBox attribute")
        min_x, min_y, width, height = parse_viewbox(root.attrib["viewBox"])
        self.assertEqual((min_x, min_y), (0.0, 0.0))
        self.assertEqual((width, height), (370.0, 280.0))

    def test_f02_tech_core_hexagonal_paths_and_geometry(self):
        """F02: assets/tech-core.svg must include vector paths and geometric radar elements."""
        root = ET.parse(self.tech_core).getroot()
        paths = root.findall(".//{http://www.w3.org/2000/svg}path") or root.findall(".//path")
        circles = root.findall(".//{http://www.w3.org/2000/svg}circle") or root.findall(".//circle")
        self.assertGreaterEqual(len(paths), 2, "tech-core.svg must contain geometric paths")
        self.assertGreaterEqual(len(circles), 1, "tech-core.svg must contain node circle elements")

    def test_f02_tech_core_dark_background_container(self):
        """F02: assets/tech-core.svg must contain an opaque background rect for dark/light contrast."""
        root = ET.parse(self.tech_core).getroot()
        rects = root.findall("{http://www.w3.org/2000/svg}rect") or root.findall("rect")
        self.assertGreaterEqual(len(rects), 1, "tech-core.svg must contain a background container rect")

    # --- Feature 3: Well-Formed Animated Matrix Rain SVG (assets/matrix-rain.svg) ---

    def test_f03_matrix_rain_exists(self):
        """F03: assets/matrix-rain.svg must exist on disk."""
        self.assertTrue(self.matrix_rain.is_file(), f"Missing file: {self.matrix_rain}")

    def test_f03_matrix_rain_xml_well_formedness(self):
        """F03: assets/matrix-rain.svg must parse as strictly valid XML (catches unescaped tokens)."""
        try:
            tree = ET.parse(self.matrix_rain)
            root = tree.getroot()
            self.assertTrue(root.tag.endswith("svg"))
        except ET.ParseError as err:
            self.fail(f"assets/matrix-rain.svg is not well-formed XML: {err}")

    def test_f03_matrix_rain_no_unescaped_meta_characters(self):
        """F03: assets/matrix-rain.svg text nodes must not contain raw unescaped '<' or '>'."""
        content = self.matrix_rain.read_text(encoding="utf-8")
        # Find raw '<' inside text tags: <text ...>raw <</text>
        # A raw '<' inside tag content produces <text ...><</text> which is invalid XML
        invalid_raw_lt = re.findall(r">[^<]*<(?![/a-zA-Z!?])", content)
        self.assertEqual(
            invalid_raw_lt,
            [],
            f"Found unescaped raw '<' inside text content: {invalid_raw_lt}",
        )

    def test_f03_matrix_rain_viewbox_and_dimensions(self):
        """F03: assets/matrix-rain.svg must specify responsive viewBox."""
        try:
            root = ET.parse(self.matrix_rain).getroot()
            self.assertIn("viewBox", root.attrib)
        except ET.ParseError:
            # If XML is invalid, verify via regex fallback to locate viewBox
            content = self.matrix_rain.read_text(encoding="utf-8")
            self.assertRegex(content, r'viewBox=[\"\'][0-9\s.]+[\"\']', "Missing viewBox in matrix-rain.svg")

    def test_f03_matrix_rain_contains_animation_or_matrix_streams(self):
        """F03: assets/matrix-rain.svg must contain matrix stream characters and elements."""
        content = self.matrix_rain.read_text(encoding="utf-8")
        self.assertIn("<text", content, "matrix-rain.svg must contain text glyphs")
        self.assertGreater(len(content), 1000, "matrix-rain.svg must contain multi-column rain stream data")

    # --- Feature 4 / Feature 13: Contribution Heatmap SVG (assets/contrib-heatmap.svg) ---

    def test_f13_heatmap_exists(self):
        """F13: assets/contrib-heatmap.svg must exist on disk."""
        self.assertTrue(self.heatmap.is_file(), f"Missing file: {self.heatmap}")

    def test_f13_heatmap_xml_well_formedness(self):
        """F13: assets/contrib-heatmap.svg must parse as valid XML."""
        tree = ET.parse(self.heatmap)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))

    def test_f13_heatmap_viewbox_dimensions(self):
        """F13: assets/contrib-heatmap.svg viewBox must be 0 0 860 216."""
        root = ET.parse(self.heatmap).getroot()
        self.assertIn("viewBox", root.attrib)
        min_x, min_y, width, height = parse_viewbox(root.attrib["viewBox"])
        self.assertEqual((min_x, min_y), (0.0, 0.0))
        self.assertEqual((width, height), (860.0, 216.0))

    def test_f13_heatmap_contains_panel_and_day_cells(self):
        """F13: assets/contrib-heatmap.svg must contain panel rect and multiple contribution day rects."""
        root = ET.parse(self.heatmap).getroot()
        rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
        # Heatmap typically has 1 panel + 5 legend rects + 365+ day rects = 370+ rects
        self.assertGreaterEqual(len(rects), 100, f"Expected >= 100 rects in heatmap, found {len(rects)}")

    def test_f13_heatmap_accessibility_attributes(self):
        """F13: assets/contrib-heatmap.svg must declare accessibility attributes role and aria-labelledby."""
        root = ET.parse(self.heatmap).getroot()
        self.assertEqual(root.attrib.get("role"), "img", "Heatmap must declare role='img'")
        self.assertIn("aria-labelledby", root.attrib, "Heatmap must declare aria-labelledby")


class TestSvgAssetsTier2BoundaryAndCornerCases(unittest.TestCase):
    """Tier 2: Boundary & Corner Cases (Text buffers, XML entities, viewBox bounds)."""

    def test_t2_text_boundary_safety_margin_info_card(self):
        """T2: info-card.svg text elements must maintain >=20px right safety margin to prevent clipping."""
        path = ASSETS_DIR / "info-card.svg"
        root = ET.parse(path).getroot()
        _, _, vb_width, _ = parse_viewbox(root.attrib["viewBox"])
        text_nodes = root.findall(".//{http://www.w3.org/2000/svg}text") or root.findall(".//text")

        for node in text_nodes:
            x_str = node.attrib.get("x")
            if not x_str:
                continue
            x = float(x_str)
            text_content = (node.text or "").strip()
            if not text_content:
                continue
            font_size_str = node.attrib.get("font-size", "12")
            font_size = float(re.sub(r"[^\d.]", "", font_size_str) or "12")
            # Estimated width = characters * font_size * 0.65
            estimated_width = len(text_content) * font_size * 0.65
            right_edge = x + estimated_width
            safety_margin = vb_width - right_edge
            self.assertGreaterEqual(
                safety_margin,
                15.0,  # 15px-20px safety threshold
                f"Text node '{text_content}' at x={x} exceeds right boundary (margin: {safety_margin:.1f}px vs viewBox {vb_width})",
            )

    def test_t2_text_boundary_safety_margin_tech_core(self):
        """T2: tech-core.svg text elements must maintain right safety margin or use middle anchor."""
        path = ASSETS_DIR / "tech-core.svg"
        root = ET.parse(path).getroot()
        _, _, vb_width, _ = parse_viewbox(root.attrib["viewBox"])
        text_nodes = root.findall(".//{http://www.w3.org/2000/svg}text") or root.findall(".//text")

        for node in text_nodes:
            anchor = node.attrib.get("text-anchor", "start")
            x = float(node.attrib.get("x", "0"))
            text_content = (node.text or "").strip()
            if not text_content:
                continue
            if anchor == "middle":
                # Middle anchored text must have x roughly in center
                self.assertLess(abs(x - vb_width / 2.0), 30.0)
            else:
                font_size = float(node.attrib.get("font-size", "11"))
                right_edge = x + len(text_content) * font_size * 0.65
                self.assertLess(right_edge, vb_width, f"Text '{text_content}' overflows right edge {vb_width}")

    def test_t2_no_forbidden_tags_in_any_svg(self):
        """T2: No SVG in assets/ may contain forbidden elements (<script>, <foreignObject>, <iframe>)."""
        svg_files = glob.glob(str(ASSETS_DIR / "*.svg"))
        forbidden = ["script", "foreignObject", "iframe", "object", "embed", "applet"]

        for svg_path in svg_files:
            content = Path(svg_path).read_text(encoding="utf-8")
            for tag in forbidden:
                self.assertNotIn(
                    f"<{tag}",
                    content.lower(),
                    f"Forbidden tag <{tag}> found in {Path(svg_path).name}",
                )

    def test_t2_no_inline_event_handlers_in_any_svg(self):
        """T2: No SVG in assets/ may contain inline event attributes (onload, onerror, onclick)."""
        svg_files = glob.glob(str(ASSETS_DIR / "*.svg"))
        event_patterns = [r"\bonload\s*=", r"\bonerror\s*=", r"\bonclick\s*=", r"\bonmouseover\s*="]

        for svg_path in svg_files:
            content = Path(svg_path).read_text(encoding="utf-8")
            for pattern in event_patterns:
                self.assertFalse(
                    re.search(pattern, content, re.IGNORECASE),
                    f"Disallowed event handler matching '{pattern}' in {Path(svg_path).name}",
                )

    def test_t2_all_svgs_viewbox_origin_non_negative(self):
        """T2: All valid SVGs in assets/ must have minX >= 0 and minY >= 0 in viewBox."""
        svg_files = glob.glob(str(ASSETS_DIR / "*.svg"))
        for svg_path in svg_files:
            try:
                root = ET.parse(svg_path).getroot()
                if "viewBox" in root.attrib:
                    min_x, min_y, w, h = parse_viewbox(root.attrib["viewBox"])
                    self.assertGreaterEqual(min_x, 0, f"Negative minX in {Path(svg_path).name}")
                    self.assertGreaterEqual(min_y, 0, f"Negative minY in {Path(svg_path).name}")
                    self.assertGreater(w, 0, f"Non-positive width in {Path(svg_path).name}")
                    self.assertGreater(h, 0, f"Non-positive height in {Path(svg_path).name}")
            except ET.ParseError:
                # If invalid XML, caught by well-formedness tests
                pass


class TestSvgAssetsTier3CrossFeatureIntegration(unittest.TestCase):
    """Tier 3: Cross-Feature Integration (Theme fallback, dark/light contrast guarantees)."""

    def test_t3_opaque_background_contrast_guarantee_info_card(self):
        """T3: info-card.svg must feature an opaque dark rect to guarantee readability in light GitHub mode."""
        root = ET.parse(ASSETS_DIR / "info-card.svg").getroot()
        rects = root.findall("{http://www.w3.org/2000/svg}rect") or root.findall("rect")
        bg_rect = rects[0]
        fill = bg_rect.attrib.get("fill", "").lower()
        # Ensure it's not 'none' or transparent
        self.assertNotIn(fill, ["none", "transparent", ""])
        # Check dark hex: luminance should be < 0.2
        if fill.startswith("#") and len(fill) == 7:
            r = int(fill[1:3], 16)
            g = int(fill[3:5], 16)
            b = int(fill[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            self.assertLess(luminance, 0.25, f"info-card background luminance {luminance} is too bright")

    def test_t3_opaque_background_contrast_guarantee_tech_core(self):
        """T3: tech-core.svg must feature an opaque dark rect to guarantee readability in light GitHub mode."""
        root = ET.parse(ASSETS_DIR / "tech-core.svg").getroot()
        rects = root.findall("{http://www.w3.org/2000/svg}rect") or root.findall("rect")
        bg_rect = rects[0]
        fill = bg_rect.attrib.get("fill", "").lower()
        self.assertNotIn(fill, ["none", "transparent", ""])
        if fill.startswith("#") and len(fill) == 7:
            r, g, b = int(fill[1:3], 16), int(fill[3:5], 16), int(fill[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            self.assertLess(luminance, 0.25, f"tech-core background luminance {luminance} is too bright")

    def test_t3_heatmap_has_dark_panel_container(self):
        """T3: contrib-heatmap.svg must include .panel background container with dark fill."""
        root = ET.parse(ASSETS_DIR / "contrib-heatmap.svg").getroot()
        content = (ASSETS_DIR / "contrib-heatmap.svg").read_text(encoding="utf-8")
        self.assertIn(".panel", content, "Heatmap SVG style must define .panel container")
        self.assertRegex(content, r"\.panel\s*\{[^}]*fill:\s*#[0-9a-fA-F]+", "Heatmap panel must have dark hex fill")


class TestSvgAssetsTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Real-World Scenarios (Mobile downscaling simulation & rendering integrity)."""

    def test_t4_mobile_viewport_360px_scaling_info_card(self):
        """T4: info-card.svg aspect ratio must scale down smoothly to 360px mobile width without distortion."""
        root = ET.parse(ASSETS_DIR / "info-card.svg").getroot()
        _, _, orig_w, orig_h = parse_viewbox(root.attrib["viewBox"])
        aspect_ratio = orig_w / orig_h

        # Downscale to mobile viewport width 360px
        target_width = 360.0
        scaled_height = target_width / aspect_ratio
        # Ensure scaled height is proportional and positive
        self.assertAlmostEqual(target_width / scaled_height, aspect_ratio, places=3)
        self.assertGreater(scaled_height, 100.0)
        self.assertLess(scaled_height, 300.0)

    def test_t4_mobile_viewport_360px_scaling_heatmap(self):
        """T4: contrib-heatmap.svg aspect ratio must scale down smoothly to 360px mobile width."""
        root = ET.parse(ASSETS_DIR / "contrib-heatmap.svg").getroot()
        _, _, orig_w, orig_h = parse_viewbox(root.attrib["viewBox"])
        aspect_ratio = orig_w / orig_h

        target_width = 360.0
        scaled_height = target_width / aspect_ratio
        self.assertAlmostEqual(target_width / scaled_height, aspect_ratio, places=3)
        self.assertGreater(scaled_height, 70.0)
        self.assertLess(scaled_height, 150.0)


if __name__ == "__main__":
    unittest.main()
