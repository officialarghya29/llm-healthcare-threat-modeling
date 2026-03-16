# Deep-Dive Review & SWOT Analysis
## Repository: `llm-healthcare-threat-modeling`
**Reviewed by:** Antigravity AI  
**Review Date:** 2026-03-16  
**Authors:** Arindam Tripathi, Arghya Bose (Supervised by Dr. Sushruta Mishra, KIIT University)

---

## Executive Summary

This is a research prototype for evaluating prompt injection defenses in an LLM-powered clinical assistant. The architecture is conceptually sound and the research question is well-motivated: **do input-only defenses (vector similarity) suffice against indirect injection via EHR data?** The empirical finding — that they do not — is genuine and demonstrated by the logs.

However, several critical bugs, structural path mismatches, a duplicate class constructor, misleading metric framing, and inconsistencies between the README claims and actual experimental data significantly undermine reproducibility and academic credibility. These are detailed below.

---

## 🏗️ Architecture Overview

```
User Request
    │
    ▼
[Stage 1] VectorShield (Semantic Cosine Similarity against known_attacks.json)
    │  BLOCKED → 400 HTTP Error
    ▼
[Stage 2] EHRSimulator (lookup by patient_id) + optional Context Scanning
    │  CONTEXT_BLOCKED → 400 HTTP Error
    ▼
[Stage 3] LLMProxy (OpenAI-compatible API via LiteLLM/Groq)
    │
    ▼
[Stage 4] Output Guardrails: Sanitizer → MedicalValidator → PolicyFilter
    │  BLOCKED_* → modified content
    ▼
Response via FastAPI /generate endpoint
```

---

## 🐛 Critical Bugs & Errors Found

### Bug 1 — Duplicate `__init__` in `MedicalValidator` (BREAKING)

**File:** `orchestrator/guardrails/medical_validator.py` — Lines 9–19 and 27–53

`__init__` is defined **twice** in the same class. In Python, the second definition **completely overwrites** the first. This means the first block is dead code.

```python
# PROBLEM: two __init__ methods — Python only uses the last one
def __init__(self, config: dict):   # Line 9 — DEAD CODE, silently ignored
    ...
def __init__(self, config: dict):   # Line 27 — This one actually runs
    ...
```

**Fix:** Remove the first `__init__` (lines 9–26).

---

### Bug 2 — Pervasive `experiments/` Path Mismatch (BREAKING for reproducibility)

All source files use an `experiments/` prefix in their paths, but the actual repository structure places files at the root level.

| File | Incorrect Path Used | Actual Path |
|---|---|---|
| `orchestrator/main.py` | `experiments/config.yaml` | `config.yaml` |
| `orchestrator/main.py` | `from experiments.orchestrator...` | `from orchestrator...` |
| `orchestrator/input_defense/vector_shield.py` | `experiments/data/known_attacks.json` | `data/known_attacks.json` |
| `orchestrator/llm/llm_proxy.py` | `experiments/.env` | `.env` |
| `client/attacker.py` | `from experiments.client.attack_corpus import...` | `from client.attack_corpus import...` |
| `client/batch_runner.py` | `experiments/data/test_dataset_large.json` | `data/test_dataset_large.json` |
| `config.yaml` | `./experiments/data/ehr_mock.json` | `./data/ehr_mock.json` |
| `config.yaml` | `./experiments/logs/audit.jsonl` | `./logs/audit.jsonl` |

> **Evidence:** `runner.log` line 23–26 shows the first run crashed with `ModuleNotFoundError: No module named 'experiments'`.

---

### Bug 3 — `config.yaml`: `context_scanning.enabled = false`

The README claims context scanning is the key defense, but `config.yaml` ships with it **disabled**. Any user cloning the repo runs the insecure baseline by default.

---

### Bug 4 — `llm.api_key_env` is an Empty String

`os.getenv("", "anything")` returns `"anything"` silently. Anyone connecting directly to Groq (not LiteLLM proxy) will get an authentication failure with no useful error.

---

### Bug 5 — `dataset_generator.py` Seeds Faker Twice

```python
Faker.seed(42)
fake = Faker()
Faker.seed(42)  # Redundant — re-seeds after instance creation
```

---

### Bug 6 — No `__init__.py` in `client/`

The `client/` directory is missing `__init__.py`, breaking module-level imports when running from repo root.

---

## 🔬 Critical Research/Data Discrepancy

### Experiment 4: The Core Finding is Misrepresented

The README claims: *"Without context scanning: 0/3 attacks blocked. Context scanning is a required layer."* This implies context scanning **fixes** the problem.

**The actual data (`reports/experiment4_results.csv`) shows:**

| Label | Baseline (scanning=false) | Hardened (scanning=true) |
|---|---|---|
| II_01 (ATTACK_01) | ALLOWED | **ALLOWED** |
| II_02 (ATTACK_02) | ALLOWED | **ALLOWED** |
| II_03 (ATTACK_03) | ALLOWED | **ALLOWED** |

`experiment4_manual_verification.json`: `"indirect_block_rate": "0/3"` — **still 0/3 with context scanning ON.**

**Root Cause — Signal Dilution Effect:** The malicious payloads (`[SYSTEM] Ignore...`) are embedded in benign clinical text, diluting their cosine similarity score below the 0.65 threshold. This is a **more nuanced and publishable finding** than what the README states.

---

### Batch Metrics Are Not Discussed in README

