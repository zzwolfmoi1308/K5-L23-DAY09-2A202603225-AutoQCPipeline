# ĐÃ VIẾT SẴN (làm mẫu cho 5 module bạn tự viết): đọc, chạy test, đừng sửa — file này được ghim bằng sha1.
"""Check 4a — ảnh mở được không, đủ độ phân giải không (cửa vào, bước 1)."""
from PIL import Image

from ..common import ERROR, Issue


def run(ds, cfg):
    min_side = cfg["intake"]["min_side_px"]
    issues = []
    for p in ds.image_files():
        try:
            with Image.open(p) as im:
                im.load()                      # open() chưa đủ: ảnh cắt cụt chỉ lộ lỗi khi load()
                w, h = im.size
        except Exception as e:
            issues.append(Issue("images", ERROR, "CORRUPT_IMAGE", p.stem, f"không mở được: {type(e).__name__}"))
            continue
        if min(w, h) < min_side:
            issues.append(Issue("images", ERROR, "BAD_SIZE", p.stem, f"cạnh ngắn {min(w, h)}px < {min_side}px", extra={"size": [w, h]}))
    return issues
