"""CHECK 6 — Ý kiến thứ hai: so nhãn với một model LỚN HƠN (yolo26l).   ★★★ (khó nhất, đáng điểm nhất)

Test:  pytest tests/test_second_opinion.py -q

Máy kiểm quy tắc, người kiểm ý nghĩa (slide). Các lỗi như thiếu nhãn / gán nhầm lớp hợp lệ / box lỏng
KHÔNG bắt được bằng quy tắc cú pháp. Ta nhờ một model mạnh hơn "nhìn lại" và CHỈ CẢNH BÁO (model cũng có thể sai):
những ảnh bị cờ sẽ vào hàng đợi cho NGƯỜI duyệt.

`preds[stem]` = list `[id_lớp, conf, cx, cy, w, h]` của model (lấy qua `get_preds(ds, cfg, "checker")` nếu preds=None).
`L = ds.valid_boxes(stem)` = list `(id_lớp, cx, cy, w, h)` của nhãn (đã bỏ dòng hỏng).
Ngưỡng ở `cfg["second_opinion"]`: conf, min_area_px, fp_conf, iou_missing, iou_match, iou_loose.

Thuật toán gợi ý, với từng ảnh (bỏ qua ảnh không có trong preds hoặc không có file nhãn):
  P = dự đoán có conf >= conf  VÀ diện tích px (w*W * h*H) >= min_area_px
  Với mỗi dự đoán r trong P: lấy các nhãn có IoU(r, nhãn) >= iou_missing  (cands)
   - không có cands                            -> POSSIBLE_MISSING     (model thấy vật mà nhãn không có box)
   - có cands cùng lớp, tốt nhất IoU < iou_loose -> POSSIBLE_LOOSE_BOX  (đúng vật, box lỏng/lệch)
   - không có cands cùng lớp, nhưng cands tốt nhất IoU >= iou_match (khác lớp) -> POSSIBLE_WRONG_CLASS
  Với mỗi dòng nhãn hợp lệ: nếu IoU với MỌI dự đoán (conf >= fp_conf, không lọc diện tích) đều < iou_missing
                                             -> POSSIBLE_FALSE_POS  (box nhãn không khớp vật nào model thấy; Issue.line = số dòng)

Chi tiết các ca biên (test kiểm đúng các ca này)
- `cands` gồm nhãn MỌI lớp có IoU >= iou_missing; "tốt nhất cùng lớp" = cands cùng lớp có IoU lớn nhất; "tốt nhất khác lớp" tương tự với cands khác lớp.
- Thứ tự quyết định cho mỗi dự đoán: (1) cands rỗng -> MISSING. (2) có cands cùng lớp: IoU tốt nhất < iou_loose -> LOOSE_BOX, ngược lại KHÔNG cờ
  (nhãn đúng lớp đã phủ vật này, kể cả khi còn nhãn khác lớp chồng lên). (3) không có cands cùng lớp: nếu IoU tốt nhất khác lớp >= iou_match -> WRONG_CLASS;
  nếu chỉ có khác lớp với IoU trong [iou_missing, iou_match) -> không cờ gì (mơ hồ: để cho FALSE_POS / lần duyệt khác).
- Một dự đoán sinh tối đa MỘT issue (MISSING / LOOSE_BOX / WRONG_CLASS); một ảnh có thể có nhiều issue.
- Thứ tự issue: theo `ds.image_files()` rồi theo thứ tự dự đoán trong `preds[stem]`, cuối cùng là các FALSE_POS theo số dòng; `Issue.image` = stem, `Issue.line` chỉ đặt cho FALSE_POS.

Lưu ý số dòng: dùng `ds.read_label_lines(stem)` (giữ số dòng gốc, kể cả dòng hỏng/trống) để lấy `Issue.line`; `valid_boxes` KHÔNG giữ số dòng.

Tất cả severity WARN; `Issue.extra` nên có {"conf": ...} hoặc {"iou": ...} (hàng đợi duyệt dùng conf để xếp ưu tiên).

Gợi ý
- `iou_xywh` có sẵn. Dòng nhãn hỏng không được làm script chết (dùng `ds.valid_boxes` và `parse_yolo_line` trong try).
- Kết quả phụ thuộc mạnh vào ngưỡng: calibrate chúng ở Bước 3 thay vì đoán.
"""
from __future__ import annotations

from typing import Any

from ..common import WARN, Issue, iou_xywh, parse_yolo_line
from ..model_cache import get_preds


