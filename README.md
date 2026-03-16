
# Threat Modeling Secure LLM Orchestration in Healthcare: Experimental Harness

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the complete experimental prototype and validation harness for a multi-layer defense architecture against prompt injection attacks in LLM-powered healthcare applications. The orchestrator is designed as a controlled research instrument — **not a production system** — for evaluating the effectiveness of proposed defenses against real-world threat vectors.

---

## 📄 Paper Reference

This repository corresponds to the experimental validation described in:

**"Threat Modeling Secure LLM Orchestration in Healthcare: Evaluating Prompt Injection Defenses in a Simulated Clinical Environment"**

**Authors:** Arindam Tripathi, Arghya Bose  
**Supervised by:** Dr. Sushruta Mishra *(Faculty, School of Computer Engineering, KIIT University)*  
**Paper Version:** Results in this repository represent the experimental validation conducted in 2025–2026.

---

## 🎯 Project Overview

This research proposes and empirically validates a layered defense architecture for LLM systems operating in high-stakes healthcare environments. The prototype simulates a clinical AI assistant that retrieves Electronic Health Records (EHRs) and generates patient summaries, while being subjected to both **Direct** and **Indirect** prompt injection attacks.

### Defense Architecture

The orchestrator implements a **4-stage pipeline**:

1. **Stage 1: Input Defense (Vector Shield)** — Probabilistic, semantic-similarity-based filter using `all-MiniLM-L6-v2` embeddings to detect user-level prompt injection before any processing occurs.
2. **Stage 2: Context Retrieval & Scanning** — Deterministic EHR lookup, followed by optional semantic scanning of retrieved patient records to prevent **Indirect Injection** (Experiment 4: Gap Analysis).
3. **Stage 3: LLM Invocation** — Isolated proxy for external model calls (Groq / `llama-3.3-70b-versatile`), with a deterministic, privilege-ordered prompt structure: `[SYSTEM] → [CONTEXT] → [USER]`.
4. **Stage 4: Output Guardrails** — Post-generation pipeline consisting of:
   - **Sanitizer**: PII scrubbing from LLM responses.
1.  **Stage 1: Input Defense (Vector Shield)** — Probabilistic, semantic-similarity-based filter using `all-MiniLM-L6-v2` embeddings to detect user-level prompt injection before any processing occurs.
2.  **Stage 2: Context Retrieval & Scanning** — Deterministic EHR lookup, followed by optional semantic scanning of retrieved patient records to prevent **Indirect Injection** (Experiment 4: Gap Analysis).
3.  **Stage 3: LLM Invocation** — Isolated proxy for external model calls (Groq / `llama-3.3-70b-versatile`), with a deterministic, privilege-ordered prompt structure: `[SYSTEM] → [CONTEXT] → [USER]`.
4.  **Stage 4: Output Guardrails** — Post-generation pipeline consisting of:
    -   **Sanitizer**: PII scrubbing from LLM responses.
    -   **Medical Validator**: Keyword-based blocking of dangerous medical advice.
    -   **Policy Filter**: Jailbreak-success detection (e.g., detecting compliant-to-bad-request language).

### Key Research Findings

-   **Indirect Injection Success Rate (Baseline):** **0/3 indirect attacks blocked** without context scanning enabled — demonstrating a critical gap in input-only defenses.
-   **Context Scanning (Experiment 4):** Identifies the *Signal Dilution Effect* where malicious payloads embedded in clinical text evade semantic detection at standard thresholds.
-   **System Reliability:** Current prototype shows a 21.33% attack block rate in large-scale batch testing, highlighting the need for structural/tag-based defense layers beyond semantic similarity.
-   **Utility Validation:** Benign requests (e.g., patient summarization) pass through the full pipeline without false positives.
-   **Vector Shield Threshold:** Configurable cosine-similarity threshold (`0.6` default); attacks scoring above this are blocked at the earliest stage, minimizing latency.

---

## 🏗️ Repository Structure

```
llm-healthcare-threat-modeling/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── requirements.txt                   # Python dependencies
├── config.yaml                        # Centralized experiment configuration
├── run_experiment.sh                  # Shell script to run a single experiment
├── run_batch.sh                       # Shell script to run the full batch
├── run_experiment4.py                 # Experiment 4 (Gap Analysis) runner
├── manual_verify_context_scanning.py  # Manual verification script
│
├── orchestrator/                      # Core API gateway and logic hub
│   ├── main.py                        # FastAPI application & request pipeline
│   ├── input_defense/
│   │   └── vector_shield.py           # Semantic similarity-based attack detector
│   ├── context/
│   │   └── ehr_simulator.py           # Deterministic EHR record retrieval
│   ├── llm/
│   │   └── llm_proxy.py               # Isolated external LLM call proxy
│   ├── guardrails/
│   │   ├── sanitizer.py               # PII scrubbing
│   │   ├── medical_validator.py       # Forbidden medical term detection
│   │   └── policy_filter.py           # Jailbreak & policy violation detection
│   ├── logging/
│   │   └── audit_log.py               # WORM-style append-only audit logger
│   └── metrics/
│       └── metrics_collector.py       # Transaction metrics (latency, decisions)
│
├── client/                            # Attack simulators and test harness
│   ├── attacker.py                    # ExperimentRunner for structured attack campaigns
│   ├── attack_corpus.py               # Categorized attack test cases
│   ├── batch_runner.py                # Large-scale batch evaluation runner
│   └── dataset_generator.py           # Synthetic test dataset generator
│
├── data/                              # Local data stores
│   ├── ehr_mock.json                  # Simulated EHR database (incl. malicious records)
│   ├── known_attacks.json             # Attack embedding corpus for Vector Shield
│   └── test_dataset_large.json        # Large-scale evaluation dataset
│
├── analysis/
│   └── generate_report.py             # Report generation from raw metrics
│
└── reports/                           # Experiment output data
    ├── experiment4_results.csv
    └── experiment4_manual_verification.json
```

