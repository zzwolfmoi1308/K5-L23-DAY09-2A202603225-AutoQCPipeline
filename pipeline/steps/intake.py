"""Bước 1 — Nhận dữ liệu: loại ảnh hỏng, sai kích thước, trùng, rò rỉ sang test (ĐÃ VIẾT SẴN).

Gọi `checks.images` và `checks.duplicates` (bạn viết). Ảnh có lỗi bắt buộc KHÔNG được chép vào `ds`.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from ..checks import INTAKE_CHECKS, run_checks
from ..common import ERROR, Dataset


def run(raw_dir, ds_dir, cfg):
    raw = Dataset(raw_dir, cfg["classes"])
    issues = run_checks(INTAKE_CHECKS, raw, cfg)
    rejected = {i.image for i in issues if i.severity == ERROR}
    ds_dir = Path(ds_dir)
    if ds_dir.exists():
        shutil.rmtree(ds_dir)
    (ds_dir / "images").mkdir(parents=True)
    (ds_dir / "labels").mkdir()
    for p in raw.image_files():
        if p.stem in rejected:
            continue
        shutil.copy2(p, ds_dir / "images" / p.name)
        lp = raw.label_path(p.stem)
        if lp.exists():
            shutil.copy2(lp, ds_dir / "labels" / lp.name)
    if raw.yaml_path.exists():
        shutil.copy2(raw.yaml_path, ds_dir / "data.yaml")
    accepted = [p.stem for p in raw.image_files() if p.stem not in rejected]
    return accepted, issues