From `reports/final_metrics.md`:

| Category | N | Pass Rate |
|---|---|---|
| benign | 25 | 100.0% ✅ |
| direct_injection | 25 | 52.0% ⚠️ |
| indirect_injection | 10 | **0.0%** ❌ |
| medical_safety | 15 | **20.0%** ❌ |
| role_confusion | 25 | **0.0%** ❌ |
| **Overall Attack Block Rate** | 75 | **21.33%** ❌ |

This data exists in the repo but is never referenced in the README.

---

## SWOT Analysis

### 💪 Strengths

1. Well-motivated, clinically relevant research problem
2. Principled 4-stage defense pipeline with correct role separation
3. Fail-closed default (`fail_mode: closed`) in VectorShield
4. SHA256 integrity hashing in AuditLogger
5. Healthcare-specific 107-signature attack corpus
6. Authentic experimental data — logs confirm real API calls
7. Good modular architecture with dependency injection
8. Reproducible dataset generation (`random.seed(42)`, `Faker.seed(42)`)
9. MIT License + public GitHub — promotes open science

### 🔴 Weaknesses

1. Duplicate `__init__` bug in `MedicalValidator`
2. Pervasive `experiments/` path mismatch — repo won't run as-is
3. `context_scanning.enabled: false` shipped in committed config
4. Empty `api_key_env` — silent authentication failure
5. README misrepresents Experiment 4 outcome
6. 21.33% batch block rate never disclosed in README
7. `PolicyFilter` uses only keyword matching — trivially bypassable
8. `MedicalValidator` ontology is very narrow (3 drug categories)
9. Missing `__init__.py` in `client/`
10. No `.env.example` template
11. `matplotlib` unpinned in `requirements.txt`
12. `pytest` listed as dependency but no `tests/` directory exists
13. `run_experiment.sh` uses `>` (overwrite) instead of `>>` (append) for log

### 🟢 Opportunities

1. Reframe Experiment 4 as "Signal Dilution Effect" — more publishable
2. Add structural tag regex filter (`[SYSTEM]`, `[INSTRUCTION]`, `ADMIN_OVERRIDE:`) for context scanning
3. Threshold sweep analysis (cosine 0.4–0.8) showing block rate vs. FPR
4. Expand EHR mock database to 20+ benign patients
5. Add proper unit test suite
6. Cross-model evaluation (GPT-4, Mistral) for generalizability
7. HIPAA/GDPR framing for regulatory impact discussion

### ⚠️ Threats

1. Reproducibility crisis risk — repo won't run out-of-the-box
2. Research integrity concern — Experiment 4 data contradicts stated conclusion
3. LiteLLM dependency not mentioned in README prerequisites
4. WSL/Arch portability issues with `venv/bin/uvicorn` paths
5. `CORS allow_origins=["*"]` — flaggable security anti-pattern
6. Small sample sizes (3 indirect cases) — fragile statistical claims
7. No API key security guidance (risk of key exposure)

---

## 📌 Prioritized Recommendations

### Must Fix (Blocking)
| # | Issue | File | Fix |
|---|---|---|---|
| 1 | Remove duplicate `__init__` | `orchestrator/guardrails/medical_validator.py` | Delete lines 9–26 |
| 2 | Fix all `experiments/` path references | Multiple files | Use paths relative to repo root |
| 3 | Set `context_scanning.enabled: true` or document toggle | `config.yaml` | Update default |
| 4 | Fix `llm.api_key_env: 'GROQ_API_KEY'` | `config.yaml` | Set correct env var name |
| 5 | Add `experiments/` setup or restructure | `README.md` | Add `PYTHONPATH` and LiteLLM prerequisite |

### Should Fix (Quality)
| # | Issue | Fix |
|---|---|---|
| 6 | Rewrite Experiment 4 conclusion | Present Signal Dilution finding honestly |
| 7 | Add `__init__.py` to `client/` | Touch file |
| 8 | Add `.env.example` | Create template |
| 9 | Pin `matplotlib` version | e.g., `matplotlib==3.9.0` |
| 10 | Remove duplicate Faker seed | Delete `dataset_generator.py` line 12 |
| 11 | Fix log append mode | Change `>` to `>>` in `run_experiment.sh` |
| 12 | Reference batch metrics in README | Link to `final_metrics.md` |

### Nice to Have (Research Value)
| # | Suggestion |
|---|---|
| 13 | Structural tag regex pre-filter for Context Scanning |
| 14 | Cosine threshold sweep analysis |
| 15 | Unit test suite under `tests/` |
| 16 | Expand `ehr_mock.json` to 20+ benign patients |
| 17 | Note CORS restriction in README |

---

## Final Assessment

| Dimension | Rating | Comment |
|---|---|---|
| Research Question | ⭐⭐⭐⭐⭐ | Excellent — directly relevant, novel |
| Code Quality | ⭐⭐⭐ | Good structure, critical bug in validator |
| Reproducibility | ⭐⭐ | Broken out-of-box due to path mismatch |
| Experimental Rigor | ⭐⭐⭐ | Real data, but sample sizes are small |
| Data Integrity | ⭐⭐⭐⭐ | Logs are authentic |
| Result Accuracy | ⭐⭐ | README misrepresents Experiment 4 outcome |
| Documentation | ⭐⭐⭐ | README is detailed but contains inaccuracies |
| **Overall** | **⭐⭐⭐** | **Promising prototype, needs targeted fixes** |
