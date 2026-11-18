# ĐÃ VIẾT SẴN (làm mẫu cho 5 module bạn tự viết): đọc, chạy test, đừng sửa — file này được ghim bằng sha1.
"""Check 3 — tên lớp trong data.yaml phải đúng danh sách của dự án (Script 3 trong slide)."""
from ..common import ERROR, Issue


def run(ds, cfg):
    valid = cfg["classes"]
    names = ds.yaml_names()
    issues = []
    if not names:
        return [Issue("class_names", ERROR, "BAD_CLASS_NAME", "data.yaml", "không đọc được names trong data.yaml")]
    for i, n in sorted(names.items()):
        if n not in valid:
            issues.append(Issue("class_names", ERROR, "BAD_CLASS_NAME", "data.yaml", f"tên lớp lạ: {n!r} (id {i})", extra={"id": i, "name": n}))
        elif i >= len(valid) or valid[i] != n:
            issues.append(Issue("class_names", ERROR, "BAD_CLASS_NAME", "data.yaml", f"{n!r} đứng sai chỗ: id {i}, mong đợi id {valid.index(n)}", extra={"id": i, "name": n}))
    if len(names) != len(valid):
        issues.append(Issue("class_names", ERROR, "BAD_CLASS_NAME", "data.yaml", f"số lớp {len(names)} khác {len(valid)}"))
    return issues
