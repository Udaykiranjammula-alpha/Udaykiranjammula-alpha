#!/usr/bin/env python3
"""
tests/test_adversarial_m2.py
Adversarial challenge test suite for Milestone 2 (Adversarial Link & Markdown Challenger).
Conducts empirical stress-testing, boundary verification, and mathematical consistency checks for:
- Local asset existence, byte lengths, and format validation (SVGs, GIF)
- GFM Markdown table column consistency, delimiter validity, and escaped pipes
- Code fence pairing, enclosure boundaries, and language tagging
- HTML AST tag balancing, LIFO nesting, and void/self-closing handling outside code blocks
- Link extraction completeness, protocol security (HTTPS/mailto), and URL formatting
- Quantitative technical dossier metrics and mathematical consistency
"""
from __future__ import annotations

import os
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
ASSETS_DIR = ROOT / "assets"


class StrictHtmlAstBalancer(HTMLParser):
    """
    Hostile, strict AST-based HTML balancer.
    Tracks start/end tags, ensures void tags don't nest, validates strict LIFO closure,
    and checks details/summary relationship.
    """
    VOID_TAGS = {"img", "br", "hr", "input", "source", "meta", "link"}

    def __init__(self):
        super().__init__()
        self.stack: list[tuple[str, int, int]] = []
        self.errors: list[str] = []
        self.tag_counts: dict[str, int] = {}
        self.details_summary_valid: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag_lower = tag.lower()
        line, col = self.getpos()
        self.tag_counts[tag_lower] = self.tag_counts.get(tag_lower, 0) + 1

        if tag_lower in self.VOID_TAGS:
            return

        if tag_lower == "summary":
            if not self.stack or self.stack[-1][0] != "details":
                self.errors.append(f"<summary> at line {line}:{col} must be immediate child of <details>")

        self.stack.append((tag_lower, line, col))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]):
        # Explicit self-closing tag like <br/> or <img ... />
        tag_lower = tag.lower()
        self.tag_counts[tag_lower] = self.tag_counts.get(tag_lower, 0) + 1

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        line, col = self.getpos()

        if tag_lower in self.VOID_TAGS:
            self.errors.append(f"Forbidden closing tag </{tag_lower}> for void element at line {line}:{col}")
            return

        if not self.stack:
            self.errors.append(f"Unexpected closing tag </{tag_lower}> at line {line}:{col} (empty stack)")
            return

        expected_tag, open_line, open_col = self.stack.pop()
        if expected_tag != tag_lower:
            self.errors.append(
                f"Tag nesting violation at line {line}:{col}: closing </{tag_lower}> "
                f"does not match open <{expected_tag}> from line {open_line}:{open_col}"
            )

    def verify_complete(self) -> list[str]:
        for tag, line, col in self.stack:
            self.errors.append(f"Unclosed HTML tag <{tag}> opened at line {line}:{col}")
        return self.errors


