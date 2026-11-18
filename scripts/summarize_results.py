#!/usr/bin/env python3
"""Gộp submission/results/*.json thành bảng so sánh + biểu đồ (ĐÃ VIẾT SẴN)."""
from __future__ import annotations

import json
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "submission/results"
METRICS = ["map50", "map50_95", "precision", "recall"]


def main():
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RES.glob("*_seed*.json"))]
    if not runs:
        raise SystemExit("chưa có kết quả trong submission/results/")
    by = defaultdict(list)
    for r in runs:
        by[r["variant"]].append(r)
    lines = ["| biến thể | #ảnh train | số seed | " + " | ".join(f"{m} (TB ± độ lệch)" for m in METRICS) + " |", "|---|---|---|" + "---|" * len(METRICS)]
    summary = {}
    for v in ["raw", "auto", "clean", "oracle"]:
        if v not in by:
            continue
        cells, summ = [], {}
        for m in METRICS:
            xs = [r[m] for r in by[v]]
            sd = st.stdev(xs) if len(xs) > 1 else 0.0
            cells.append(f"{st.mean(xs):.3f} ± {sd:.3f}")
            summ[m] = dict(mean=round(st.mean(xs), 4), std=round(sd, 4), values=xs)
        summary[v] = summ
        lines.append(f"| {v} | {by[v][0]['train_images']} | {len(by[v])} | " + " | ".join(cells) + " |")
    if "raw" in summary and "clean" in summary:
        d = summary["clean"]["map50"]["mean"] - summary["raw"]["map50"]["mean"]
        lines += ["", f"Chênh mAP50 (clean − raw) = **{d:+.3f}**."]
    (RES / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RES / "comparison.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n".join(lines))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        for k, m in enumerate(["map50", "map50_95"]):
            vs = [v for v in ["raw", "auto", "clean", "oracle"] if v in summary]
            ax[k].bar(vs, [summary[v][m]["mean"] for v in vs], yerr=[summary[v][m]["std"] for v in vs], capsize=4,
                      color=["#94a3b8", "#f59e0b", "#2563eb", "#16a34a"][: len(vs)])
            ax[k].set_title(m)
            ax[k].set_ylim(0, 1)
        fig.tight_layout()
        fig.savefig(RES / "comparison.png", dpi=140)
        print("đã ghi comparison.png")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
