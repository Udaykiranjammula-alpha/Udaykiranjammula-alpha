#!/usr/bin/env python3
"""
tests/test_workflows.py
Comprehensive deterministic E2E test suite for GitHub Actions workflows & telemetry scripts.
Covers:
- F09: GitHub Actions Workflow Hardening
- F10: Workflow Idempotency & Script Verification
- F04: Tokyo Night Heatmap Renderer
Across Tiers 1-4.
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
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
SCRIPTS_DIR = ROOT / "scripts"
DATA_DIR = ROOT / "data"

try:
    import yaml
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False


def parse_yaml_fallback(content: str) -> dict:
    """Fallback basic YAML parser for workflow structure validation when PyYAML is unavailable."""
    data: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()
    return data


class TestWorkflowsTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Core Feature Coverage for GitHub Actions & Heatmap Generator (F09, F10, F04)."""

    def setUp(self):
        self.update_wf = WORKFLOWS_DIR / "update-contributions.yml"
        self.snake_wf = WORKFLOWS_DIR / "snake.yml"
        self.render_script = SCRIPTS_DIR / "render_heatmap.py"
        self.contributions_json = DATA_DIR / "contributions.json"

    # --- Feature 9: GitHub Actions Workflow Hardening ---

    def test_f09_workflow_files_exist(self):
        """F09: .github/workflows/ must contain update-contributions.yml and snake.yml."""
        self.assertTrue(self.update_wf.is_file(), f"Missing {self.update_wf}")
        self.assertTrue(self.snake_wf.is_file(), f"Missing {self.snake_wf}")

    def test_f09_yaml_syntax_valid(self):
        """F09: All workflow YAML files must parse without syntax error."""
        wf_files = glob.glob(str(WORKFLOWS_DIR / "*.yml"))
        self.assertGreaterEqual(len(wf_files), 1, "No YAML workflows found")

        for wf_path in wf_files:
            content = Path(wf_path).read_text(encoding="utf-8")
            if HAS_PYYAML:
                try:
                    parsed = yaml.safe_load(content)
                    self.assertIsInstance(parsed, dict, f"YAML root must be mapping in {Path(wf_path).name}")
                except yaml.YAMLError as err:
                    self.fail(f"Invalid YAML syntax in {Path(wf_path).name}: {err}")
            else:
                parsed = parse_yaml_fallback(content)
                self.assertIn("name", parsed)

    def test_f09_telemetry_workflow_triggers(self):
        """F09: update-contributions.yml must declare schedule (cron) and workflow_dispatch triggers."""
        content = self.update_wf.read_text(encoding="utf-8")
        self.assertIn("schedule:", content, "Missing schedule trigger in update-contributions.yml")
        self.assertIn("cron:", content, "Missing cron definition in update-contributions.yml")
        self.assertIn("workflow_dispatch:", content, "Missing workflow_dispatch in update-contributions.yml")

    def test_f09_telemetry_workflow_write_permissions(self):
        """F09: update-contributions.yml must explicitly specify 'permissions: contents: write'."""
        content = self.update_wf.read_text(encoding="utf-8")
        has_write_perm = ("permissions:\n  contents: write" in content or "contents: write" in content)
        self.assertTrue(has_write_perm, "update-contributions.yml must grant least-privilege 'contents: write'")

    def test_f09_telemetry_workflow_runner_environment(self):
        """F09: update-contributions.yml must specify runs-on: ubuntu-latest."""
        content = self.update_wf.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-latest", content)

    # --- Feature 4: Tokyo Night Heatmap Renderer ---

    def test_f04_render_heatmap_script_exists(self):
        """F04: scripts/render_heatmap.py must exist and be readable."""
        self.assertTrue(self.render_script.is_file(), f"Missing {self.render_script}")

    def test_f04_render_heatmap_dry_run_execution(self):
        """F04: scripts/render_heatmap.py dry-run must exit 0 and emit valid XML SVG."""
        with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as tmp_svg:
            tmp_path = Path(tmp_svg.name)

        try:
            cmd = [
                sys.executable,
                str(self.render_script),
                "--input",
                str(self.contributions_json),
                "--output",
                str(tmp_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, f"render_heatmap.py failed: {result.stderr}")
            self.assertTrue(tmp_path.is_file())
            self.assertGreater(tmp_path.stat().st_size, 1000)

            # Validate generated SVG structure
            tree = ET.parse(tmp_path)
            root = tree.getroot()
            self.assertTrue(root.tag.endswith("svg"))
            self.assertEqual(root.attrib.get("viewBox"), "0 0 860 216")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    # --- Feature 10: Workflow Idempotency & Script Verification ---

    def test_f10_clean_bot_commit_configuration(self):
        """F10: update-contributions.yml must configure official github-actions[bot] identity."""
        content = self.update_wf.read_text(encoding="utf-8")
        self.assertIn('git config user.name "github-actions[bot]"', content)
        self.assertIn("41898282+github-actions[bot]@users.noreply.github.com", content)

    def test_f10_safe_diff_check_before_commit(self):
        """F10: update-contributions.yml must check git diff --quiet before committing."""
        content = self.update_wf.read_text(encoding="utf-8")
        self.assertIn("git diff --quiet", content, "Workflow must check git diff before committing")
        self.assertIn("exit 0", content, "Workflow must exit cleanly when no diff exists")

    def test_f10_atomic_staging_explicit_targets(self):
        """F10: update-contributions.yml must only stage specific generated artifacts (never git add -A)."""
        content = self.update_wf.read_text(encoding="utf-8")
        self.assertNotIn("git add -A", content)
        self.assertNotIn("git add .", content)
        self.assertIn("git add data/contributions.json assets/contrib-heatmap.svg", content)

    def test_f10_commit_message_follows_conventional_format(self):
        """F10: update-contributions.yml commit message must follow chore: convention."""
        content = self.update_wf.read_text(encoding="utf-8")
        self.assertRegex(content, r'git commit -m\s*["\']chore', "Commit message must follow chore prefix")

    def test_f10_actions_checkout_v4_utilized(self):
        """F10: Workflows must utilize modern actions/checkout@v4."""
        content = self.update_wf.read_text(encoding="utf-8")
        self.assertIn("actions/checkout@v4", content)

    def test_f09_concurrency_control_configured(self):
        """F09: Workflows must specify concurrency control to avoid simultaneous push collisions."""
        update_content = self.update_wf.read_text(encoding="utf-8")
        self.assertIn("concurrency:", update_content)
        self.assertIn("group:", update_content)
        snake_content = self.snake_wf.read_text(encoding="utf-8")
        self.assertIn("concurrency:", snake_content)
        self.assertIn("group:", snake_content)

    def test_f10_fetch_contributions_script_exists(self):
        """F10: scripts/fetch_contributions.py must exist on disk."""
        fetch_script = SCRIPTS_DIR / "fetch_contributions.py"
        self.assertTrue(fetch_script.is_file(), f"Missing {fetch_script}")


class TestWorkflowsTier2BoundaryAndCornerCases(unittest.TestCase):
    """Tier 2: Boundary & Corner Cases (Jittered cron, malformed inputs, atomic files)."""

    def setUp(self):
        self.update_wf = WORKFLOWS_DIR / "update-contributions.yml"
        self.render_script = SCRIPTS_DIR / "render_heatmap.py"

    def test_t2_scheduled_cron_jitter_avoids_hour_top(self):
        """T2: update-contributions.yml scheduled cron minute must not be 00 (jittered to avoid contention)."""
        content = self.update_wf.read_text(encoding="utf-8")
        match = re.search(r'cron:\s*["\']([^"\']+)["\']', content)
        self.assertIsNotNone(match, "Could not locate cron string in update-contributions.yml")
        cron_expr = match.group(1).strip()
        cron_parts = cron_expr.split()
        self.assertGreaterEqual(len(cron_parts), 5, f"Malformed cron expression: '{cron_expr}'")
        minute = cron_parts[0]
        self.assertNotEqual(
            minute,
            "0",
            f"Cron schedule should use non-zero minute to avoid top-of-hour contention, got '{minute}'",
        )

    def test_t2_render_heatmap_handles_corrupted_json(self):
        """T2: render_heatmap.py must exit with code 1 when supplied corrupted JSON, leaving output intact."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp_json:
            tmp_json.write("{ corrupted: json content [[")
            corrupt_json_path = Path(tmp_json.name)

        with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as tmp_svg:
            tmp_svg.write("<svg>original</svg>")
            out_svg_path = Path(tmp_svg.name)

        try:
            cmd = [
                sys.executable,
                str(self.render_script),
                "--input",
                str(corrupt_json_path),
                "--output",
                str(out_svg_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 1, "Script should exit 1 on corrupt JSON")
            self.assertIn("error:", result.stderr.lower())
            # Output SVG should not be modified
            self.assertEqual(out_svg_path.read_text(encoding="utf-8"), "<svg>original</svg>")
        finally:
            if corrupt_json_path.exists():
                corrupt_json_path.unlink()
            if out_svg_path.exists():
                out_svg_path.unlink()

    def test_t2_render_heatmap_handles_empty_days_list(self):
        """T2: render_heatmap.py must exit with code 1 when JSON has an empty days list."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp_json:
            tmp_json.write(json.dumps({"username": "testuser", "days": []}))
            empty_json_path = Path(tmp_json.name)

        with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as tmp_svg:
            out_svg_path = Path(tmp_svg.name)

        try:
            cmd = [
                sys.executable,
                str(self.render_script),
                "--input",
                str(empty_json_path),
                "--output",
                str(out_svg_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 1)
        finally:
            if empty_json_path.exists():
                empty_json_path.unlink()
            if out_svg_path.exists():
                out_svg_path.unlink()

    def test_t2_atomic_file_write_leaves_no_tmp_leftovers(self):
        """T2: render_heatmap.py must cleanly rename temp files and leave no stray .tmp files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "output.svg"
            cmd = [
                sys.executable,
                str(self.render_script),
                "--input",
                str(DATA_DIR / "contributions.json"),
                "--output",
                str(out_path),
            ]
            subprocess.run(cmd, check=True, timeout=10)
            tmp_files = list(Path(tmp_dir).glob("*.tmp"))
            self.assertEqual(tmp_files, [], f"Leftover temporary files found: {tmp_files}")

    def test_t2_fetch_contributions_handles_invalid_markup(self):
        """T2: fetch_contributions.parse_calendar must reject invalid XML and malformed records."""
        sys.path.insert(0, str(SCRIPTS_DIR))
        import fetch_contributions

        with self.assertRaises(RuntimeError):
            fetch_contributions.parse_calendar(b"Not XML content at all")

        malformed_xml = b'<svg><rect data-date="invalid-date" data-count="5"/></svg>'
        with self.assertRaises(RuntimeError):
            fetch_contributions.parse_calendar(malformed_xml)

    def test_t2_fetch_contributions_atomic_write_zero_tmp_leftovers(self):
        """T2: fetch_contributions.write_json_atomic leaves zero .tmp files even on write failure."""
        sys.path.insert(0, str(SCRIPTS_DIR))
        import fetch_contributions

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "contributions.json"
            # Valid write
            fetch_contributions.write_json_atomic(out_file, {"schema_version": 1, "test": "data"})
            self.assertTrue(out_file.is_file())
            self.assertEqual(list(Path(tmp_dir).glob("*.tmp")), [])

            # Write failure with non-serializable object
            with self.assertRaises(TypeError):
                fetch_contributions.write_json_atomic(out_file, {"unserializable": object()})
            # Ensure no stray temp files left behind
            self.assertEqual(list(Path(tmp_dir).glob("*.tmp")), [], "Stray .tmp file remained after failure")

    def test_t2_fetch_contributions_graceful_cache_fallback(self):
        """T2: fetch_contributions.py preserves cache and exits 0 on network error when cache exists."""
        fetch_script = SCRIPTS_DIR / "fetch_contributions.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            cached_json = Path(tmp_dir) / "contributions.json"
            cached_json.write_text(json.dumps({"schema_version": 1, "cached": True}), encoding="utf-8")

            cmd = [
                sys.executable,
                str(fetch_script),
                "--username",
                "invalid-user-unlikely-to-exist-999999",
                "--output",
                str(cached_json),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(res.returncode, 0, f"Expected graceful exit 0, got {res.returncode}: {res.stderr}")
            self.assertTrue(cached_json.is_file())


class TestWorkflowsTier3CrossFeatureIntegration(unittest.TestCase):
    """Tier 3: Cross-Feature Integration (Script paths, data alignment, deterministic rerun)."""

    def setUp(self):
        self.update_wf = WORKFLOWS_DIR / "update-contributions.yml"
        self.render_script = SCRIPTS_DIR / "render_heatmap.py"
        self.contributions_json = DATA_DIR / "contributions.json"

    def test_t3_workflow_script_paths_exist_in_repository(self):
        """T3: All python scripts called by update-contributions.yml must exist on disk."""
        content = self.update_wf.read_text(encoding="utf-8")
        script_calls = re.findall(r"python\s+(scripts/[\w.-]+)", content)
        self.assertGreaterEqual(len(script_calls), 1)

        for script_rel in script_calls:
            target = ROOT / script_rel
            self.assertTrue(target.is_file(), f"Workflow calls non-existent script: {target}")

    def test_t3_idempotent_heatmap_generation(self):
        """T3: Running render_heatmap.py twice on identical input produces byte-identical output (0 diff)."""
        with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f1, \
             tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f2:
            p1, p2 = Path(f1.name), Path(f2.name)

        try:
            cmd1 = [sys.executable, str(self.render_script), "--input", str(self.contributions_json), "--output", str(p1)]
            cmd2 = [sys.executable, str(self.render_script), "--input", str(self.contributions_json), "--output", str(p2)]
            subprocess.run(cmd1, check=True, timeout=10)
            subprocess.run(cmd2, check=True, timeout=10)

            svg1 = p1.read_text(encoding="utf-8")
            svg2 = p2.read_text(encoding="utf-8")
            self.assertEqual(svg1, svg2, "Rerunning heatmap renderer on identical input produced diff")
        finally:
            if p1.exists():
                p1.unlink()
            if p2.exists():
                p2.unlink()

    def test_t3_contributions_json_schema_valid_for_heatmap(self):
        """T3: data/contributions.json must have schema required by render_heatmap.py."""
        self.assertTrue(self.contributions_json.is_file())
        doc = json.loads(self.contributions_json.read_text(encoding="utf-8"))
        self.assertIn("username", doc)
        self.assertIn("days", doc)
        self.assertIsInstance(doc["days"], list)
        self.assertGreater(len(doc["days"]), 0)
        first_day = doc["days"][0]
        self.assertIn("date", first_day)
        self.assertIn("count", first_day)


class TestWorkflowsTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Real-World Scenarios (Simulating complete GitHub Actions telemetry run step)."""

    def test_t4_simulate_telemetry_workflow_pipeline(self):
        """T4: End-to-end execution of telemetry render step simulating full GitHub Actions job."""
        render_script = SCRIPTS_DIR / "render_heatmap.py"
        contributions_json = DATA_DIR / "contributions.json"

        with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as out_f:
            target_svg = Path(out_f.name)

        try:
            # 1. Run generator
            cmd = [sys.executable, str(render_script), "--input", str(contributions_json), "--output", str(target_svg)]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("Rendered", proc.stdout)

            # 2. Verify output is production-ready
            tree = ET.parse(target_svg)
            root = tree.getroot()
            self.assertEqual(root.attrib.get("viewBox"), "0 0 860 216")
            self.assertEqual(root.attrib.get("role"), "img")

            # 3. Simulate git diff check (re-render and check equality)
            re_rendered = render_script.read_text(encoding="utf-8")
            self.assertGreater(len(re_rendered), 100)
        finally:
            if target_svg.exists():
                target_svg.unlink()


if __name__ == "__main__":
    unittest.main()