def run(ds, cfg, preds=None) -> list[Issue]:
    if preds is None:
        preds = get_preds(ds, cfg, "checker")

    so_cfg = cfg.get("second_opinion", {})
    conf_thresh = so_cfg.get("conf", 0.25)
    min_area_px = so_cfg.get("min_area_px", 600)
    fp_conf = so_cfg.get("fp_conf", 0.1)
    iou_missing = so_cfg.get("iou_missing", 0.3)
    iou_match = so_cfg.get("iou_match", 0.5)
    iou_loose = so_cfg.get("iou_loose", 0.5)

    issues: list[Issue] = []

    for img_p in ds.image_files():
        stem = img_p.stem

        # Bỏ qua ảnh không có trong preds hoặc không có file nhãn
        img_preds = preds.get(stem)
        if img_preds is None:
            img_preds = preds.get(f"{stem}.jpg")
        if img_preds is None:
            continue

        if not ds.label_path(stem).exists():
            continue

        im_size = ds.image_size(stem)
        if not im_size:
            continue
        W, H = im_size

        # Đọc các dòng nhãn hợp lệ kèm số dòng gốc
        valid_labels: list[tuple[int, int, tuple[float, float, float, float]]] = []
        for lineno, text in ds.read_label_lines(stem) or []:
            try:
                cls_id, cx, cy, w, h = parse_yolo_line(text)
            except ValueError:
                continue
            if 0 <= cls_id < len(ds.classes):
                valid_labels.append((lineno, cls_id, (cx, cy, w, h)))

        # 1. P = dự đoán có conf >= conf_thresh VÀ diện tích px >= min_area_px
        pred_issues: list[Issue] = []
        for p in img_preds:
            p_cls, p_conf, p_cx, p_cy, p_w, p_h = p[0], p[1], p[2], p[3], p[4], p[5]
            p_area_px = (p_w * W) * (p_h * H)

            if p_conf < conf_thresh or p_area_px < min_area_px:
                continue

            p_box = (p_cx, p_cy, p_w, p_h)
            # Lấy cands có IoU >= iou_missing
            cands = []
            for l_lineno, l_cls, l_box in valid_labels:
                iou = iou_xywh(p_box, l_box)
                if iou >= iou_missing:
                    cands.append((l_lineno, l_cls, iou))

            if not cands:
                # (1) cands rỗng -> POSSIBLE_MISSING
                cls_name = ds.classes[p_cls] if 0 <= p_cls < len(ds.classes) else str(p_cls)
                pred_issues.append(
                    Issue(
                        "second_opinion",
                        WARN,
                        "POSSIBLE_MISSING",
                        stem,
                        f"model thấy {cls_name} (conf {p_conf:.2f}) nhưng nhãn không có",
                        line=None,
                        extra={"conf": p_conf},
                    )
                )
            else:
                same_class_cands = [c for c in cands if c[1] == p_cls]
                if same_class_cands:
                    # (2) có cands cùng lớp:
                    best_same_iou = max(c[2] for c in same_class_cands)
                    if best_same_iou < iou_loose:
                        pred_issues.append(
                            Issue(
                                "second_opinion",
                                WARN,
                                "POSSIBLE_LOOSE_BOX",
                                stem,
                                f"box nhãn lỏng/lệch so với dự đoán (IoU {best_same_iou:.2f} < {iou_loose})",
                                line=None,
                                extra={"iou": round(best_same_iou, 4), "conf": p_conf},
                            )
                        )
                    # ngược lại: nhãn đúng lớp đã phủ vật này -> KHÔNG cờ
                else:
                    # (3) không có cands cùng lớp:
                    diff_class_cands = [c for c in cands if c[1] != p_cls]
                    if diff_class_cands:
                        best_diff_iou = max(c[2] for c in diff_class_cands)
                        if best_diff_iou >= iou_match:
                            cls_name = ds.classes[p_cls] if 0 <= p_cls < len(ds.classes) else str(p_cls)
                            pred_issues.append(
                                Issue(
                                    "second_opinion",
                                    WARN,
                                    "POSSIBLE_WRONG_CLASS",
                                    stem,
                                    f"nghi gán nhầm lớp: model thấy {cls_name} (conf {p_conf:.2f}), nhãn có lớp khác (IoU {best_diff_iou:.2f})",
                                    line=None,
                                    extra={"conf": p_conf, "iou": round(best_diff_iou, 4)},
                                )
                            )
                        # nếu IoU trong [iou_missing, iou_match) -> không cờ gì (mơ hồ)

        # 2. FALSE_POS: với mỗi dòng nhãn hợp lệ, nếu IoU với MỌI dự đoán (conf >= fp_conf, không lọc diện tích) < iou_missing
        fp_preds = [p for p in img_preds if p[1] >= fp_conf]
        fp_issues: list[Issue] = []
        for l_lineno, l_cls, l_box in valid_labels:
            has_match = any(iou_xywh(l_box, (p[2], p[3], p[4], p[5])) >= iou_missing for p in fp_preds)
            if not has_match:
                fp_issues.append(
                    Issue(
                        "second_opinion",
                        WARN,
                        "POSSIBLE_FALSE_POS",
                        stem,
                        f"dòng {l_lineno}: box nhãn không khớp dự đoán nào của model",
                        line=l_lineno,
                        extra={"line": l_lineno},
                    )
                )

        issues.extend(pred_issues)
        issues.extend(fp_issues)

    return issues
