# ĐÃ VIẾT SẴN (làm mẫu cho 5 module bạn tự viết): đọc, chạy test, đừng sửa — file này được ghim bằng sha1.
"""Check 5 — đếm box theo lớp để thấy bất thường (Script 5 trong slide)."""
from collections import Counter

from ..common import WARN, Issue


def _raw_ids(ds):
    for lf in ds.label_files():
        for _, ln in ds.read_label_lines(lf.stem) or []:
            tok = ln.split()
            if tok:
                yield lf.stem, tok[0]


def class_counts(ds) -> Counter:
    """Đếm số box theo token đầu dòng (cả ID lạ như '93')."""
    return Counter(t for _, t in _raw_ids(ds))


def run(ds, cfg):
    c = cfg["stats"]
    issues = []
    for tok, n in sorted(class_counts(ds).items()):
        if n < c["rare_class_min_boxes"]:
            issues.append(Issue("stats", WARN, "CLASS_RARE", "<dataset>", f"lớp {tok} chỉ có {n} box", extra={"class": tok, "n": n}))
    per_img = Counter(s for s, _ in _raw_ids(ds))
    for s, n in sorted(per_img.items()):
        if n > c["dense_image_max_boxes"]:
            issues.append(Issue("stats", WARN, "DENSE_IMAGE", s, f"{n} box trong một ảnh", extra={"n": n}))
    return issues