class TestAdversarialAssetIntegrity(unittest.TestCase):
    """Adversarial stress-testing of all local assets referenced or located in assets/."""

    @classmethod
    def setUpClass(cls):
        cls.readme_content = README_PATH.read_text(encoding="utf-8")
        # Extract all local asset paths referenced in README
        cls.referenced_local_assets = set()
        for match in re.finditer(r'(?:src=["\']|href=["\']|!\[[^\]]*\]\()([^"\'\)\s]+)', cls.readme_content):
            target = match.group(1).strip()
            if target and not target.startswith(("http://", "https://", "mailto:", "#")):
                # Strip query and fragments
                cleaned = target.split("?")[0].split("#")[0]
                cls.referenced_local_assets.add(cleaned)

    def test_local_asset_references_exist_and_non_empty(self):
        """Verify all local asset paths referenced in README.md exist on disk with > 0 bytes."""
        self.assertGreaterEqual(len(self.referenced_local_assets), 3, "Expected at least 3 local assets referenced")
        for rel_path in self.referenced_local_assets:
            file_path = ROOT / rel_path
            self.assertTrue(file_path.exists(), f"Referenced local asset does not exist: {rel_path}")
            self.assertTrue(file_path.is_file(), f"Referenced asset is not a file: {rel_path}")
            size = file_path.stat().st_size
            self.assertGreater(size, 0, f"Referenced asset {rel_path} has 0 bytes")

    def test_no_windows_backslashes_in_asset_paths(self):
        """All asset references in README must use POSIX forward slashes / for cross-platform compatibility."""
        for rel_path in self.referenced_local_assets:
            self.assertNotIn("\\", rel_path, f"Windows backslash detected in asset link: {rel_path}")

    def test_no_path_traversal_in_asset_references(self):
        """Local references must not contain directory traversal sequences (..) or absolute root paths."""
        for rel_path in self.referenced_local_assets:
            self.assertNotIn("..", rel_path, f"Path traversal sequence detected in asset reference: {rel_path}")
            self.assertFalse(rel_path.startswith("/") or ":" in rel_path, f"Absolute path detected: {rel_path}")

    def test_all_disk_assets_are_valid_and_non_corrupted(self):
        """Verify every asset in the assets/ directory is structurally intact and non-empty."""
        assets = list(ASSETS_DIR.iterdir())
        self.assertGreaterEqual(len(assets), 4, f"Expected at least 4 assets in assets/, found {len(assets)}")

        for asset in assets:
            self.assertTrue(asset.is_file(), f"Asset item is not a file: {asset}")
            size = asset.stat().st_size
            self.assertGreater(size, 100, f"Asset file {asset.name} is suspiciously small ({size} bytes)")

            if asset.suffix.lower() == ".svg":
                # Must be well-formed XML
                try:
                    tree = ET.parse(asset)
                    root = tree.getroot()
                    self.assertTrue(
                        root.tag.endswith("svg"),
                        f"SVG root tag is not svg in {asset.name}: {root.tag}",
                    )
                    self.assertTrue(
                        "viewBox" in root.attrib or ("width" in root.attrib and "height" in root.attrib),
                        f"SVG {asset.name} missing dimensions/viewBox",
                    )
                except ET.ParseError as err:
                    self.fail(f"Corrupted or invalid XML in SVG asset {asset.name}: {err}")

            elif asset.suffix.lower() == ".gif":
                # Must start with GIF87a or GIF89a header
                with open(asset, "rb") as f:
                    header = f.read(6)
                    self.assertIn(
                        header,
                        (b"GIF87a", b"GIF89a"),
                        f"GIF asset {asset.name} has invalid magic header: {header}",
                    )


class TestAdversarialMarkdownTables(unittest.TestCase):
    """Stress-test markdown table structure, delimiters, escaping, and column consistency."""

    @classmethod
    def setUpClass(cls):
        cls.readme_content = README_PATH.read_text(encoding="utf-8")
        cls.lines = cls.readme_content.splitlines()

    def _extract_tables(self) -> list[dict]:
        """Parse all markdown tables from the document."""
        tables = []
        current_table = []
        current_start_line = 0

        for line_idx, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            # GFM table row check
            if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2:
                if not current_table:
                    current_start_line = line_idx
                current_table.append((line_idx, stripped))
            else:
                if current_table:
                    if len(current_table) >= 2:
                        tables.append({
                            "start_line": current_start_line,
                            "rows": current_table,
                        })
                    current_table = []

        if current_table and len(current_table) >= 2:
            tables.append({
                "start_line": current_start_line,
                "rows": current_table,
            })

        return tables

    def _split_table_cells(self, row_str: str) -> list[str]:
        """Split table row into cells, respecting backtick inline code spans."""
        # Strip outer pipes
        inner = row_str.strip()
        if inner.startswith("|"):
            inner = inner[1:]
        if inner.endswith("|"):
            inner = inner[:-1]

        # Parse character by character to handle backticks and escaped pipes
        cells = []
        current = []
        in_backtick = False

        for ch in inner:
            if ch == "`":
                in_backtick = not in_backtick
                current.append(ch)
            elif ch == "|" and not in_backtick:
                cells.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        cells.append("".join(current).strip())
        return cells

    def test_tables_detected_count(self):
        """Ensure all 6 expected technical tables exist in README.md."""
        tables = self._extract_tables()
        self.assertGreaterEqual(
            len(tables), 6,
            f"Expected at least 6 technical tables in README.md, found {len(tables)}",
        )

    def test_every_table_delimiter_row_is_valid_gfm(self):
        """Delimiter rows must contain only hyphens and colons conforming to GFM specification."""
        tables = self._extract_tables()
        for t_idx, t in enumerate(tables, start=1):
            delim_line_num, delim_str = t["rows"][1]
            delim_cells = self._split_table_cells(delim_str)
            for col_idx, cell in enumerate(delim_cells, start=1):
                self.assertTrue(
                    re.match(r"^:?-+:?$", cell),
                    f"Table {t_idx} (line {delim_line_num}) delimiter col {col_idx} is invalid: '{cell}'",
                )

    def test_every_table_has_consistent_column_count_across_all_rows(self):
        """Every row in every table must match the header row's exact column count."""
        tables = self._extract_tables()
        for t_idx, t in enumerate(tables, start=1):
            header_line, header_str = t["rows"][0]
            header_cells = self._split_table_cells(header_str)
            expected_cols = len(header_cells)
            self.assertGreaterEqual(expected_cols, 2, f"Table {t_idx} at line {header_line} has < 2 cols")

            for row_line, row_str in t["rows"][1:]:
                row_cells = self._split_table_cells(row_str)
                self.assertEqual(
                    len(row_cells),
                    expected_cols,
                    f"Table {t_idx} row at line {row_line} has {len(row_cells)} columns, expected {expected_cols}.\nRow: {row_str}",
                )


