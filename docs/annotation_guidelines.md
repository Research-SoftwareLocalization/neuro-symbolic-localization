# Linguistic Annotation Guidelines and Dual-Pass Workflow
**Benchmark Resource:** OPUS KDE4v2 500-String Gold Evaluation Subset ($N=500$)  
**Framework:** Invariant-Guided Self-Correction (IGSC) and Multidimensional Quality Metrics (MQM)  
**Target Locales:** German, Spanish, French, Hindi, Telugu, Marathi

## 1. Six-Stratum IGSC Fitment Architecture
1. **S1: Parameterized Strings (`%1`, `%s`, `{var}`)** — $n=110$ (audits $\mathcal{I}_{ph}$ multiset parity).
2. **S2: Accelerators & Inline Markup (`&`, XML)** — $n=80$ (audits $\mathcal{I}_{acc}$ mnemonics & entities).
3. **S3: Technical & Compound Identifiers (NTT)** — $n=50$ (audits $\mathcal{I}_{ntt}$ whitelisting vs. copy-fallback).
4. **S4: Extended Tooltips & Dialogs (>10 words)** — $n=50$ (audits $\mathcal{I}_{chat}$ & multi-clause adequacy).
5. **S5: Medium UI Phrases (4–10 words)** — $n=90$ (audits $\mathcal{I}_{script}$ purity & postpositional inflection).
6. **S6: Short Variable-Free UI Labels (1–3 words)** — $n=120$ (audits context-starved accuracy & $\mathcal{I}_{enc}$).

## 2. Dual-Pass Localization Protocol
* **Step 1 (Primary Native Linguist):** Translates Column H in `Translation_Workspace_500` and sets Column I to `Translated (Step 1)`.
* **Step 2 (Senior Reviewer):** Audits Column H against source & `auto_qa_check` (Column K), setting Column I to `Dual-Verified (Step 2)`.

## 3. Four-Tier MQM Severity Rubric (`MQM_IAA_Subsample_50`)
* **No Error (Pass) [0.0]:** Fully accurate, fluent, and invariant-compliant.
* **Minor Fluency/Style [1.0]:** Stylistic or punctuation nuance that does not impair UI comprehension.
* **Major Adequacy/Terminology [5.0]:** Semantic drift or domain terminology error affecting comprehension.
* **Critical Invariant Defect [25.0]:** Build-breaking or runtime-crashing syntax defect (`%1`, `&`, entity, or foreign script).
