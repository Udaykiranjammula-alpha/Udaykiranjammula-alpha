#!/usr/bin/env python3
"""
tests/run_all_tests.py
Master Test Runner aggregating E2E test results across all 4 tiers and 13 features:
- tests/test_svg_assets.py
- tests/test_links.py
- tests/test_gfm_markdown.py
- tests/test_workflows.py

Produces structured tier-by-tier reporting, counts, execution timings, and failure breakdowns.
Exits 0 if all tests pass, or non-zero if failures occur.
"""
from __future__ import annotations

import argparse
import sys
import time
import unittest
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tests.test_gfm_markdown as mod_gfm
import tests.test_links as mod_links
import tests.test_svg_assets as mod_svg
import tests.test_workflows as mod_workflows


MODULES = [
    ("SVG Assets & Well-Formedness (F01, F02, F03, F04, F13)", mod_svg),
    ("Link & URL Resolution Gate (F11)", mod_links),
    ("GFM Markdown & Systems Dossiers (F12, F05, F06, F07, F08)", mod_gfm),
    ("GitHub Actions & Heatmap Generator (F09, F10, F04)", mod_workflows),
]


def classify_tier(test_name: str, class_name: str) -> str:
    """Classify a test into Tier 1, 2, 3, or 4 based on class/method naming convention."""
    combined = f"{class_name}.{test_name}".lower()
    if "tier1" in combined or "_f0" in combined or "_f1" in combined:
        return "Tier 1: Feature Coverage"
    elif "tier2" in combined or "_t2" in combined:
        return "Tier 2: Boundary & Corner"
    elif "tier3" in combined or "_t3" in combined:
        return "Tier 3: Cross-Feature Integration"
    elif "tier4" in combined or "_t4" in combined:
        return "Tier 4: Real-World Scenarios"
    return "Tier 1: Feature Coverage"


class TierTrackingResult(unittest.TestResult):
    """Custom TestResult collecting detailed tier metrics and execution stats."""

    def __init__(self, verbose: bool = False):
        super().__init__()
        self.verbose = verbose
        self.tier_stats = {
            "Tier 1: Feature Coverage": {"run": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0},
            "Tier 2: Boundary & Corner": {"run": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0},
            "Tier 3: Cross-Feature Integration": {"run": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0},
            "Tier 4: Real-World Scenarios": {"run": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0},
        }
        self.module_stats: dict[str, dict[str, int]] = {}
        self.test_start_times: dict[str, float] = {}
        self.test_durations: dict[str, float] = {}

    def startTest(self, test: unittest.TestCase):
        super().startTest(test)
        self.test_start_times[test.id()] = time.perf_counter()
        tier = classify_tier(test._testMethodName, test.__class__.__name__)
        self.tier_stats[tier]["run"] += 1

        mod_name = test.__class__.__module__
        if mod_name not in self.module_stats:
            self.module_stats[mod_name] = {"run": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0}
        self.module_stats[mod_name]["run"] += 1

        if self.verbose:
            sys.stdout.write(f"  - {test.id()} ... ")
            sys.stdout.flush()

    def stopTest(self, test: unittest.TestCase):
        super().stopTest(test)
        start = self.test_start_times.get(test.id())
        if start is not None:
            self.test_durations[test.id()] = time.perf_counter() - start

    def addSuccess(self, test: unittest.TestCase):
        super().addSuccess(test)
        tier = classify_tier(test._testMethodName, test.__class__.__name__)
        self.tier_stats[tier]["pass"] += 1
        self.module_stats[test.__class__.__module__]["pass"] += 1
        if self.verbose:
            duration = time.perf_counter() - self.test_start_times.get(test.id(), time.perf_counter())
            print(f"ok ({duration:.3f}s)")

    def addFailure(self, test: unittest.TestCase, err):
        super().addFailure(test, err)
        tier = classify_tier(test._testMethodName, test.__class__.__name__)
        self.tier_stats[tier]["fail"] += 1
        self.module_stats[test.__class__.__module__]["fail"] += 1
        if self.verbose:
            print("FAIL")

    def addError(self, test: unittest.TestCase, err):
        super().addError(test, err)
        tier = classify_tier(test._testMethodName, test.__class__.__name__)
        self.tier_stats[tier]["error"] += 1
        self.module_stats[test.__class__.__module__]["error"] += 1
        if self.verbose:
            print("ERROR")

    def addSkip(self, test: unittest.TestCase, reason: str):
        super().addSkip(test, reason)
        tier = classify_tier(test._testMethodName, test.__class__.__name__)
        self.tier_stats[tier]["skip"] += 1
        self.module_stats[test.__class__.__module__]["skip"] += 1
        if self.verbose:
            print(f"SKIP ({reason})")


