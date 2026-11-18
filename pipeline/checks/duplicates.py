# ĐÃ VIẾT SẴN (làm mẫu cho các module bạn tự viết): đọc, chạy test, đừng sửa — file này được ghim bằng sha1.
"""Check — ảnh trùng: md5 (trùng từng byte) + perceptual hash (trùng gần đúng) + rò rỉ sang test/val (Script 4 trong slide).

Test: pytest tests/test_duplicates.py -q   (đã xanh sẵn)

Quy tắc (để bạn hiểu kết quả, và để calibrate `duplicates.phash_dist`):
- Duyệt ảnh theo thứ tự tên; ảnh ĐẦU TIÊN được giữ, ảnh sau trùng với nó thì bị báo (`image` = ảnh bị báo).
- Mỗi ảnh nhiều nhất một issue, ưu tiên: LEAK_TEST > DUP_IMAGE_EXACT > DUP_IMAGE_NEAR.
- LEAK_TEST: trùng (md5 hoặc phash <= phash_dist) với ảnh trong `cfg["intake"]["reference_dirs"]` (test/val).
- Ảnh bị báo (LEAK/EXACT/NEAR) KHÔNG được thêm vào danh sách "đã giữ": ảnh sau chỉ so với các ảnh đã giữ.
  Vì vậy A=B=C (3 ảnh giống nhau) -> báo B và C, đều "of: A".
- `phash_dist` là khoảng cách Hamming của hai phash: số này càng lớn càng dễ gộp nhầm ảnh khác nhau. Bạn sẽ calibrate nó ở Bước 3.
"""
import hashlib
from pathlib import Path

import imagehash
from PIL import Image

from ..common import ERROR, ROOT, Issue


def _hash(p: Path):
    md5 = hashlib.md5(p.read_bytes()).hexdigest()
    with Image.open(p) as im:
        ph = imagehash.phash(im.convert("RGB"))
    return md5, ph


def run(ds, cfg):
    dist = cfg["duplicates"]["phash_dist"]
    issues = []
    ref = []                                    # (md5, phash, tên) của kho cũ: test + gold_val
    for d in cfg["intake"].get("reference_dirs", []):
        for p in sorted((ROOT / d).glob("*")):
            if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
                try:
                    ref.append((*_hash(p), f"{Path(d).parent.name}/{p.name}"))
                except Exception:
                    pass
    seen = []                                   # (md5, phash, stem) các ảnh đã giữ
    for p in ds.image_files():
        try:
            md5, ph = _hash(p)
        except Exception:
            continue                            # ảnh hỏng: check images báo
        hit = next((r for r in ref if r[0] == md5 or r[1] - ph <= dist), None)
        if hit:
            issues.append(Issue("duplicates", ERROR, "LEAK_TEST", p.stem, f"trùng ảnh kho test/val: {hit[2]}", extra={"of": hit[2]}))
            continue
        ex = next((s for s in seen if s[0] == md5), None)
        if ex:
            issues.append(Issue("duplicates", ERROR, "DUP_IMAGE_EXACT", p.stem, f"trùng từng byte với {ex[2]}", extra={"of": ex[2]}))
            continue
        nr = next((s for s in seen if s[1] - ph <= dist), None)
        if nr:
            issues.append(Issue("duplicates", ERROR, "DUP_IMAGE_NEAR", p.stem, f"trùng gần đúng với {nr[2]} (phash {nr[1] - ph})", extra={"of": nr[2], "dist": int(nr[1] - ph)}))
            continue
        seen.append((md5, ph, p.stem))
    return issues
