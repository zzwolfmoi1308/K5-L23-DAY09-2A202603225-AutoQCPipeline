"""Bước 3 (đầu vào của người) — xếp hàng ảnh cần người xem (ĐÃ VIẾT SẴN)."""
from __future__ import annotations

from collections import defaultdict

from ..common import WARN


def build_queue(issues, fixes, image_stems, cfg):
    w = cfg["review"]["weights"]
    score, codes = defaultdict(float), defaultdict(set)
    for i in issues:
        if i.severity == WARN and i.image in image_stems:
            score[i.image] += w.get(i.code, w.get("default", 1.0)) * (1 + i.extra.get("conf", 0) if i.extra else 1)
            codes[i.image].add(i.code)
    for f in fixes:
        if f["action"] in ("drop_line", "clip_box") and f["image"] in image_stems:
            score[f["image"]] += w.get("FIXED_" + f["action"].upper(), 1.0)
            codes[f["image"]].add("FIXED_" + f["action"].upper())
        if f["action"] == "needs_label" and f["image"] in image_stems:     # chưa có nhãn: chỉ người mới gán được
            score[f["image"]] += w.get("NEEDS_LABEL", 10.0)
            codes[f["image"]].add("NEEDS_LABEL")
    rows = [dict(image=k, priority=round(v, 3), codes=";".join(sorted(codes[k]))) for k, v in score.items()]
    return sorted(rows, key=lambda r: (-r["priority"], r["image"]))
