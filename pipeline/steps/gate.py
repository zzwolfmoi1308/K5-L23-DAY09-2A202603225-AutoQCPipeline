"""BƯỚC 4 — Cửa chặn: quyết định Release / Hold / Rework.   ★

Test:  pytest tests/test_gate.py -q

Cây quyết định Day 07 (slide Day 09: "Lỗi bắt buộc chặn pipeline; lỗi cảnh báo chuyển người xem"):

  còn ≥ 1 lỗi bắt buộc (severity ERROR)                          -> "Rework"
  không còn lỗi bắt buộc, nhưng tỉ lệ ẢNH còn cảnh báo
      >= cfg["gate"]["warn_ratio_hold"]                          -> "Hold"
  còn lại                                                        -> "Release"

Tỉ lệ cảnh báo = (số ẢNH khác nhau có ≥ 1 cảnh báo) / (tổng số ảnh).  Chú ý:
- chỉ đếm issue có `image` nằm trong `image_stems` (bỏ "<dataset>", "data.yaml");
- bỏ qua ảnh nằm trong `reviewed` (người đã xem, cảnh báo của ảnh đó coi như đã xử lý) — nhưng LỖI BẮT BUỘC thì không bao giờ được bỏ qua;
- mẫu số là số ảnh, không phải số issue.

Trả về dict: decision, n_errors, n_warn_images, n_images, warn_ratio (làm tròn 4 chữ số), reasons (list[str], giải thích bằng tiếng Việt, có số liệu).
"""
from __future__ import annotations

from typing import Any

from ..common import ERROR, WARN


def decide(issues, image_stems, cfg, reviewed=frozenset()) -> dict[str, Any]:
    gate_cfg = cfg.get("gate", {})
    warn_ratio_hold = gate_cfg.get("warn_ratio_hold", 0.10)

    # 1. Đếm lỗi bắt buộc (ERROR): lỗi bắt buộc không bao giờ bị bỏ qua kể cả ở ảnh đã duyệt
    errors = [i for i in issues if i.severity == ERROR]
    n_errors = len(errors)

    # 2. Đếm số ảnh còn cảnh báo (WARN):
    # - Chỉ tính issue có image nằm trong image_stems (bỏ <dataset>, data.yaml, và ảnh không còn trong dataset)
    # - Bỏ qua ảnh nằm trong reviewed
    stems_set = set(image_stems)
    reviewed_set = set(reviewed)
    warn_images = {
        i.image
        for i in issues
        if i.severity == WARN and i.image in stems_set and i.image not in reviewed_set
    }
    n_warn_images = len(warn_images)
    n_images = len(image_stems)

    # 3. Tính tỉ lệ cảnh báo
    if n_images == 0:
        warn_ratio = 0.0
    else:
        warn_ratio = round(n_warn_images / n_images, 4)

    # 4. Ra quyết định theo cây quyết định
    reasons: list[str] = []
    if n_errors > 0:
        decision = "Rework"
        reasons.append(f"Còn {n_errors} lỗi bắt buộc (ERROR) chưa được khắc phục.")
    elif warn_ratio >= warn_ratio_hold:
        decision = "Hold"
        reasons.append(
            f"Tỉ lệ ảnh có cảnh báo {warn_ratio:.2%} ({n_warn_images}/{n_images} ảnh) >= ngưỡng cho phép {warn_ratio_hold:.2%}."
        )
    else:
        decision = "Release"
        reasons.append(
            f"Đạt yêu cầu: 0 lỗi bắt buộc, tỉ lệ ảnh cảnh báo {warn_ratio:.2%} ({n_warn_images}/{n_images} ảnh) < ngưỡng {warn_ratio_hold:.2%}."
        )

    return {
        "decision": decision,
        "n_errors": n_errors,
        "n_warn_images": n_warn_images,
        "n_images": n_images,
        "warn_ratio": warn_ratio,
        "reasons": reasons,
    }
