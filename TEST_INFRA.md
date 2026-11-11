# Test Infrastructure & E2E Quality Gate Architecture

**Target Repository**: `Udaykiranjammula-alpha/Udaykiranjammula-alpha`  
**Engineer Portfolio**: Jammula Uday Kiran (Systems, Forensics, Edge AI)  
**Standard**: Opaque-Box Deterministic End-to-End Quality Verification  
**Dependencies**: Python 3.11+ Standard Library (Zero External Packages)

---

## 1. Test Philosophy

The testing infrastructure implements strict opaque-box verification for a production GitHub profile README ecosystem. The testing philosophy is governed by five foundational principles:

1. **Deterministic Execution**: Tests produce identical, reproducible results regardless of host OS (Windows, Linux, macOS). Non-deterministic attributes (such as network latency or timestamp generation) are isolated and bounded with deterministic fallbacks.
2. **Zero Third-Party Dependencies**: All tests run directly on vanilla Python 3.11+ utilizing standard modules (`unittest`, `xml.etree.ElementTree`, `html.parser`, `urllib.request`, `json`, `re`, `pathlib`, `subprocess`). No external package installation (`pip`) is required.
3. **Spec-Driven Ground Truth (No Facades)**: Tests validate against authoritative specifications mined in `ORIGINAL_REQUEST.md` and `PROJECT.md`. Tests never act as facades or mirror broken implementation artifacts; implementation flaws (such as malformed XML or broken links) result in explicit test failures.
4. **Adversarial & Boundary Rigor**: Tests subject components to adversarial inputs including unescaped XML meta-characters (`<`, `>`, `&`), mobile viewport constraints ($360\text{px}$), malformed telemetry payloads, and broken tag pairings.
5. **Progressive Testability & Isolation**: Each test module operates independently, manages its own temporary state, and cleans up artifacts without relying on execution sequence.

---

## 2. 13-Feature Inventory

The test suite provides complete, end-to-end verification for all 13 features defined in `PROJECT.md` across Requirements R1–R4:

| Feature ID | Feature Name | Domain | Requirements | Primary Test Suite | Description & Scope |
|:---|:---|:---|:---|:---|:---|
| **F01** | Tokyo Night HUD Info Card | SVG Rendering | R1 (AC 1.1, AC 1.2) | `test_svg_assets.py` | Validates `assets/info-card.svg` XML syntax, responsive `viewBox="0 0 490 290"`, dark container background, and monospace text styling. |
| **F02** | Systems Architecture Core Radar | SVG Rendering | R1 (AC 1.1, AC 1.2) | `test_svg_assets.py` | Validates `assets/tech-core.svg` XML parsing, `viewBox="0 0 370 280"`, hexagonal nodes, and contrast integrity across dark/light themes. |
| **F03** | Well-Formed Matrix Rain SVG | SVG Rendering | R1 (AC 1.1) | `test_svg_assets.py` | Validates `assets/matrix-rain.svg` XML well-formedness, character escaping (`&lt;`, `&gt;`), viewBox scaling, and vector animation elements. |
| **F04** | Tokyo Night Heatmap Renderer | Telemetry Scripts | R1 (AC 1.1), R3 (AC 3.1) | `test_workflows.py`, `test_svg_assets.py` | Validates `scripts/render_heatmap.py` CLI execution, Tokyo Night color palette levels 0–4, viewBox `860x216`, and atomic file generation. |
| **F05** | FileDNA 2.0 Engineering Dossier | Technical Rigor | R2 (AC 2.1) | `test_gfm_markdown.py` | Validates Shannon entropy formula $H(X)$, 5-tier classification matrix (0.0–8.0 bits/byte), magic bytes (PNG/PDF/EXE/ZIP), and concurrent multi-hash pipeline. |
| **F06** | ESP32 Distributed ML Accelerator | Technical Rigor | R2 (AC 2.2) | `test_gfm_markdown.py` | Validates 4-node cluster topology (Master, Workers, Aggregator), INT8 affine quantization, SRAM budget (<520 KB), and ring buffer latency (~1.2ms). |
| **F07** | Uday AI Local Server Dossier | Technical Rigor | R2 (AC 2.3) | `test_gfm_markdown.py` | Validates `/tmp/llm.sock` Unix socket architecture, llama.cpp backend, `mmap()` weight loading, Q4_K_M/Q8_0 RAM footprints, and ~18 tok/s benchmarks. |
| **F08** | Systems Profile Visual Polish & Badges | GFM & Typography | R1 (AC 1.2), R2 | `test_gfm_markdown.py` | Validates terminal dossiers (`cat /etc/engineer.profile`), collapsible `<details>` cards, Shields.io badges, and typography balance. |
| **F09** | GitHub Actions Workflow Hardening | CI/CD Automation | R3 (AC 3.1) | `test_workflows.py` | Validates `.github/workflows/*.yml` YAML syntax, cron schedules with jittered minutes, `workflow_dispatch`, and scoped `permissions: contents: write`. |
| **F10** | Workflow Idempotency & Script Health | Automation | R3 (AC 3.1) | `test_workflows.py` | Validates `git diff --quiet` clean commit logic, `github-actions[bot]` config, `[skip ci]`, and deterministic zero-diff rerun behavior. |
| **F11** | Complete URL & Link Resolution Gate | Link Integrity | R4 (AC 4.1) | `test_links.py` | Validates 100% of relative filesystem asset paths and performs HTTP 200 checks on external endpoints with custom User-Agent. |
| **F12** | GFM & HTML Tag Balance Gate | Markdown Integrity | R4 (AC 4.2) | `test_gfm_markdown.py` | Validates 0 unclosed or mismatched HTML tags via AST parser, valid GFM table structure, code fence language identifiers, and image syntax. |
| **F13** | SVG Well-Formedness & Theme Gate | Quality Gate | R1 (AC 1.1), R4 | `test_svg_assets.py` | Validates 100% XML parse compliance across all SVGs, viewBox bounds, absence of forbidden tags (`<script>`, `<foreignObject>`), and contrast guarantees. |

---

## 3. 4-Tier Test Architecture

