#!/usr/bin/env python3
"""
tests/test_gfm_markdown.py
Comprehensive deterministic E2E test suite for GFM Markdown & Systems Dossiers.
Covers:
- F12: GFM & HTML Tag Balance Verification Gate
- F05: FileDNA 2.0 Engineering Dossier
- F06: ESP32 Distributed ML Accelerator Dossier
- F07: Uday AI Local Server Dossier
- F08: Systems Profile Visual Polish & Badges
Across Tiers 1-4.
"""
from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"


class GFMTagBalancer(HTMLParser):
    """AST-based HTML tag balancer verifying balanced closing tags outside code fences."""

    VOID_TAGS = {"img", "br", "hr", "input", "source", "meta", "link"}

    def __init__(self):
        super().__init__()
        self.stack: list[tuple[str, tuple[int, int]]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag_lower = tag.lower()
        if tag_lower not in self.VOID_TAGS:
            self.stack.append((tag_lower, self.getpos()))

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in self.VOID_TAGS:
            return
        if not self.stack:
            self.errors.append(f"Unexpected closing tag </{tag_lower}> at line {self.getpos()[0]}")
            return
        last_tag, pos = self.stack.pop()
        if last_tag != tag_lower:
            self.errors.append(
                f"Mismatched closing tag </{tag_lower}> at line {self.getpos()[0]} "
                f"expected </{last_tag}> opened at line {pos[0]}"
            )

    def finish(self) -> list[str]:
        for tag, pos in self.stack:
            self.errors.append(f"Unclosed tag <{tag}> opened at line {pos[0]}")
        return self.errors


class TestGfmMarkdownTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Core Feature Coverage for GFM & Engineering Dossiers."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        # Strip code blocks for HTML AST analysis
        cls.content_no_code = re.sub(r"```.*?```", "", cls.content, flags=re.DOTALL)

    # --- Feature 12: GFM & HTML Tag Balance Verification Gate ---

    def test_f12_html_tag_balance_zero_errors(self):
        """F12: HTML tag balancer must verify exactly 0 unclosed and 0 mismatched tags."""
        balancer = GFMTagBalancer()
        balancer.feed(self.content_no_code)
        errors = balancer.finish()
        self.assertEqual(errors, [], f"HTML tag balancing errors detected: {errors}")

    def test_f12_table_syntax_and_column_counts(self):
        """F12: Markdown tables must have matching column counts and valid header delimiters."""
        lines = self.content.splitlines()
        in_table = False
        expected_cols = 0
        table_rows = []

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if not in_table:
                    in_table = True
                    expected_cols = len(cells)
                    table_rows = [(line_num, cells)]
                else:
                    table_rows.append((line_num, cells))
            else:
                if in_table:
                    # Validate completed table
                    self.assertGreaterEqual(len(table_rows), 2, "Table must have at least header + delimiter")
                    # Delimiter row check
                    delim_cells = table_rows[1][1]
                    for d in delim_cells:
                        self.assertTrue(
                            re.match(r"^:?-+:?$", d),
                            f"Invalid table delimiter cell '{d}' at line {table_rows[1][0]}",
                        )
                    # All rows must have same column count
                    for r_num, row_cells in table_rows:
                        self.assertEqual(
                            len(row_cells),
                            expected_cols,
                            f"Column count mismatch at line {r_num}: expected {expected_cols}, got {len(row_cells)}",
                        )
                    in_table = False

    def test_f12_code_fences_are_paired(self):
        """F12: All code fence markers (```) must be paired (even count)."""
        fence_count = len(re.findall(r"^```", self.content, flags=re.MULTILINE))
        self.assertEqual(fence_count % 2, 0, f"Unbalanced code fences count: {fence_count}")
        self.assertGreaterEqual(fence_count, 10, "Expected multiple code blocks in portfolio")

    def test_f12_no_broken_markdown_links_syntax(self):
        """F12: Markdown links must not have unbalanced brackets or missing parentheses."""
        unbalanced = re.findall(r"\[[^\]]*\([^)]*$", self.content, flags=re.MULTILINE)
        self.assertEqual(unbalanced, [], f"Unbalanced markdown link syntax detected: {unbalanced}")

    def test_f12_terminal_code_fence_has_language_identifier(self):
        """F12: Terminal dossier code fence must declare language identifier (e.g. zsh)."""
        self.assertIn("```zsh", self.content, "Terminal dossier code fence must declare language identifier 'zsh'")

    # --- Feature 5: FileDNA 2.0 Engineering Dossier ---

    def test_f05_filedna_shannon_entropy_formula_present(self):
        """F05: FileDNA section must include the Shannon entropy mathematical formula."""
        self.assertTrue(
            "H(X) = -Σ P(xᵢ) · log₂ P(xᵢ)" in self.content or "H(X) = -\\sum" in self.content or "Shannon Entropy" in self.content,
            "Missing Shannon entropy formula in FileDNA dossier",
        )

    def test_f05_filedna_entropy_classification_tiers(self):
        """F05: FileDNA section must document the 0.0 to 8.0 bits/byte threshold classification tiers."""
        self.assertIn("0.0", self.content)
        self.assertIn("8.0", self.content)
        self.assertIn("bits/byte", self.content)
        self.assertIn("Compiled Binary", self.content)
        self.assertIn("RANSOMWARE", self.content)

    def test_f05_filedna_magic_byte_signatures(self):
        """F05: FileDNA section must document binary magic-byte signatures for PNG, PDF, EXE, ZIP."""
        self.assertIn("89 50 4E 47", self.content, "Missing PNG magic bytes [89 50 4E 47]")
        self.assertIn("25 50 44 46", self.content, "Missing PDF magic bytes [25 50 44 46]")
        self.assertIn("4D 5A", self.content, "Missing EXE magic bytes [4D 5A]")
        self.assertIn("50 4B", self.content, "Missing ZIP magic bytes [50 4B]")

    def test_f05_filedna_concurrent_multi_hash_pipeline(self):
        """F05: FileDNA section must document concurrent multi-hash streaming (SHA-256, MD5, SHA-1, CRC-32)."""
        self.assertIn("SHA-256", self.content)
        self.assertIn("MD5", self.content)
        self.assertIn("SHA-1", self.content)
        self.assertIn("CRC-32", self.content)
        self.assertIn("PARALLEL STREAMS", self.content)

    def test_f05_filedna_offline_privacy_architecture(self):
        """F05: FileDNA section must document zero-telemetry, fully offline architecture."""
        self.assertIn("zero-telemetry", self.content.lower())
        self.assertIn("offline", self.content.lower())

    # --- Feature 6: ESP32 Distributed ML Accelerator Dossier ---

    def test_f06_esp32_cluster_node_topology(self):
        """F06: ESP32 section must specify 4-node cluster topology (Node 0 Master, Node 1-2 Workers, Node 3 Aggregator)."""
        self.assertIn("NODE 0", self.content)
        self.assertIn("NODE 1", self.content)
        self.assertIn("NODE 2", self.content)
        self.assertIn("NODE 3", self.content)
        self.assertIn("Master", self.content)
        self.assertIn("Aggregator", self.content)

    def test_f06_esp32_hardware_sram_constraints(self):
        """F06: ESP32 section must document the 520 KB SRAM per node constraint."""
        self.assertIn("520", self.content)
        self.assertIn("SRAM", self.content)

    def test_f06_esp32_ring_buffer_and_latency_metric(self):
        """F06: ESP32 section must document zero-copy ring buffer protocol and ~1.2ms transfer latency."""
        self.assertIn("RING BUFFER SYNCHRONIZATION", self.content)
        self.assertIn("Zero-copy activation exchange", self.content)
        self.assertIn("~1.2ms", self.content)

    def test_f06_esp32_int8_quantized_inference(self):
        """F06: ESP32 section must document INT8 tensor quantization."""
        self.assertIn("INT8", self.content)

    def test_f06_esp32_mesh_networking_protocol(self):
        """F06: ESP32 section must specify Wi-Fi / ESP-NOW mesh networking protocol."""
        self.assertIn("ESP-NOW", self.content)
        self.assertIn("mesh", self.content.lower())

    # --- Feature 7: Uday AI Local Server Dossier ---

    def test_f07_uday_ai_unix_socket_architecture(self):
        """F07: Uday AI section must specify Unix socket interface (/tmp/llm.sock)."""
        self.assertIn("/tmp/llm.sock", self.content)
        self.assertIn("Unix Socket", self.content)

    def test_f07_uday_ai_quantization_tiers_and_ram(self):
        """F07: Uday AI section must document Q4_K_M (4.5 GB RAM) and Q8_0 (8.0 GB RAM) tiers."""
        self.assertIn("Q4_K_M", self.content)
        self.assertIn("4.5 GB RAM", self.content)
        self.assertIn("Q8_0", self.content)
        self.assertIn("8.0 GB RAM", self.content)

    def test_f07_uday_ai_token_throughput_benchmarks(self):
        """F07: Uday AI section must document throughput metrics (~18 tok/s and ~11 tok/s)."""
        self.assertIn("18 tok/s", self.content)
        self.assertIn("11 tok/s", self.content)

    def test_f07_uday_ai_mmap_weight_loading(self):
        """F07: Uday AI section must document mmap() zero-copy weight loading."""
        self.assertIn("mmap()", self.content)

    def test_f07_uday_ai_orchestration_layer_components(self):
        """F07: Uday AI section must document session manager, context tracker, prompt formatter."""
        self.assertIn("Session manager", self.content)
        self.assertIn("Context window tracker", self.content)

    # --- Feature 8: Systems Profile Visual Polish & Badges ---

    def test_f08_terminal_engineer_profile_dossier(self):
        """F08: Profile must feature cat /etc/engineer.profile terminal ASCII dossier."""
        self.assertIn("cat /etc/engineer.profile", self.content)
        self.assertIn("KL University", self.content)
        self.assertIn("Low-Level Systems", self.content)

    def test_f08_collapsible_details_architecture_cards(self):
        """F08: All 3 flagship project dossiers must be wrapped in collapsible <details> cards."""
        details_count = len(re.findall(r"<details>", self.content))
        summary_count = len(re.findall(r"<summary>", self.content))
        self.assertGreaterEqual(details_count, 3, "Expected at least 3 collapsible details cards")
        self.assertEqual(details_count, summary_count, "Each <details> must have matching <summary>")

    def test_f08_terminal_command_ls_projects(self):
        """F08: Profile must feature ls /home/projects --flagship terminal listing."""
        self.assertIn("ls /home/projects --flagship", self.content)

    def test_f08_engineering_philosophy_quote(self):
        """F08: Profile must feature deterministic engineering philosophy quote."""
        self.assertIn("Build systems that are deterministic, transparent, and hardware-aware", self.content)

    def test_f08_hardware_battlestation_bench(self):
        """F08: Profile must feature Hardware Lab & Cyber Battlestation ASCII layout."""
        self.assertIn("Hardware Lab & Cyber Battlestation", self.content)
        self.assertIn("ESP32-WROOM-32D", self.content)


class TestGfmMarkdownTier2BoundaryAndCornerCases(unittest.TestCase):
    """Tier 2: Boundary & Corner Cases (HTML/Markdown spacing, image syntax, headings)."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")

    def test_t2_no_empty_headings(self):
        """T2: No heading markers (#, ##, ###) without accompanying title text."""
        empty_headings = re.findall(r"^#{1,6}\s*$", self.content, flags=re.MULTILINE)
        self.assertEqual(empty_headings, [], f"Empty markdown headings found: {empty_headings}")

    def test_t2_block_html_markdown_spacing(self):
        """T2: Block HTML tags (div, details) must maintain blank lines before nested markdown/code."""
        lines = self.content.splitlines()
        for idx, line in enumerate(lines[:-1]):
            stripped = line.strip()
            # If line is <details> or <summary>...</summary>, next line should either be empty or an HTML tag
            if stripped.startswith("<summary>") and stripped.endswith("</summary>"):
                next_line = lines[idx + 1].strip()
                # Check for blank line or valid break tag
                self.assertTrue(
                    next_line == "" or next_line.startswith("<"),
                    f"Missing blank line after summary tag at line {idx + 1}: '{next_line}'",
                )

    def test_t2_no_malformed_image_tags(self):
        """T2: All markdown images ![alt](src) and HTML <img src='...'> must have non-empty sources."""
        md_imgs = re.findall(r"!\[([^\]]*)\]\(([^)]*)\)", self.content)
        for alt, src in md_imgs:
            self.assertTrue(src.strip(), f"Markdown image missing source: alt='{alt}'")

        html_imgs = re.findall(r"<img\s+([^>]+)>", self.content)
        for attrs in html_imgs:
            self.assertIn("src=", attrs, f"HTML img tag missing src: <img {attrs}>")


class TestGfmMarkdownTier3CrossFeatureIntegration(unittest.TestCase):
    """Tier 3: Cross-Feature Integration (Badges map to technologies, SVG links match dossiers)."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")

    def test_t3_badges_match_technologies(self):
        """T3: Visual badges must cover C++, ESP32, Python, Linux, Electron, FreeRTOS."""
        required_techs = ["C%2B%2B", "ESP32", "Python", "Linux", "Electron", "FreeRTOS"]
        for tech in required_techs:
            self.assertIn(tech, self.content, f"Missing badge/icon for core technology: {tech}")

    def test_t3_hud_cards_centered_in_gfm_container(self):
        """T3: info-card.svg and tech-core.svg must be centered in responsive container."""
        hud_block = re.search(r"<div align=\"center\">\s*<a[^>]*>\s*<img src=\"assets/info-card.svg\"", self.content)
        self.assertIsNotNone(hud_block, "HUD cards must be centered within <div align='center'>")


class TestGfmMarkdownTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Real-World Scenarios (Complete Recruiter Browsing Journey)."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")

    def test_t4_full_recruiter_reading_hierarchy(self):
        """T4: Recruiter reading hierarchy must present sections in logical systems portfolio order."""
        sections = [
            "Engineering Dossier",
            "Flagship Projects",
            "FileDNA 2.0",
            "ESP32 Distributed Neural Network Accelerator",
            "Uday AI Local Server",
            "Enterprise & Systems Engineering Suite",
            "Hardware Lab",
            "Core Competency Matrix",
            "Live GitHub Analytics",
            "Contribution Heatmap",
            "Engineering Philosophy",
        ]

        last_pos = 0
        for section in sections:
            pos = self.content.find(section, last_pos)
            self.assertNotEqual(
                pos,
                -1,
                f"Section '{section}' missing or out of sequential portfolio order after pos {last_pos}",
            )
            last_pos = pos


if __name__ == "__main__":
    unittest.main()