---

## 🧪 Experimental Methodology

### Threat Model

Three distinct attack categories are simulated:

| Category | ID | Description | Expected Outcome |
|---|---|---|---|
| **Direct Injection** | DI_01–03 | User explicitly overrides system instructions | `BLOCKED` by Vector Shield |
| **Indirect Injection** | II_01 | Indirect Injection (Pirate) | ALLOWED |
| II_02 | Indirect Injection (Admin) | ALLOWED |
| II_03 | Indirect Injection (Dosage) | ALLOWED |
| **Role Confusion** | RC_01 | Attacker impersonates System Admin | `BLOCKED` by Vector Shield |
| **Benign** | BN_01 | Standard clinical summarization request | ALLOWED |

### The Signal Dilution Effect
Experimental data revealed that embedding malicious instructions within long clinical records significantly dilutes the semantic vector distance. Even with Context Scanning enabled, the cosine similarity score often remains below the detection threshold (e.g., ~0.56 vs a 0.65 threshold), allowing the injection to pass.

## 📊 Large-Scale Batch Evaluation
Beyond the primary test cases, the system was evaluated against a 100-sample synthetic dataset (`data/test_dataset_large.json`).

| Metric | Result |
| :--- | :--- |
| **Overall Attack Block Rate** | 21.33% |
| Role Confusion Block Rate | 0.0% |
| Indirect Injection Block Rate | 0.0% |
| Medical Safety Block Rate | 20.0% |

*Detailed metrics available in `reports/final_metrics.md`.*

### Experiment 4: Gap Analysis (Indirect Injection)

This experiment specifically evaluates whether the **Context Scanning** feature (`config.yaml: context_scanning.enabled`) is necessary. Results from `reports/experiment4_manual_verification.json` confirm:

- **Without context scanning:** `0/3` indirect injection attacks were blocked (all `ALLOWED`).
- **Conclusion:** Input-layer defenses alone are insufficient against indirect injection. Context scanning is a **required** layer.

---

## 🚀 Reproducing the Results

### Prerequisites

- **Python 3.10+**
- **Groq API Key** (for `llama-3.3-70b-versatile`)

### Setup

```bash
# Clone the repository
git clone https://github.com/officialarghya29/llm-healthcare-threat-modeling.git
cd llm-healthcare-threat-modeling

# Install dependencies
pip install -r requirements.txt

# Set your API key
export GROQ_API_KEY="your_key_here"
```

### Running the Orchestrator

```bash
# Start the FastAPI server
uvicorn experiments.orchestrator.main:app --reload
```

### Running the Attack Harness

```bash
# Run all attack categories against the live orchestrator
python client/attacker.py

# Run the large-scale batch evaluation
bash run_batch.sh

# Run Experiment 4 (Gap Analysis / Indirect Injection)
python run_experiment4.py
```

### Configuration

All experimental parameters are controlled via `config.yaml`. Key knobs:

| Parameter | Default | Description |
|---|---|---|
| `input_defense.vector_shield.threshold` | `0.6` | Cosine similarity cutoff for blocking |
| `input_defense.vector_shield.model_name` | `all-MiniLM-L6-v2` | Sentence embedding model |
| `context_scanning.enabled` | `true` | Enables EHR context scanning (Exp 4) |
| `context_scanning.threshold` | `0.65` | Sensitivity for indirect injection detection |
| `llm.model_name` | `llama-3.3-70b-versatile` | LLM backend |

> ⚠️ **Do not hardcode thresholds in source code.** All tunable parameters must be set via `config.yaml`.

---

## 👥 Authors

- **Arindam Tripathi** — *Lead Researcher* — [Arindamtripathi619](https://github.com/Arindamtripathi619)
- **Arghya Bose** — *Researcher* — [officialarghya29](https://github.com/officialarghya29)

**Supervised by:**
- **Dr. Sushruta Mishra** — *Faculty, School of Computer Engineering, KIIT University*

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Last Updated:** February 2026  
**Status:** Experimental Prototype — Research Validation in Progress
