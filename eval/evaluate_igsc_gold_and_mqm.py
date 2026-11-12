#!/usr/bin/env python3
"""End-to-End Evaluation & Inter-Annotator Agreement (IAA) Suite for KDE4v2 Gold-500 & MQM-50."""
import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List
import numpy as np
import openpyxl
import pandas as pd

MQM_CATEGORIES = [
    "No Error (Pass)",
    "Minor Fluency/Style",
    "Major Adequacy/Terminology",
    "Critical Invariant Defect",
]
MQM_PENALTY_WEIGHTS = {
    "No Error (Pass)": 0.0,
    "Minor Fluency/Style": 1.0,
    "Major Adequacy/Terminology": 5.0,
    "Critical Invariant Defect": 25.0,
}
R_PH = re.compile(r"%\d+|%[sdioxXufFeEgGaAcspnBMyY]|\{[^\}]+\}")
FORBIDDEN_RANGES = [(0x4E00, 0x9FFF), (0xAC00, 0xD7AF), (0x0400, 0x04FF), (0x0600, 0x06FF)]

def check_script_purity(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in FORBIDDEN_RANGES):
            return False
    return True

def validate_and_export_gold(excel_path: str, manifest_path: str = "data/sampling_manifest.json", export_txt_path: str = None) -> List[str]:
    df = pd.read_excel(excel_path, sheet_name="Translation_Workspace_500", keep_default_na=False).sort_values("subset_index")
    if len(df) != 500:
        raise ValueError(f"Expected 500 rows in {excel_path}, found {len(df)}.")
    if Path(manifest_path).exists():
        expected_idx = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["sampled_indices_0based"]
        if [int(x) for x in df["original_index_0based"].tolist()] != expected_idx:
            raise ValueError("original_index_0based column does not match sampling_manifest.json!")
    t_col = [c for c in df.columns if c.startswith("target_translation")][0]
    gold_lines, warnings = [], []
    for _, row in df.iterrows():
        sub_i, src, tgt = int(row["subset_index"]), str(row["source_text"]).strip(), str(row[t_col]).strip()
        if not tgt:
            raise ValueError(f"Empty translation at subset_index={sub_i}.")
        if "\n" in tgt or "\r" in tgt:
            raise ValueError(f"Internal newline at subset_index={sub_i}.")
        if "\ufffd" in tgt:
            warnings.append(f"[subset_index {sub_i}] Contains U+FFFD replacement character.")
        if sorted(R_PH.findall(src)) != sorted(R_PH.findall(tgt)):
            warnings.append(f"[subset_index {sub_i}] Placeholder multiset mismatch.")
        if not check_script_purity(tgt):
            warnings.append(f"[subset_index {sub_i}] Foreign script codepoint detected.")
        gold_lines.append(tgt)
    print(f"[QA AUDIT] {excel_path}: {len(warnings)} warning(s)." if warnings else f"[QA AUDIT] {excel_path}: All 500 segments passed.")
    if export_txt_path:
        Path(export_txt_path).parent.mkdir(parents=True, exist_ok=True)
        Path(export_txt_path).write_text("\n".join(gold_lines) + "\n", encoding="utf-8")
        print(f"[EXPORT] Wrote 500 gold references -> {export_txt_path}")
    return gold_lines

def evaluate_bleu_chrf(excel_or_gold_txt: str, full_model_predictions_txt: str, manifest_path: str = "data/sampling_manifest.json", total_expected_lines: int = 10228) -> Dict[str, object]:
    import sacrebleu
    full_preds = Path(full_model_predictions_txt).read_text(encoding="utf-8").splitlines()
    if len(full_preds) != total_expected_lines:
        raise ValueError(f"Expected {total_expected_lines} lines in {full_model_predictions_txt}, got {len(full_preds)}.")
    if excel_or_gold_txt.endswith(".xlsx"):
        df = pd.read_excel(excel_or_gold_txt, sheet_name="Translation_Workspace_500", keep_default_na=False).sort_values("subset_index")
        indices = [int(i) for i in df["original_index_0based"].tolist()]
        t_col = [c for c in df.columns if c.startswith("target_translation")][0]
        gold_refs = [str(x).strip() for x in df[t_col].tolist()]
    else:
        indices = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["sampled_indices_0based"]
        gold_refs = [line.strip() for line in Path(excel_or_gold_txt).read_text(encoding="utf-8").splitlines()]
    subset_preds = [full_preds[i].strip() for i in indices]
    bleu = sacrebleu.corpus_bleu(subset_preds, [gold_refs])
    chrf = sacrebleu.corpus_chrf(subset_preds, [gold_refs])
    chrf_pp = sacrebleu.corpus_chrf(subset_preds, [gold_refs], word_order=2)
    return {"n_segments": len(gold_refs), "BLEU": round(bleu.score, 2), "chrF": round(chrf.score, 2), "chrF++": round(chrf_pp.score, 2)}

