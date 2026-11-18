"""BƯỚC 2/4 — Sửa tự động những lỗi bắt buộc mà máy sửa được AN TOÀN.   ★★

Test:  pytest tests/test_autofix.py -q

`fix(ds, issues, cfg) -> list[dict]`: duyệt `issues` (chỉ lỗi severity ERROR), sửa thẳng vào thư mục `ds`,
và trả về danh sách thay đổi; mỗi phần tử có khoá: image, line, action, before, after
(đây chính là file `03_fixes.csv` — bằng chứng pipeline đã làm gì, người có thể kiểm lại).

| code lỗi                                       | cách sửa                                    | action           |
|------------------------------------------------|---------------------------------------------|------------------|
| BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO, DUP_BOX    | xoá dòng đó khỏi file nhãn                  | "drop_line"      |
| BOX_OUT_OF_IMAGE                               | cắt box về trong [0,1] (giữ nguyên lớp)     | "clip_box"       |
| MISSING_LABEL_FILE                             | KHÔNG sửa file (máy không thể bịa nhãn): ghi 1 dòng fix, before="(không có file)", after="chuyển người gán" | "needs_label" |
| BAD_CLASS_NAME                                 | ghi lại `names` trong data.yaml đúng `cfg["classes"]` | "rename_classes" |
| DUP_IMAGE_*, LEAK_TEST, CORRUPT_IMAGE, BAD_SIZE| xoá ảnh + nhãn khỏi `ds`                    | "remove_image"   |

Bẫy cần nghĩ tới (có test cho từng cái)
- Một file có NHIỀU dòng lỗi: số dòng trong `issues` là số dòng GỐC. Nếu xoá từng dòng một thì số dòng lệch.
  Gom theo file, rồi ghi lại MỘT lần.
- Sau khi cắt, box có thể không còn diện tích (nằm hẳn ngoài ảnh): lúc đó xoá dòng thay vì ghi box rỗng.
- Một dòng có 2 lỗi (vd. BOX_OUT_OF_IMAGE + DUP_BOX): xoá dòng thắng, chỉ ghi 1 fix `drop_line`, không ghi thêm `clip_box`. Dòng trống ở giữa file vẫn đếm vào số dòng gốc.
- Ảnh vừa bị xoá (DUP_IMAGE_*...) mà còn issue dòng của chính nó: bỏ qua êm, không được báo lỗi/chết.
- Không động tới lỗi WARN (cảnh báo là việc của người). Không sửa file ở `data/raw/` — chỉ sửa `ds`.
- Chạy lần 2 trên dữ liệu đã sửa phải không làm gì thêm (idempotent) — NGOẠI LỆ duy nhất: `needs_label` được ghi lại mỗi lần còn lỗi `MISSING_LABEL_FILE` (vì ảnh vẫn chưa có nhãn).

- `needs_label` KHÔNG tạo file nhãn rỗng (rỗng = "ảnh nền", khác với "chưa gán"). `review_queue` sẽ đẩy ảnh này lên đầu hàng đợi cho người.

Gợi ý: `yaml.safe_load / safe_dump`.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import yaml

from ..common import ERROR, parse_yolo_line

DROP_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}


def fix(ds, issues, cfg) -> list[dict[str, Any]]:
    # Chỉ xử lý các lỗi bắt buộc (severity ERROR)
    error_issues = [i for i in issues if i.severity == ERROR]
    if not error_issues:
        return []

    fixes: list[dict[str, Any]] = []
    removed_images: set[str] = set()

    # 1. Xử lý các lỗi cần xoá ảnh (remove_image)
    for iss in error_issues:
        code = iss.code
        if code.startswith("DUP_IMAGE") or code in ("LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"):
            stem = iss.image
            if stem not in removed_images:
                # Xoá file ảnh trong images_dir
                if ds.images_dir.exists():
                    for p in ds.images_dir.iterdir():
                        if p.stem == stem:
                            try:
                                p.unlink()
                            except OSError:
                                pass
                # Xoá file nhãn trong labels_dir
                lbl = ds.label_path(stem)
                if lbl.exists():
                    try:
                        lbl.unlink()
                    except OSError:
                        pass
                ds._size_cache.pop(stem, None)
                removed_images.add(stem)
                fixes.append({
                    "image": stem,
                    "line": None,
                    "action": "remove_image",
                    "before": iss.message or code,
                    "after": "(đã xoá)",
                })

    # 2. Xử lý sửa tên lớp trong data.yaml (rename_classes)
    bad_class_name_issues = [i for i in error_issues if i.code == "BAD_CLASS_NAME"]
    if bad_class_name_issues and ds.yaml_path.exists():
        try:
            cur_yaml = yaml.safe_load(ds.yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            cur_yaml = {}
        before_names = cur_yaml.get("names", {})
        classes = list(cfg.get("classes", []))
        cur_yaml["names"] = {i: name for i, name in enumerate(classes)}
        ds.yaml_path.write_text(yaml.safe_dump(cur_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")
        fixes.append({
            "image": "data.yaml",
            "line": None,
            "action": "rename_classes",
            "before": str(before_names),
            "after": str(classes),
        })

    # 3. Xử lý ảnh thiếu file nhãn (needs_label)
    missing_label_issues = [
        i for i in error_issues if i.code == "MISSING_LABEL_FILE" and i.image not in removed_images
    ]
    for iss in missing_label_issues:
        fixes.append({
            "image": iss.image,
            "line": None,
            "action": "needs_label",
            "before": "(không có file)",
            "after": "chuyển người gán",
        })

    # 4. Xử lý các lỗi dòng nhãn theo từng file (drop_line, clip_box)
    line_level_issues = [
        i for i in error_issues
        if i.line is not None and i.image not in removed_images and i.code in (DROP_CODES | {"BOX_OUT_OF_IMAGE"})
    ]

    issues_by_stem: dict[str, list[Any]] = defaultdict(list)
    for iss in line_level_issues:
        issues_by_stem[iss.image].append(iss)

    for stem, stem_issues in issues_by_stem.items():
        lbl_path = ds.label_path(stem)
        if not lbl_path.exists():
            continue

        raw_lines = lbl_path.read_text(encoding="utf-8", errors="replace").splitlines()
        # Gom lỗi theo dòng gốc (1-based)
        by_line: dict[int, list[Any]] = defaultdict(list)
        for iss in stem_issues:
            by_line[iss.line].append(iss)

        line_actions: dict[int, tuple[str, str, str]] = {}
        for lineno, iss_list in sorted(by_line.items()):
            if lineno < 1 or lineno > len(raw_lines):
                continue
            orig_text = raw_lines[lineno - 1]

            # Kiểm tra xem dòng có lỗi xoá không (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO, DUP_BOX)
            has_drop = any(i.code in DROP_CODES for i in iss_list)

            if has_drop:
                line_actions[lineno] = ("drop_line", orig_text, "(xoá)")
            elif any(i.code == "BOX_OUT_OF_IMAGE" for i in iss_list):
                # Thử cắt box về [0, 1]
                try:
                    c, cx, cy, w, h = parse_yolo_line(orig_text)
                    x1 = cx - w / 2
                    x2 = cx + w / 2
                    y1 = cy - h / 2
                    y2 = cy + h / 2

                    x1_c = max(0.0, min(1.0, x1))
                    x2_c = max(0.0, min(1.0, x2))
                    y1_c = max(0.0, min(1.0, y1))
                    y2_c = max(0.0, min(1.0, y2))

                    new_w = x2_c - x1_c
                    new_h = y2_c - y1_c
                    if new_w <= 0.0 or new_h <= 0.0:
                        # Box nằm hoàn toàn ngoài ảnh -> xoá dòng
                        line_actions[lineno] = ("drop_line", orig_text, "(xoá: box ngoài ảnh)")
                    else:
                        new_cx = (x1_c + x2_c) / 2
                        new_cy = (y1_c + y2_c) / 2
                        clipped_line = f"{int(c)} {new_cx:.6f} {new_cy:.6f} {new_w:.6f} {new_h:.6f}"
                        line_actions[lineno] = ("clip_box", orig_text, clipped_line)
                except Exception:
                    line_actions[lineno] = ("drop_line", orig_text, "(xoá)")

        # Ghi lại file nhãn và lưu log các thay đổi
        new_lines: list[str] = []
        for idx, text in enumerate(raw_lines, 1):
            if idx in line_actions:
                act, before, after = line_actions[idx]
                fixes.append({
                    "image": stem,
                    "line": idx,
                    "action": act,
                    "before": before,
                    "after": after,
                })
                if act == "clip_box":
                    new_lines.append(after)
                # drop_line thì bỏ qua, không thêm vào new_lines
            else:
                new_lines.append(text)

        lbl_path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")

    return fixes
