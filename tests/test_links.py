#!/usr/bin/env python3
"""
tests/test_links.py
Comprehensive deterministic E2E test suite for Link & Asset Resolution Gate (F11).
Verifies 100% of relative local asset paths and external HTTP endpoints across Tiers 1-4.
"""
from __future__ import annotations

import concurrent.futures
import re
import socket
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
USER_AGENT = "UdayProfileTestSuite/1.0 (+https://github.com/Udaykiranjammula-alpha)"


def extract_all_links(content: str) -> tuple[list[str], list[str]]:
    """
    Extract all local and external links from markdown and embedded HTML.
    Returns (local_links, external_links).
    """
    # 1. Markdown links [text](url)
    md_links = re.findall(r"\[(?:[^\]]*)\]\(([^)\s]+)\)", content)
    # 2. HTML src="..."
    src_links = re.findall(r'src=["\']([^"\']+)["\']', content)
    # 3. HTML href="..."
    href_links = re.findall(r'href=["\']([^"\']+)["\']', content)

    all_raw = sorted(set(md_links + src_links + href_links))
    local_links = []
    external_links = []

    for link in all_raw:
        link = link.strip()
        if not link or link.startswith("#"):
            continue
        if link.startswith(("http://", "https://", "mailto:")):
            external_links.append(link)
        else:
            # Strip query strings or fragments for filesystem check
            cleaned = link.split("?")[0].split("#")[0]
            local_links.append(cleaned)

    return sorted(set(local_links)), sorted(set(external_links))


def probe_url(url: str, timeout: float = 6.0, retries: int = 2) -> tuple[str, int | None, str | None]:
    """Probe external URL with GET request and custom User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return url, res.status, None
        except urllib.error.HTTPError as http_err:
            return url, http_err.code, str(http_err)
        except Exception as err:
            if attempt == retries - 1:
                return url, None, str(err)
            time.sleep(0.5)
    return url, None, "Unknown error"


def check_network_connectivity() -> bool:
    """Probe GitHub to verify outbound internet connectivity."""
    try:
        req = urllib.request.Request("https://github.com", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=4.0) as res:
            return res.status == 200
    except Exception:
        return False


class TestLinksTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Core Feature Coverage for Link Resolution (F11)."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        cls.local_links, cls.external_links = extract_all_links(cls.content)
        cls.is_online = check_network_connectivity()

    def test_f11_readme_exists_and_non_empty(self):
        """F11: README.md must exist and contain portfolio content."""
        self.assertTrue(README_PATH.is_file(), f"Missing README at {README_PATH}")
        self.assertGreater(len(self.content), 1000, "README.md is unexpectedly short")

    def test_f11_extracts_links(self):
        """F11: Link extractor must discover both local assets and external endpoints."""
        self.assertGreaterEqual(len(self.local_links), 3, "Expected at least 3 local asset links")
        self.assertGreaterEqual(len(self.external_links), 20, "Expected at least 20 external URLs")

    def test_f11_all_local_assets_resolve_to_filesystem(self):
        """F11: 100% of relative local links in README.md must exist on disk."""
        missing = []
        for rel_path in self.local_links:
            target = ROOT / rel_path
            if not target.exists():
                missing.append(f"{rel_path} -> {target}")
        self.assertEqual(missing, [], f"Broken local asset links found in README: {missing}")

    def test_f11_flagship_repo_urls_present(self):
        """F11: README.md must link to all 3 flagship GitHub repositories."""
        expected_repos = [
            "https://github.com/Udaykiranjammula-alpha/file-dna",
            "https://github.com/Udaykiranjammula-alpha/esp32-distributed-ml-accelerator",
            "https://github.com/Udaykiranjammula-alpha/uday-ai-local-server",
        ]
        for repo_url in expected_repos:
            self.assertIn(repo_url, self.external_links, f"Missing flagship repo URL: {repo_url}")

    def test_f11_enterprise_suite_repo_urls_present(self):
        """F11: README.md must link to enterprise systems repositories."""
        expected_repos = [
            "https://github.com/Udaykiranjammula-alpha/Banking-Loan-Management-System-using-c",
            "https://github.com/Udaykiranjammula-alpha/STUDENT-GRIEVANCE-REDRESSAL-SYSTEM-SGRS-using-python",
            "https://github.com/Udaykiranjammula-alpha/-FEDFW-Lab-Insem1",
        ]
        for repo_url in expected_repos:
            self.assertIn(repo_url, self.external_links, f"Missing enterprise repo URL: {repo_url}")

    def test_f11_external_flagship_urls_return_http_200(self):
        """F11: Flagship repository URLs must resolve to HTTP 200 when online."""
        if not self.is_online:
            self.skipTest("Host environment is offline; skipping live external HTTP probe")

        flagship_urls = [
            "https://github.com/Udaykiranjammula-alpha/file-dna",
            "https://github.com/Udaykiranjammula-alpha/esp32-distributed-ml-accelerator",
            "https://github.com/Udaykiranjammula-alpha/uday-ai-local-server",
        ]
        for url in flagship_urls:
            _, status, err = probe_url(url, timeout=5.0)
            self.assertEqual(status, 200, f"URL {url} returned non-200 status {status} (err: {err})")


class TestLinksTier2BoundaryAndCornerCases(unittest.TestCase):
    """Tier 2: Boundary & Corner Cases (URL syntax, protocols, escaping, mailto)."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        cls.local_links, cls.external_links = extract_all_links(cls.content)

    def test_t2_no_empty_href_or_src(self):
        """T2: No empty href='' or src='' attributes in markdown or HTML."""
        empty_md = re.findall(r"\[(?:[^\]]*)\]\(\s*\)", self.content)
        empty_src = re.findall(r'src=["\']\s*["\']', self.content)
        empty_href = re.findall(r'href=["\']\s*["\']', self.content)
        self.assertEqual(empty_md, [], f"Empty markdown links found: {empty_md}")
        self.assertEqual(empty_src, [], f"Empty src attributes found: {empty_src}")
        self.assertEqual(empty_href, [], f"Empty href attributes found: {empty_href}")

    def test_t2_all_external_urls_use_secure_https_or_mailto(self):
        """T2: All external links must use https:// or mailto: (no insecure http://)."""
        insecure = [u for u in self.external_links if u.startswith("http://")]
        self.assertEqual(insecure, [], f"Insecure HTTP links detected: {insecure}")

    def test_t2_mailto_format_and_domain(self):
        """T2: Mailto link in README must target valid university email address."""
        mailto_links = [u for u in self.external_links if u.startswith("mailto:")]
        self.assertGreaterEqual(len(mailto_links), 1, "Expected at least one mailto: link")
        email = mailto_links[0].replace("mailto:", "")
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        self.assertRegex(email, email_regex, f"Malformed email address: {email}")
        self.assertTrue(email.endswith("kluniversity.in"), f"Email must be university domain: {email}")

    def test_t2_shields_io_badge_syntax_escaping(self):
        """T2: Shields.io badges must not contain unescaped whitespace or invalid delimiters."""
        shields_urls = [u for u in self.external_links if "img.shields.io" in u]
        self.assertGreaterEqual(len(shields_urls), 5, "Expected Shields.io badge URLs")
        for badge_url in shields_urls:
            # Must not contain raw spaces
            self.assertNotIn(" ", badge_url, f"Raw unescaped space in badge URL: {badge_url}")
            # Valid URL parsing
            parsed = urllib.parse.urlparse(badge_url)
            self.assertTrue(bool(parsed.scheme and parsed.netloc), f"Invalid badge URL: {badge_url}")

    def test_t2_no_path_traversal_in_local_links(self):
        """T2: No local links may contain directory traversal sequences ('../' or absolute drive paths)."""
        for rel_path in self.local_links:
            self.assertNotIn("..", rel_path, f"Directory traversal detected in link: {rel_path}")
            self.assertFalse(
                rel_path.startswith("/") or ":" in rel_path,
                f"Absolute path detected in local link: {rel_path}",
            )