def cohen_kappa_with_ci(labels_a: List[str], labels_b: List[str], categories: List[str] = MQM_CATEGORIES, weights: str = None) -> Dict[str, float]:
    n, k = len(labels_a), len(categories)
    cat_to_idx = {c: idx for idx, c in enumerate(categories)}
    conf = np.zeros((k, k), dtype=float)
    for a, b in zip(labels_a, labels_b):
        conf[cat_to_idx[a], cat_to_idx[b]] += 1.0
    p_mat = conf / n
    row_m, col_m = p_mat.sum(axis=1), p_mat.sum(axis=0)
    exp_mat = np.outer(row_m, col_m)
    w_mat = np.zeros((k, k), dtype=float)
    for i in range(k):
        for j in range(k):
            w_mat[i, j] = (0.0 if i == j else 1.0) if weights is None else (abs(i - j) / (k - 1) if weights == "linear" else ((i - j) ** 2) / ((k - 1) ** 2))
    obs_d, exp_d = float(np.sum(w_mat * p_mat)), float(np.sum(w_mat * exp_mat))
    p_o, p_e = 1.0 - obs_d, 1.0 - exp_d
    if math.isclose(exp_d, 0.0, abs_tol=1e-12):
        kappa, se = (1.0 if math.isclose(obs_d, 0.0, abs_tol=1e-12) else 0.0), 0.0
    else:
        kappa = 1.0 - (obs_d / exp_d)
        abar_i, abar_j = w_mat @ col_m, w_mat.T @ row_m
        term_sum = sum(p_mat[i, j] * ((1.0 - w_mat[i, j]) - ((1.0 - abar_i[i]) + (1.0 - abar_j[j])) * (1.0 - kappa)) ** 2 for i in range(k) for j in range(k))
        var_k = (term_sum - ((kappa - p_e * (1.0 - kappa)) ** 2)) / (n * (exp_d ** 2))
        se = math.sqrt(max(0.0, var_k))
    return {"n": n, "P_o": round(p_o, 4), "P_e": round(p_e, 4), "kappa": round(kappa, 4), "se": round(se, 4), "ci95_low": round(max(-1.0, kappa - 1.96 * se), 4), "ci95_high": round(min(1.0, kappa + 1.96 * se), 4)}

def evaluate_mqm_sheet(excel_path: str) -> Dict[str, object]:
    df = pd.read_excel(excel_path, sheet_name="MQM_IAA_Subsample_50", skiprows=3, keep_default_na=False).sort_values("mqm_index")
    comp = df[(df["annotator_1_mqm_label"].astype(str).str.strip() != "") & (df["annotator_2_mqm_label"].astype(str).str.strip() != "")]
    if len(comp) == 0:
        raise ValueError(f"No completed dual annotations in {excel_path}.")
    a1 = comp["annotator_1_mqm_label"].astype(str).str.strip().tolist()
    a2 = comp["annotator_2_mqm_label"].astype(str).str.strip().tolist()
    unw = cohen_kappa_with_ci(a1, a2, weights=None)
    mean_pen = float(np.mean([(MQM_PENALTY_WEIGHTS[x] + MQM_PENALTY_WEIGHTS[y]) / 2.0 for x, y in zip(a1, a2)]))
    return {
        "file": excel_path, "evaluated_segments": len(comp), "raw_agreement_pct": round(unw["P_o"] * 100.0, 2),
        "cohen_kappa_unweighted": unw, "cohen_kappa_linear": cohen_kappa_with_ci(a1, a2, weights="linear"),
        "cohen_kappa_quadratic": cohen_kappa_with_ci(a1, a2, weights="quadratic"), "mean_mqm_penalty_per_segment": round(mean_pen, 3),
    }

def populate_mqm_model_outputs(excel_path: str, full_model_txt_path: str, output_excel_path: str = None) -> str:
    full_preds = Path(full_model_txt_path).read_text(encoding="utf-8").splitlines()
    if len(full_preds) != 10228:
        raise ValueError(f"Expected 10,228 lines in {full_model_txt_path}, found {len(full_preds)}.")
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["MQM_IAA_Subsample_50"]
    for row_idx in range(5, 55):
        orig_idx0 = int(ws.cell(row=row_idx, column=3).value)
        cell = ws.cell(row=row_idx, column=7, value=str(full_preds[orig_idx0]))
        cell.number_format = "@"
    save_path = output_excel_path or excel_path
    wb.save(save_path)
    print(f"[MQM PREP] Populated 50 model predictions into {save_path}")
    return save_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KDE4v2 Gold-500 & MQM-50 Evaluation Pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_val = sub.add_parser("validate")
    p_val.add_argument("--excel", required=True)
    p_val.add_argument("--manifest", default="data/sampling_manifest.json")
    p_val.add_argument("--export-txt", default=None)
    p_sc = sub.add_parser("score")
    p_sc.add_argument("--gold", required=True)
    p_sc.add_argument("--pred", required=True)
    p_sc.add_argument("--manifest", default="data/sampling_manifest.json")
    p_mqm = sub.add_parser("mqm-iaa")
    p_mqm.add_argument("--excel", nargs="+", required=True)
    p_prep = sub.add_parser("prep-mqm")
    p_prep.add_argument("--excel", required=True)
    p_prep.add_argument("--pred", required=True)
    p_prep.add_argument("--out", default=None)
    args = parser.parse_args()
    if args.cmd == "validate":
        validate_and_export_gold(args.excel, args.manifest, args.export_txt)
    elif args.cmd == "score":
        print(json.dumps(evaluate_bleu_chrf(args.gold, args.pred, args.manifest), indent=2))
    elif args.cmd == "mqm-iaa":
        for p in args.excel:
            print(json.dumps(evaluate_mqm_sheet(p), indent=2))
    elif args.cmd == "prep-mqm":
        populate_mqm_model_outputs(args.excel, args.pred, args.out)
