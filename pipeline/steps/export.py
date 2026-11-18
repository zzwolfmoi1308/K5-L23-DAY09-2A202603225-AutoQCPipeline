"""Bước 5 — Xuất bộ dữ liệu đã đạt cửa chặn, kèm manifest để truy vết (ĐÃ VIẾT SẴN)."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import yaml

from ..common import Dataset


def export(ds: Dataset, out_dir, name: str, decision: dict, cfg: dict) -> Path:
    """Chép nhãn (không chép ảnh: ảnh nằm trong data/raw/images) + data.yaml + manifest.json vào out_dir/name."""
    out = Path(out_dir) / name
    if out.exists():
        shutil.rmtree(out)
    (out / "labels").mkdir(parents=True)
    stems = []
    sha = {}
    for p in ds.image_files():
        lp = ds.label_path(p.stem)
        if not lp.exists():
            continue
        shutil.copy2(lp, out / "labels" / lp.name)
        stems.append(p.name)
        sha[lp.name] = hashlib.sha1(lp.read_bytes()).hexdigest()[:12]
    (out / "data.yaml").write_text(yaml.safe_dump({"path": ".", "names": dict(enumerate(cfg["classes"]))}, allow_unicode=True), encoding="utf-8")
    manifest = dict(
        name=name,
        n_images=len(stems),
        classes=cfg["classes"],
        decision=decision,
        config=cfg,
        images=stems,
        label_sha1=sha,
        note="Ảnh lấy từ data/raw/images theo danh sách `images`; dùng scripts/materialize_dataset.py để dựng thư mục train.",
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return out