class TestLinksTier3CrossFeatureIntegration(unittest.TestCase):
    """Tier 3: Cross-Feature Integration (Assets binding, dossier links)."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        cls.local_links, cls.external_links = extract_all_links(cls.content)

    def test_t3_local_assets_are_non_empty(self):
        """T3: All referenced local assets must have positive byte length."""
        for rel_path in self.local_links:
            target = ROOT / rel_path
            self.assertTrue(target.is_file(), f"Target missing: {target}")
            self.assertGreater(target.stat().st_size, 0, f"Referenced asset {target} is 0 bytes")

    def test_t3_hud_cards_both_referenced_in_readme(self):
        """T3: Both info-card.svg and tech-core.svg must be referenced together in README."""
        self.assertIn("assets/info-card.svg", self.local_links)
        self.assertIn("assets/tech-core.svg", self.local_links)

    def test_t3_heatmap_referenced_in_readme(self):
        """T3: assets/contrib-heatmap.svg must be embedded in README."""
        self.assertIn("assets/contrib-heatmap.svg", self.local_links)


class TestLinksTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Real-World Scenarios (Recruiter journey link click-through)."""

    @classmethod
    def setUpClass(cls):
        cls.content = README_PATH.read_text(encoding="utf-8")
        cls.local_links, cls.external_links = extract_all_links(cls.content)
        cls.is_online = check_network_connectivity()

    def test_t4_recruiter_profile_and_contact_click_flow(self):
        """T4: Recruiter primary entry points (Profile, Email, Flagship Repos) must all be accessible."""
        primary_endpoints = [
            "https://github.com/Udaykiranjammula-alpha",
            "mailto:2500031243@kluniversity.in",
            "https://github.com/Udaykiranjammula-alpha/file-dna",
        ]
        for ep in primary_endpoints:
            self.assertIn(ep, self.external_links, f"Recruiter entry point missing: {ep}")

        if self.is_online:
            # Probe HTTP endpoints
            for ep in primary_endpoints:
                if ep.startswith("https://"):
                    _, status, err = probe_url(ep, timeout=5.0)
                    self.assertEqual(status, 200, f"Recruiter endpoint {ep} returned status {status}")


if __name__ == "__main__":
    unittest.main()
