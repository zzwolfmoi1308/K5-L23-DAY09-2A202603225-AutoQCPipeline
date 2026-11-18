"""Calibration: đo độ chính xác của CHÍNH CÔNG CỤ KIỂM trên bộ có lỗi cố ý đã biết (ĐÃ VIẾT SẴN).

Slide Day 09: "Script bắt đủ lỗi đã chèn thì mới đáng tin trên dữ liệu thật". `data/calib/` là 30+9 ảnh nhãn sạch
trong đó đã chèn lỗi cố ý; `data/calib/MANIFEST.csv` là ĐÁP ÁN (loại lỗi, ảnh, dòng).

    python -m pipeline.calibrate                                   # bảng precision/recall/F1 theo mã lỗi
    python -m pipeline.calibrate --sweep duplicates.phash_dist=2,4,6,8,10,12,16
    python -m pipeline.calibrate --sweep second_opinion.conf=0.25,0.4,0.5,0.6,0.7 --out submission/calibration

Cách chấm: mã lỗi cú pháp so theo (ảnh, dòng); mã còn lại so theo ảnh.
 TP: cờ đúng ảnh/dòng có lỗi chèn | FP: cờ ảnh KHÔNG có lỗi loại đó | FN: lỗi chèn mà không cờ.
(Ảnh sạch cũng có thể có lỗi tự nhiên do nhãn người/model lệch: vẫn tính FP — đó đúng là báo động giả mà người kiểm phải gánh.)
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import defaultdict

from . import checks
from .common import ROOT, Dataset, load_config

TYPE2CODE = {
    "MISSING_LABEL_FILE": "MISSING_LABEL_FILE", "BAD_CLASS_ID": "BAD_CLASS_ID", "BOX_OUT_OF_IMAGE": "BOX_OUT_OF_IMAGE",
    "BOX_ZERO": "BOX_ZERO", "BAD_FORMAT": "BAD_FORMAT", "DUP_BOX": "DUP_BOX", "BAD_CLASS_NAME": "BAD_CLASS_NAME",
    "DUP_IMAGE_EXACT": "DUP_IMAGE_EXACT", "DUP_IMAGE_NEAR": "DUP_IMAGE_NEAR",
    "WRONG_CLASS": "POSSIBLE_WRONG_CLASS", "MISSING_BOX": "POSSIBLE_MISSING", "LOOSE_BOX": "POSSIBLE_LOOSE_BOX", "FALSE_POS": "POSSIBLE_FALSE_POS",
}
LINE_CODES = {"BAD_CLASS_ID", "BOX_OUT_OF_IMAGE", "BOX_ZERO", "BAD_FORMAT", "DUP_BOX"}     # so theo (ảnh, dòng)
SWEEP_CODES = {
    "duplicates.phash_dist": ["DUP_IMAGE_EXACT", "DUP_IMAGE_NEAR"],
    "label_format.overflow_tol": ["BOX_OUT_OF_IMAGE"],
    "second_opinion.conf": ["POSSIBLE_WRONG_CLASS", "POSSIBLE_MISSING", "POSSIBLE_LOOSE_BOX", "POSSIBLE_FALSE_POS"],
    "second_opinion.iou_loose": ["POSSIBLE_LOOSE_BOX"],
    "second_opinion.fp_conf": ["POSSIBLE_FALSE_POS"],
}


def load_manifest(path=None):
    exp = defaultdict(set)
    for r in csv.DictReader(open(path or ROOT / "data/calib/MANIFEST.csv", encoding="utf-8")):
        code = TYPE2CODE[r["type"]]
        exp[code].add((r["image"], int(r["line"]) if code in LINE_CODES and r["line"] else None))
    return exp


def evaluate(cfg, manifest=None):
    exp = manifest or load_manifest()
    ds = Dataset(ROOT / "data/calib", cfg["classes"])
    issues = checks.run_checks(checks.INTAKE_CHECKS + checks.QC_CHECKS, ds, cfg)
    got = defaultdict(set)
    for i in issues:
        got[i.code].add((i.image, i.line if i.code in LINE_CODES else None))
    res = {}
    for code in sorted(exp):
        tp, fp, fn = len(exp[code] & got[code]), len(got[code] - exp[code]), len(exp[code] - got[code])
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        res[code] = dict(tp=tp, fp=fp, fn=fn, precision=round(p, 3), recall=round(r, 3),
                         f1=round(2 * p * r / (p + r), 3) if p + r else 0.0, n_injected=len(exp[code]))
    return res


def table(res, codes=None):
    codes = codes or sorted(res)
    out = [f"{'mã lỗi':24} {'chèn':>5} {'TP':>4} {'FP':>4} {'FN':>4} {'precision':>10} {'recall':>7} {'F1':>6}"]
    for c in codes:
        r = res[c]
        out.append(f"{c:24} {r['n_injected']:>5} {r['tp']:>4} {r['fp']:>4} {r['fn']:>4} {r['precision']:>10.2f} {r['recall']:>7.2f} {r['f1']:>6.2f}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="configs/pipeline.yaml")
    ap.add_argument("--sweep", action="append", default=[], help="tham.số=v1,v2,... (lặp lại được)")
    ap.add_argument("--out", help="thư mục ghi calibration_report.md/.json")
    a = ap.parse_args(argv)
    cfg = load_config(ROOT / a.config)
    base = evaluate(cfg)
    print(table(base))
    md = ["# Báo cáo calibration (sinh tự động)", "", "## Với cấu hình hiện tại", "", "```", table(base), "```"]
    payload = dict(config_eval=base, sweeps={})
    for sw in a.sweep:
        param, vals = sw.split("=")
        vals = [float(v) if "." in v else int(v) for v in vals.split(",")]
        codes = SWEEP_CODES.get(param, sorted(base))
        print(f"\n== sweep {param} ==")
        md += ["", f"## Sweep `{param}`", "", "| giá trị | " + " | ".join(f"{c} (P / R / F1)" for c in codes) + " |", "|---|" + "---|" * len(codes)]
        rows = []
        sect, key = param.split(".")
        for v in vals:
            c2 = copy.deepcopy(cfg)
            c2[sect][key] = v
            r = evaluate(c2)
            cells = [f"{r[c]['precision']:.2f} / {r[c]['recall']:.2f} / {r[c]['f1']:.2f}" for c in codes]
            print(f"{param}={v:<6} " + "  ".join(f"{c.replace('POSSIBLE_', ''):12} {x}" for c, x in zip(codes, cells)))
            md.append(f"| {v} | " + " | ".join(cells) + " |")
            rows.append(dict(value=v, **{c: r[c] for c in codes}))
        payload["sweeps"][param] = rows
    if a.out:
        out = ROOT / a.out
        out.mkdir(parents=True, exist_ok=True)
        (out / "calibration_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        (out / "calibration.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nđã ghi {a.out}/calibration_report.md, calibration.json")


if __name__ == "__main__":
    main()
