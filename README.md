# Neuro-Symbolic Software Localization: Invariant-Guided Self-Correction (IGSC) for Cloud-Native Pipelines

Official research codebase and replication package for **"Invariant-Guided Self-Correction for Cloud-Native Software Localization Pipelines"**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![vLLM](https://img.shields.io/badge/vLLM-0.32.0-orange.svg)](https://github.com/vllm-project/vllm)

---

## Abstract

Localizing graphical user interfaces (GUIs) into diverse global languages requires strict adherence to both linguistic adequacy and executable software syntax. Unlike unconstrained prose translation, software UI strings contain positional format specifiers, keyboard mnemonic accelerators, markup entities, and technical identifiers whose corruption causes compilation failures or runtime crashes. 

This repository provides the complete implementation of **Invariant-Guided Self-Correction (IGSC)**, a reference-free closed-loop architecture that pairs deterministic software verification with large language model self-correction to eliminate structural defects without external oracle supervision.

---

## Key Features

1. **Deterministic Invariant Verification (`src/invariants.py`):**
   A linear-time verification engine auditing six formal software localization invariants:
   * $\mathcal{I}_{script}$: Orthographic script purity and digraphic boundary enforcement.
   * $\mathcal{I}_{ph}$: Positional placeholder multiset parity and failure decomposition ($E_{omit}$, $E_{halluc}$, $E_{mut}$).
   * $\mathcal{I}_{acc}$: Keyboard mnemonic accelerator preservation.
   * $\mathcal{I}_{enc}$: Subword byte-level UTF-8 decoding integrity ($U+FFFD$ suppression).
   * $\mathcal{I}_{chat}$: Zero conversational framing and preamble suppression.
   * $\mathcal{I}_{ntt}$: Semantic non-echoing with domain-aware non-translatable token whitelisting.

2. **IGSC Closed-Loop Repair Engine (`src/cascade.py`):**
   Dynamic prompt conditioning that translates programmatic validation failures into targeted diagnostic hints at temperature $T=0.0$.

3. **Dual-Paradigm Evaluation Suite (`eval/`):**
   Evaluation scripts combining deterministic Structural Pass Rates (SPR) with reference-free neural Quality Estimation (WMT22 CometKiwi).

---

## Repository Structure

```text
neuro-symbolic-localization/
├── data/               # Canonical benchmark corpora, sampling manifest, and gold references
│   ├── source_full_10228.txt
│   ├── source_500.txt
│   ├── sampling_manifest.json
│   └── references/
├── workbooks/          # Bilingual Excel translation & MQM IAA kits (de, es, fr, hi, te, bn)
├── src/                # Core modular neuro-symbolic architecture
│   ├── invariants.py   # Six formal deterministic invariant verifiers
│   ├── cache.py        # Three-tier Contextual Translation Memory
│   ├── router.py       # Split Conformal Risk Control calibration
│   └── cascade.py      # NMT gate + vLLM XGrammar logit-masking & IGSC loop
├── scripts/            # Execution orchestration scripts
├── eval/               # Gold-500 BLEU/chrF++ & MQM Cohen's Kappa IAA suite
├── docs/               # Linguistic annotation guidelines & check-in provenance
├── requirements.txt    # Pinned Python dependencies
├── LICENSE             # MIT Open-Source License
└── README.md           # Project documentation
```

## Quickstart & Evaluation CLI

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Validate completed bilingual workbook & export 500-line gold .txt
python eval/evaluate_igsc_gold_and_mqm.py validate \
  --excel workbooks/kde_igsc_gold_500_de.xlsx \
  --manifest data/sampling_manifest.json \
  --export-txt data/references/gold_de_500.txt

# 3. Score 10,228-line model predictions on the 500-string gold subset (BLEU, chrF, chrF++)
python eval/evaluate_igsc_gold_and_mqm.py score \
  --gold data/references/gold_de_500.txt \
  --pred outputs/repaired_llama_8b/de.txt \
  --manifest data/sampling_manifest.json

# 4. Compute Human MQM & Cohen's Kappa Inter-Annotator Agreement (n = 50)
python eval/evaluate_igsc_gold_and_mqm.py mqm-iaa \
  --excel workbooks/kde_igsc_gold_500_de.xlsx workbooks/kde_igsc_gold_500_te.xlsx
```

## Citation

```bibtex
@article{sharma2026neurosymbolic,
  title={Invariant-Guided Self-Correction for Cloud-Native Software Localization Pipelines: A 1.22-Million-Segment LLM Benchmark and Dual-Paradigm Evaluation Across High-Resource and Low-Resource Languages},
  author={Sharma, Neeraj Kumar and Panda, Subhrakanta and Neti, Lalita Bhanu Murthy},
  journal={Journal Submission (Q1)},
  year={2026}
}
```
