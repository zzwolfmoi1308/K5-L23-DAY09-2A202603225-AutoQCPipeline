"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from __future__ import annotations

from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line


def run(ds, cfg):
    fmt_cfg = cfg.get("label_format", {})
    overflow_tol = fmt_cfg.get("overflow_tol", 0.002)
    min_box_px = fmt_cfg.get("min_box_px", 12)
    max_box_frac = fmt_cfg.get("max_box_frac", 0.95)
    dup_box_iou = fmt_cfg.get("dup_box_iou", 0.9)

    issues: list[Issue] = []

    for lab_file in ds.label_files():
        stem = lab_file.stem
        lines = ds.read_label_lines(stem)
        if not lines:
            continue

        im_size = ds.image_size(stem)
        valid_boxes: list[tuple[int, int, tuple[float, float, float, float]]] = []

        for lineno, text in lines:
            # 1. BAD_FORMAT: không đúng 5 cột số
            try:
                cls_id, cx, cy, w, h = parse_yolo_line(text)
            except ValueError as e:
                issues.append(
                    Issue(
                        "label_format",
                        ERROR,
                        "BAD_FORMAT",
                        stem,
                        f"dòng sai định dạng: {text!r} ({e})",
                        line=lineno,
                    )
                )
                continue

            # 2. BAD_CLASS_ID: id lớp ngoài 0..len(ds.classes)-1
            if cls_id < 0 or cls_id >= len(ds.classes):
                issues.append(
                    Issue(
                        "label_format",
                        ERROR,
                        "BAD_CLASS_ID",
                        stem,
                        f"id lớp {cls_id} ngoài 0..{len(ds.classes)-1}",
                        line=lineno,
                        extra={"id": cls_id},
                    )
                )
                continue

            # 3. BOX_ZERO: w <= 0 hoặc h <= 0
            if w <= 0 or h <= 0:
                issues.append(
                    Issue(
                        "label_format",
                        ERROR,
                        "BOX_ZERO",
                        stem,
                        f"kích thước box <= 0 (w={w}, h={h})",
                        line=lineno,
                    )
                )
                continue

            # 4. BOX_OUT_OF_IMAGE: mép box vượt [0, 1] quá overflow_tol
            x1 = cx - w / 2
            x2 = cx + w / 2
            y1 = cy - h / 2
            y2 = cy + h / 2
            overflow = max(0.0, -x1, x2 - 1.0, -y1, y2 - 1.0)
            if overflow > overflow_tol:
                issues.append(
                    Issue(
                        "label_format",
                        ERROR,
                        "BOX_OUT_OF_IMAGE",
                        stem,
                        f"box tràn ảnh: {overflow:.4f}",
                        line=lineno,
                        extra={"overflow": overflow},
                    )
                )

            # 5. DUP_BOX: cùng lớp với dòng trước đó và IoU > dup_box_iou
            for prev_lineno, prev_cls, prev_box in valid_boxes:
                if prev_cls == cls_id and iou_xywh((cx, cy, w, h), prev_box) > dup_box_iou:
                    issues.append(
                        Issue(
                            "label_format",
                            ERROR,
                            "DUP_BOX",
                            stem,
                            f"box trùng với dòng {prev_lineno}",
                            line=lineno,
                            extra={"dup_of": prev_lineno},
                        )
                    )
                    break

            # 6. BOX_TINY: cạnh ngắn của box (px) < min_box_px
            if im_size is not None:
                W, H = im_size
                short_px = min(w * W, h * H)
                if short_px < min_box_px:
                    issues.append(
                        Issue(
                            "label_format",
                            WARN,
                            "BOX_TINY",
                            stem,
                            f"cạnh ngắn {short_px:.1f}px < {min_box_px}px",
                            line=lineno,
                            extra={"short_px": short_px},
                        )
                    )

            # 7. BOX_HUGE: diện tích box > max_box_frac
            area_frac = w * h
            if area_frac > max_box_frac:
                issues.append(
                    Issue(
                        "label_format",
                        WARN,
                        "BOX_HUGE",
                        stem,
                        f"diện tích box {area_frac:.3f} > {max_box_frac}",
                        line=lineno,
                        extra={"frac": area_frac},
                    )
                )

            valid_boxes.append((lineno, cls_id, (cx, cy, w, h)))

    return issues
