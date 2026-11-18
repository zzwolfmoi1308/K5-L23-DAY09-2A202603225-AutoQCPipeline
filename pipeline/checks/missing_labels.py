# ĐÃ VIẾT SẴN (làm mẫu cho 5 module bạn tự viết): đọc, chạy test, đừng sửa — file này được ghim bằng sha1.
"""Check 1 — ảnh nào thiếu file nhãn (Script 1 trong slide)."""
from ..common import ERROR, WARN, Issue


def run(ds, cfg):
    issues = []
    imgs = {p.stem for p in ds.image_files()}
    labs = {p.stem for p in ds.label_files()}
    for s in sorted(imgs - labs):
        issues.append(Issue("missing_labels", ERROR, "MISSING_LABEL_FILE", s, "ảnh không có file nhãn"))
    for s in sorted(labs - imgs):
        issues.append(Issue("missing_labels", WARN, "ORPHAN_LABEL", s, "file nhãn không có ảnh"))
    for s in sorted(imgs & labs):
        if not ds.read_label_lines(s):
            issues.append(Issue("missing_labels", WARN, "EMPTY_LABEL", s, "file nhãn rỗng: ảnh nền hay thiếu nhãn?"))
    return issues
