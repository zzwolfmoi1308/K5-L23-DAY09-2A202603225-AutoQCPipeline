"""Lấy dự đoán của model cho ảnh (ĐÃ VIẾT SẴN).

Ưu tiên đọc cache JSON trong `data/cache/` (chạy được trên máy không có GPU / chưa cài ultralytics).
Ảnh chưa có trong cache thì gọi model thật (cần `pip install ultralytics`).

Định dạng: {tên_ảnh_không_đuôi: [[id_lớp_dự_án, conf, cx, cy, w, h], ...]}
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import ROOT

YOLO2PRJ = {0: 1, 2: 0, 5: 3, 7: 2}        # chỉ số lớp COCO của model -> id lớp dự án (person→1, car→0, bus→3, truck→2)


def load_cache(path) -> dict:
    p = ROOT / path
    if not p.exists():
        return {}
    return {Path(k).stem: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()}


def run_model(weights: str, image_paths: list[Path], conf: float = 0.25, imgsz: int = 640) -> dict:
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError("Ảnh chưa có trong cache và chưa cài ultralytics: pip install ultralytics") from e
    model = YOLO(weights)
    out = {}
    for i in range(0, len(image_paths), 16):
        for r in model.predict([str(p) for p in image_paths[i:i + 16]], conf=conf, classes=list(YOLO2PRJ), imgsz=imgsz, verbose=False):
            rows = [[YOLO2PRJ[int(c)], round(s, 4)] + [round(v, 6) for v in xywhn]
                    for c, s, xywhn in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist(), r.boxes.xywhn.tolist())]
            out[Path(r.path).stem] = rows
    return out


def get_preds(ds, cfg, which: str) -> dict:
    """which = 'checker' (yolo26l — model lớn hơn dùng làm ý kiến thứ hai; dự đoán đã lưu sẵn trong cache). Trả {stem: rows}."""
    mc = cfg["models"][which]
    cache = load_cache(mc["cache"])
    need = [p for p in ds.image_files() if p.stem not in cache and ds.image_size(p.stem)]
    if need:
        cache.update(run_model(mc["weights"], need, conf=mc.get("conf", 0.25)))
    return cache