The testing framework organizes tests into 4 progressive tiers of validation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 4: REAL-WORLD SCENARIOS                        │
│   • Full Recruiter End-to-End Browsing Journey                         │
│   • GitHub Actions Automated Telemetry Run & Commit Simulation         │
├────────────────────────────────────────────────────────────────────────┤
│                TIER 3: CROSS-FEATURE INTEGRATION                       │
│   • Markdown + Local SVG Asset Embedding Binding                       │
│   • Dark/Light Theme Resilience & Self-Contained Contrast Guarantee   │
│   • Telemetry Pipeline End-to-End: JSON -> Heatmap Generator -> SVG    │
├────────────────────────────────────────────────────────────────────────┤
│                 TIER 2: BOUNDARY & CORNER CASES                        │
│   • XML Special Character Escaping (&, <, >, ", ')                     │
│   • Monospace Text Boundary Safety Buffers (>=20px from right margin)  │
│   • Responsive Mobile Scaling (ViewBox down to 360px viewport)         │
│   • Corrupted / Empty Telemetry JSON Error Handling                    │
├────────────────────────────────────────────────────────────────────────┤
│                   TIER 1: CORE FEATURE COVERAGE                        │
│   • >=5 Dedicated Test Cases Per Feature Across F01 - F13              │
│   • XML Well-Formedness, YAML Syntax, HTML Tag AST Balancing           │
│   • Link Resolution, Dossier Mathematical Specs, Workflow Permissions  │
└────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Core Feature Coverage
- Ensures at least 5 test cases per feature across R1–R4 (over 65 core feature tests).
- Verifies every component functions in accordance with its base contract.

### Tier 2: Boundary & Corner Cases
- Tests extreme values, edge conditions, and error triggers:
  - Empty or null inputs in telemetry parsing.
  - Viewport compression down to $360\text{px}$ mobile screens.
  - Text overflowing bounding boxes and monospace font width variances.
  - Character entity escaping (`<`, `>`, `&`, quotes) inside XML text nodes.
  - Malformed table delimiters or unescaped pipe characters in markdown.

### Tier 3: Cross-Feature Integration
- Tests interactions between separate components:
  - Embedding of generated SVGs within Markdown HTML blocks and tables.
  - Contrast guarantees of Tokyo Night SVGs when viewed against dark (`#0d1117`) and light (`#ffffff`) GitHub interfaces.
  - Verification that GitHub Actions workflow commands align with actual script CLI parameters (`--input`, `--output`).

### Tier 4: Real-World Scenarios
- End-to-End Recruiter Browsing Journey: Simulates a technical recruiter or engineering manager navigating from the header, reading dossiers, inspecting architectures, checking live metrics, and verifying project repository links.
- Automated Daily Telemetry Cycle: Simulates the scheduled GitHub Actions telemetry run, verifying input ingestion, SVG generation, diff detection, and commit preparation.

---

## 4. Test Directory Layout

```
hopeful-carson/
├── TEST_INFRA.md                   # This test architecture specification
├── TEST_READY.md                   # Test suite publication & execution checklist
├── tests/
│   ├── __init__.py                 # Test package initialization
│   ├── test_svg_assets.py          # SVG XML parser, viewBox, Tokyo Night colors, contrast
│   ├── test_links.py               # Local file resolution & external HTTP 200 network probe
│   ├── test_gfm_markdown.py        # HTML tag balancer, GFM tables, code fences, dossiers
│   ├── test_workflows.py           # GitHub Actions YAML syntax, permissions, script dry-runs
│   └── run_all_tests.py            # Master runner aggregating all 4 tiers with formatted report
├── assets/                         # Vector assets under test
├── scripts/                        # Telemetry generators under test
├── .github/workflows/              # CI/CD workflow YAML files under test
└── README.md                       # Profile portfolio under test
```

---

## 5. Execution & Verification Guide

### Master Runner (Recommended)
Executes all test modules across all 4 tiers, outputs structured progress, and generates a tier-by-tier summary table:
```bash
python tests/run_all_tests.py
```

### Standard Python Unittest Discovery
Runs standard discovery across the `tests/` directory:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Individual Test Suites
```bash
# Run SVG assets test suite
python -m unittest tests/test_svg_assets.py -v

# Run Link & URL resolution test suite
python -m unittest tests/test_links.py -v

# Run GFM markdown & tag balancer test suite
python -m unittest tests/test_gfm_markdown.py -v

# Run GitHub Actions workflow test suite
python -m unittest tests/test_workflows.py -v
```

---

## 6. Quality Thresholds & Acceptance Criteria

| Metric | Target / Threshold | Enforcement Mechanism |
|:---|:---|:---|
| **Feature Coverage** | $\ge 5$ test cases per feature (F01–F13) | Tier 1 test inventory verification |
| **SVG XML Well-Formedness** | 100% of SVGs parse with 0 errors | `xml.etree.ElementTree` strict parser |
| **SVG Responsive Scaling** | 100% SVGs declare valid `viewBox` | Attribute presence and geometry check |
| **HTML Tag Balance** | 0 unclosed / 0 mismatched tags | AST `HTMLParser` stack validation |
| **Local Asset Resolution** | 100% referenced files exist on disk | Filesystem path verification |
| **External URL Resolution** | 100% return HTTP 200 (or valid redirect) | Multi-threaded HTTP probe with User-Agent |
| **Workflow Permissions** | Least-privilege `contents: write` | YAML attribute inspection |
| **Telemetry Idempotency** | 0 diff on identical data execution | Re-run output byte comparison |
