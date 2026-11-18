#!/usr/bin/env python3
"""Dựng thư mục dataset kiểu Ultralytics cho từng biến thể (ĐÃ VIẾT SẴN).

    python scripts/materialize_dataset.py --variant raw   --out work/train/raw
    python scripts/materialize_dataset.py --variant clean --out work/train/clean --export submission/export/clean_v1
    python scripts/materialize_dataset.py --variant oracle --out work/train/oracle --export submission/export/clean_v1

- raw    : đúng như nhận về: MỌI ảnh trong data/raw/images + nhãn data/raw/labels (không sửa gì)
- clean  : ảnh theo manifest.json của lần xuất pipeline + nhãn trong export/labels/
- auto   : như `clean` nhưng KHÔNG có người duyệt (`make run-auto` -> submission/export/clean_auto): tách hiệu ứng của 80 ảnh nhãn người
- oracle : cùng ảnh với `clean` nhưng nhãn = nhãn người (data/review_reference) — chặn trên để so sánh (tuỳ chọn)
Cả ba dùng CHUNG: val = data/gold_val (40 ảnh nhãn người), test = data/test (100 ảnh nhãn người).
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["car", "person", "truck", "bus"]


def copy_split(src_dir: Path, dst: Path):
    (dst / "images").mkdir(parents=True, exist_ok=True)
    (dst / "labels").mkdir(parents=True, exist_ok=True)
    for p in sorted((src_dir / "images").iterdir()):
        shutil.copy2(p, dst / "images" / p.name)
    for p in sorted((src_dir / "labels").glob("*.txt")):
        shutil.copy2(p, dst / "labels" / p.name)


def materialize(variant: str, out: Path, export: Path | None) -> Path:
    if out.exists():
        shutil.rmtree(out)
    train = out / "train"
    (train / "images").mkdir(parents=True)
    (train / "labels").mkdir(parents=True)
    raw_imgs = ROOT / "data/raw/images"
    if variant == "raw":
        for p in sorted(raw_imgs.iterdir()):
            shutil.copy2(p, train / "images" / p.name)
        for p in sorted((ROOT / "data/raw/labels").glob("*.txt")):
            shutil.copy2(p, train / "labels" / p.name)
    else:
        if export is None or not (export / "manifest.json").exists():
            raise SystemExit(f"cần --export trỏ tới thư mục xuất của pipeline (có manifest.json), nhận: {export}")
        names = json.loads((export / "manifest.json").read_text(encoding="utf-8"))["images"]
        for n in names:
            shutil.copy2(raw_imgs / n, train / "images" / n)
            stem = Path(n).stem
            src = (export / "labels" / f"{stem}.txt") if variant in ("clean", "auto") else (ROOT / "data/review_reference/labels" / f"{stem}.txt")
            shutil.copy2(src, train / "labels" / f"{stem}.txt")
    copy_split(ROOT / "data/gold_val", out / "val")
    copy_split(ROOT / "data/test", out / "test")
    (out / "data.yaml").write_text(
        f"path: {out.resolve()}\ntrain: train/images\nval: val/images\ntest: test/images\nnames:\n" + "".join(f"  {i}: {n}\n" for i, n in enumerate(NAMES)))
    n_img = len(list((train / "images").iterdir()))
    print(f"{variant}: {n_img} ảnh train, {len(list((train / 'labels').glob('*.txt')))} file nhãn -> {out}")
    return out / "data.yaml"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["raw", "clean", "auto", "oracle"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--export", default="submission/export/clean_v1")
    a = ap.parse_args()
    materialize(a.variant, ROOT / a.out, ROOT / a.export)
