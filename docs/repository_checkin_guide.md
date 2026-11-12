# Repository Check-In and Provenance Guide

## 1. Replication Package Layout
```text
neuro-symbolic-localization/
├── data/
│   ├── source_full_10228.txt
│   ├── source_500.txt
│   ├── sampling_manifest.json
│   └── references/
├── workbooks/
│   ├── kde_igsc_gold_500_de.xlsx
│   ├── kde_igsc_gold_500_es.xlsx
│   ├── kde_igsc_gold_500_fr.xlsx
│   ├── kde_igsc_gold_500_hi.xlsx
│   ├── kde_igsc_gold_500_te.xlsx
│   ├── kde_igsc_gold_500_bn.xlsx
├── src/ & scripts/             # Core IGSC verifier, TM cache, conformal router & runner
├── eval/
│   └── evaluate_igsc_gold_and_mqm.py
└── docs/
    ├── annotation_guidelines.md
    └── repository_checkin_guide.md
```

## 2. Reproducibility & Double-Blind Hygiene
* **Source SHA-256:** `464d65825b81856c4cb600638fca87c3b3abc1692239679e1ec093677bfe281f` ($N=10,228$ Unix-LF UI strings).
* **Deterministic Seed:** `seed = 42` maps `subset_index` `0..499` to exact 0-based catalog lines.