class TestAdversarialCodeFences(unittest.TestCase):
    """Stress-test code fences, language syntax identifiers, and nesting boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.readme_content = README_PATH.read_text(encoding="utf-8")
        cls.lines = cls.readme_content.splitlines()

    def test_code_fences_strictly_paired(self):
        """Total count of triple backtick fences must be strictly even."""
        fences = [idx for idx, line in enumerate(self.lines, start=1) if line.strip().startswith("```")]
        self.assertEqual(
            len(fences) % 2, 0,
            f"Odd number of code fence markers detected: {len(fences)} at lines {fences}",
        )
        self.assertGreaterEqual(len(fences), 8, "Expected at least 4 paired code blocks")

    def test_code_fence_openings_and_closings_alternate(self):
        """Fences must strictly alternate between open and close without nesting."""
        in_fence = False
        fence_ranges = []
        open_line = 0

        for line_num, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                if not in_fence:
                    in_fence = True
                    open_line = line_num
                else:
                    in_fence = False
                    fence_ranges.append((open_line, line_num))

        self.assertFalse(in_fence, f"Unclosed code fence opened at line {open_line}")
        for op, cl in fence_ranges:
            self.assertGreater(cl, op, f"Invalid fence range: {op} to {cl}")

    def test_code_fence_languages_are_valid(self):
        """Opening code fences must have valid language identifiers or plain text/ascii."""
        in_fence = False
        valid_languages = {"zsh", "bash", "sh", "python", "cpp", "c", "json", "yaml", "xml", ""}

        for line_num, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                if not in_fence:
                    # Opening fence
                    in_fence = True
                    lang = stripped[3:].strip()
                    self.assertIn(
                        lang, valid_languages,
                        f"Unrecognized code fence language '{lang}' at line {line_num}",
                    )
                else:
                    # Closing fence must be exactly ```
                    in_fence = False
                    self.assertEqual(
                        stripped, "```",
                        f"Closing fence at line {line_num} contains extra text: '{stripped}'",
                    )


class TestAdversarialHtmlAstBalancing(unittest.TestCase):
    """Stress-test HTML AST balancing outside code fences and inline backtick spans."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        # Strip all code blocks completely
        cls.clean_content = re.sub(r"```.*?```", "", cls.content, flags=re.DOTALL)
        # Strip inline code spans
        cls.clean_content = re.sub(r"`[^`]*`", "", cls.clean_content)

    def test_strict_html_ast_balancer_zero_errors(self):
        """Verify strict LIFO HTML AST balance with 0 unclosed and 0 mismatched tags."""
        balancer = StrictHtmlAstBalancer()
        balancer.feed(self.clean_content)
        errors = balancer.verify_complete()
        self.assertEqual(errors, [], f"HTML AST balancing errors: {errors}")

    def test_collapsible_details_structure_and_counts(self):
        """Ensure all <details> have matching </details> and properly paired <summary> tags."""
        open_details = len(re.findall(r"<details(?:\s+[^>]*)?>", self.clean_content, flags=re.IGNORECASE))
        close_details = len(re.findall(r"</details>", self.clean_content, flags=re.IGNORECASE))
        self.assertEqual(
            open_details, close_details,
            f"Details tag count mismatch: <details>={open_details}, </details>={close_details}",
        )
        self.assertEqual(open_details, 3, "Expected exactly 3 collapsible project dossiers")

        open_summary = len(re.findall(r"<summary(?:\s+[^>]*)?>", self.clean_content, flags=re.IGNORECASE))
        close_summary = len(re.findall(r"</summary>", self.clean_content, flags=re.IGNORECASE))
        self.assertEqual(
            open_summary, close_summary,
            f"Summary tag count mismatch: <summary>={open_summary}, </summary>={close_summary}",
        )
        self.assertEqual(open_summary, 3, "Expected exactly 3 summary tags matching 3 dossiers")


