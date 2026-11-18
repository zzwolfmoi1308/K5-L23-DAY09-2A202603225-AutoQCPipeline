#!/usr/bin/env python3
"""Mô phỏng bước 3 — NGƯỜI duyệt (ĐÃ VIẾT SẴN).

Trong lab thật bạn sẽ mở CVAT, sửa nhãn các ảnh trong hàng đợi. Ở đây ta mô phỏng người duyệt:
với mỗi ảnh nằm trong `budget` ảnh đầu hàng đợi, thay nhãn bằng nhãn tham chiếu do NGƯỜI gán
(`data/review_reference/labels/`, lấy từ COCO). Ảnh ngoài ngân sách giữ nguyên nhãn máy.

=> Pipeline của bạn phải xếp đúng ảnh quan trọng lên đầu hàng đợi: ngân sách có hạn như thời gian thật.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def simulate(queue_csv: Path, ds_dir: Path, budget: int, log_csv: Path) -> list[str]:
    rows = list(csv.DictReader(open(queue_csv, encoding="utf-8")))
    ref = ROOT / "data" / "review_reference" / "labels"
    reviewed, log = [], []
    for r in rows[:budget]:
        src = ref / f"{r['image']}.txt"
        if not src.exists():
            log.append(dict(image=r["image"], result="không có nhãn tham chiếu (bỏ qua)", codes=r["codes"]))
            continue
        shutil.copy2(src, ds_dir / "labels" / f"{r['image']}.txt")
        reviewed.append(r["image"])
        log.append(dict(image=r["image"], result="đã duyệt: thay bằng nhãn người", codes=r["codes"]))
    log_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(log_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["image", "result", "codes"])
        w.writeheader()
        w.writerows(log)
    return reviewed


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default="work/run", help="thư mục chạy pipeline (có ds/ và review queue)")
    ap.add_argument("--reports", default="submission/reports")
    ap.add_argument("--budget", type=int, default=80)
    a = ap.parse_args()
    q = Path(a.reports) / "05_review_queue.csv"
    if not q.exists():
        sys.exit(f"không thấy {q}: hãy chạy `python -m pipeline.run` trước")
    done = simulate(q, Path(a.work) / "ds", a.budget, Path(a.reports) / "06_review_log.csv")
    (Path(a.work) / "reviewed.txt").write_text("\n".join(done) + "\n", encoding="utf-8")
    print(f"đã duyệt {len(done)} ảnh -> {a.work}/reviewed.txt")