def run_all(verbose: bool = False) -> int:
    """Run all test suites and print structured summary."""
    print("=" * 80)
    print("  JAMMULA UDAY KIRAN — GITHUB PROFILE README E2E QUALITY TEST SUITE")
    print("  Opaque-Box Deterministic Verification Matrix (Tiers 1 - 4)")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for description, module in MODULES:
        mod_suite = loader.loadTestsFromModule(module)
        suite.addTests(mod_suite)

    total_loaded = suite.countTestCases()
    print(f"\nDiscovered {total_loaded} test cases across {len(MODULES)} test modules.\n")

    result = TierTrackingResult(verbose=verbose)
    start_time = time.perf_counter()

    # Run tests module by module to invoke setUpClass and tearDownClass properly
    for description, module in MODULES:
        print(f"▶ Running {description} ...")
        mod_suite = loader.loadTestsFromModule(module)
        mod_suite.run(result)

    total_time = time.perf_counter() - start_time

    # Print Summary Tables
    print("\n" + "=" * 80)
    print("  4-TIER COVERAGE SUMMARY")
    print("=" * 80)
    print(f"{'Tier':<35} | {'Run':<6} | {'Pass':<6} | {'Fail':<6} | {'Error':<6} | {'Skip':<6}")
    print("-" * 75)
    for tier_name, stats in result.tier_stats.items():
        print(
            f"{tier_name:<35} | {stats['run']:<6} | {stats['pass']:<6} | "
            f"{stats['fail']:<6} | {stats['error']:<6} | {stats['skip']:<6}"
        )

    print("\n" + "=" * 80)
    print("  MODULE BREAKDOWN SUMMARY")
    print("=" * 80)
    print(f"{'Module':<35} | {'Run':<6} | {'Pass':<6} | {'Fail':<6} | {'Error':<6} | {'Skip':<6}")
    print("-" * 75)
    for mod_name, stats in result.module_stats.items():
        short_name = mod_name.split(".")[-1]
        print(
            f"{short_name:<35} | {stats['run']:<6} | {stats['pass']:<6} | "
            f"{stats['fail']:<6} | {stats['error']:<6} | {stats['skip']:<6}"
        )

    # Detailed Failures & Errors
    if result.failures:
        print("\n" + "!" * 80)
        print(f"  FAILURES ({len(result.failures)})")
        print("!" * 80)
        for test, traceback in result.failures:
            print(f"\n[FAIL] {test.id()}")
            print("-" * 60)
            print(traceback.strip())

    if result.errors:
        print("\n" + "!" * 80)
        print(f"  ERRORS ({len(result.errors)})")
        print("!" * 80)
        for test, traceback in result.errors:
            print(f"\n[ERROR] {test.id()}")
            print("-" * 60)
            print(traceback.strip())

    print("\n" + "=" * 80)
    total_passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    print(
        f"TOTAL: {result.testsRun} run | {total_passed} passed | "
        f"{len(result.failures)} failed | {len(result.errors)} errors | "
        f"{len(result.skipped)} skipped  in {total_time:.2f}s"
    )
    print("=" * 80)

    # Return exit code
    return 1 if (result.failures or result.errors) else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master E2E Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose test execution output")
    args = parser.parse_args()
    sys.exit(run_all(verbose=args.verbose))