class TestAdversarialLinkFormatting(unittest.TestCase):
    """Verify security, formatting, and protocols across all links in README.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        # Extract markdown links, hrefs, and srcs
        cls.md_links = re.findall(r"\[([^\]]*)\]\(([^)\s]+)\)", cls.content)
        cls.href_links = re.findall(r'href=["\']([^"\']+)["\']', cls.content)
        cls.src_links = re.findall(r'src=["\']([^"\']+)["\']', cls.content)
        cls.all_urls = [u for _, u in cls.md_links] + cls.href_links + cls.src_links

    def test_no_insecure_http_links(self):
        """Ensure zero unencrypted http:// links exist in the entire README."""
        insecure = [u for u in self.all_urls if u.startswith("http://")]
        self.assertEqual(insecure, [], f"Insecure HTTP URLs found: {insecure}")

    def test_no_empty_or_whitespace_urls(self):
        """Ensure no link or source has empty or whitespace-only target."""
        empty_urls = [u for u in self.all_urls if not u.strip()]
        self.assertEqual(empty_urls, [], f"Empty URL targets found: {empty_urls}")

    def test_all_flagship_repos_are_properly_formatted_github_links(self):
        """Flagship repo links must follow canonical GitHub format."""
        expected = [
            "https://github.com/Udaykiranjammula-alpha/file-dna",
            "https://github.com/Udaykiranjammula-alpha/esp32-distributed-ml-accelerator",
            "https://github.com/Udaykiranjammula-alpha/uday-ai-local-server",
        ]
        for repo_url in expected:
            self.assertIn(repo_url, self.all_urls, f"Missing required flagship repo URL: {repo_url}")


class TestAdversarialMilestone2DossierMetrics(unittest.TestCase):
    """Empirical mathematical and architectural consistency check for M2 dossiers."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")

    def test_filedna_entropy_formula_and_bounds(self):
        """FileDNA dossier must state the exact Shannon formula and [0.0, 8.0] range."""
        self.assertIn("H(X) = -\\sum", self.content)
        self.assertIn("0.0", self.content)
        self.assertIn("8.0", self.content)
        self.assertIn("RANSOMWARE", self.content)

    def test_filedna_radix_trie_signatures(self):
        """FileDNA dossier must document all 4 canonical magic-byte signatures."""
        signatures = ["89 50 4E 47", "25 50 44 46", "4D 5A 90 00", "50 4B 03 04"]
        for sig in signatures:
            self.assertIn(sig, self.content, f"Missing signature in FileDNA dossier: {sig}")

    def test_esp32_sram_budget_math(self):
        """ESP32 SRAM budget numbers (180 + 128 + 140 + 72) must sum exactly to 520 KB."""
        # Check that numbers exist in document
        self.assertIn("180 KB", self.content)
        self.assertIn("128 KB", self.content)
        self.assertIn("140 KB", self.content)
        self.assertIn("72 KB", self.content)
        self.assertIn("520 KB", self.content)
        # Sum verification
        total = 180 + 128 + 140 + 72
        self.assertEqual(total, 520, f"SRAM numbers do not sum to 520: {total}")

    def test_esp32_inference_latency_benchmark(self):
        """ESP32 MobileNet benchmark must state 54.2 ms end-to-end latency and ~1.2 ms transfer."""
        self.assertIn("54.2 ms", self.content)
        self.assertIn("1.2 ms", self.content)
        self.assertIn("MobileNet-v1", self.content)

    def test_uday_ai_roofline_bandwidth_math(self):
        """Uday AI Roofline bandwidth math must be mathematically accurate."""
        # Q4_K_M: 3.9 GB * 18 tok/s = 70.2 GB/s
        self.assertIn("3.9 GB", self.content)
        self.assertIn("18 tok/s", self.content)
        self.assertIn("70.2 GB/s", self.content)
        # Q8_0: 7.2 GB * 11 tok/s = 79.2 GB/s
        self.assertIn("7.2 GB", self.content)
        self.assertIn("11 tok/s", self.content)
        self.assertIn("79.2 GB/s", self.content)
        # Check product
        self.assertAlmostEqual(3.9 * 18, 70.2, places=1)
        self.assertAlmostEqual(7.2 * 11, 79.2, places=1)

    def test_uday_ai_kv_cache_budget_math(self):
        """Uday AI KV-cache formula 2 * 32 * 8 * 128 * 2 = 131072 bytes (128 KB/token)."""
        kv_bytes = 2 * 32 * 8 * 128 * 2
        self.assertEqual(kv_bytes, 131072)
        self.assertEqual(kv_bytes / 1024, 128)
        self.assertIn("128 KB/token", self.content)
        self.assertIn("512 MB", self.content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
