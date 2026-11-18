"""Ghi báo cáo lỗi dạng chữ như slide: một dòng một chỗ cần mở (ĐÃ VIẾT SẴN)."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..common import ERROR, Issue, write_issues_csv


def write_report(issues: list[Issue], stem_path: str | Path, title: str, n_images: int, verdict: dict | None = None):
    """Ghi <stem_path>.csv và <stem_path>.txt. Trả về Counter theo (check, code)."""
    stem_path = Path(stem_path)
    write_issues_csv(issues, stem_path.with_suffix(".csv"))
    by_check = Counter(i.check for i in issues)
    by_code = Counter((i.severity, i.code) for i in issues)
    lines = [f"# {title}", f"ảnh đã quét: {n_images}", ""]
    for chk in sorted(by_check):
        lines.append(f"{chk} -> {by_check[chk]} dòng")
    lines.append("")
    for i in sorted(issues, key=lambda i: (i.severity != ERROR, i.code, i.image, i.line or 0)):
        loc = f"{i.image}.txt:{i.line}" if i.line else i.image
        lines.append(f"[{i.severity.upper():5}] {i.code:20} {loc}  {i.message}")
    lines += ["", "## Tổng hợp theo mã"] + [f"{s:5} {c:22} {n}" for (s, c), n in sorted(by_code.items())]
    if verdict:
        lines += ["", f"Kết luận: {verdict['decision'].upper()} — " + "; ".join(verdict["reasons"])]
    stem_path.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return by_code
