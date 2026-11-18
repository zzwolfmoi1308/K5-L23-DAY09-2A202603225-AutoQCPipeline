"""Phần dùng chung (ĐÃ VIẾT SẴN — không cần sửa).

- `Issue`: một dòng trong báo cáo lỗi.
- `Dataset`: bọc một thư mục `images/` + `labels/` + `data.yaml` theo kiểu YOLO.
- `parse_yolo_line`, `iou_xywh`: hàm nhỏ dùng trong nhiều check.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMG_EXTS = {".jpg", ".jpeg", ".png"}          # so sánh SAU KHI hạ chữ thường (.JPG vẫn là ảnh!)
ERROR, WARN = "error", "warn"                 # lỗi bắt buộc (chặn pipeline) | cảnh báo (chuyển người xem)


@dataclass
class Issue:
    """Một lỗi/cảnh báo. `image` là *tên file không đuôi* (stem), hoặc 'data.yaml' cho lỗi cấp dataset."""
    check: str                 # tên module check, ví dụ "label_format"
    severity: str              # ERROR | WARN
    code: str                  # mã lỗi, ví dụ "BOX_OUT_OF_IMAGE"
    image: str
    message: str
    line: int | None = None    # số dòng (đếm từ 1) trong file nhãn, nếu có
    extra: dict = field(default_factory=dict)

    def row(self) -> dict:
        d = asdict(self)
        d["extra"] = json.dumps(self.extra, ensure_ascii=False) if self.extra else ""
        d["line"] = "" if self.line is None else self.line
        return d


def load_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else ROOT / "configs" / "pipeline.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def parse_yolo_line(text: str) -> tuple[int, float, float, float, float]:
    """'1 0.5 0.5 0.2 0.3' -> (1, 0.5, 0.5, 0.2, 0.3). Ném ValueError nếu không đúng 5 cột số."""
    parts = text.split()
    if len(parts) != 5:
        raise ValueError(f"cần 5 cột, có {len(parts)}")
    c = float(parts[0])
    if c != int(c):
        raise ValueError("id lớp phải là số nguyên")
    vals = [float(v) for v in parts[1:]]
    if any(v != v or v in (float("inf"), float("-inf")) for v in vals):   # nan / inf
        raise ValueError("giá trị nan/inf")
    return (int(c), *vals)


def iou_xywh(a, b) -> float:
    """IoU của hai box (cx, cy, w, h), cùng hệ chuẩn hoá."""
    ax1, ay1, ax2, ay2 = a[0] - a[2] / 2, a[1] - a[3] / 2, a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1, bx2, by2 = b[0] - b[2] / 2, b[1] - b[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2
    iw, ih = max(0.0, min(ax2, bx2) - max(ax1, bx1)), max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


class Dataset:
    """Thư mục dataset kiểu YOLO: <root>/images, <root>/labels, <root>/data.yaml."""

    def __init__(self, root: str | Path, classes: list[str]):
        self.root = Path(root)
        self.images_dir = self.root / "images"
        self.labels_dir = self.root / "labels"
        self.yaml_path = self.root / "data.yaml"
        self.classes = list(classes)
        self._size_cache: dict[str, tuple[int, int] | None] = {}

    # --- ảnh
    def image_files(self) -> list[Path]:
        """Mọi ảnh (đuôi .jpg/.jpeg/.png, KHÔNG phân biệt hoa thường), sắp xếp theo tên."""
        if not self.images_dir.exists():
            return []
        return sorted(p for p in self.images_dir.iterdir() if p.suffix.lower() in IMG_EXTS)

    def image_path(self, stem: str) -> Path | None:
        for p in self.image_files():
            if p.stem == stem:
                return p
        return None

    def image_size(self, stem: str) -> tuple[int, int] | None:
        """(rộng, cao) px; None nếu ảnh không mở được."""
        if stem not in self._size_cache:
            p = self.image_path(stem)
            try:
                with Image.open(p) as im:
                    self._size_cache[stem] = im.size
            except Exception:
                self._size_cache[stem] = None
        return self._size_cache[stem]

    # --- nhãn
    def label_path(self, stem: str) -> Path:
        return self.labels_dir / f"{stem}.txt"

    def label_files(self) -> list[Path]:
        return sorted(self.labels_dir.glob("*.txt")) if self.labels_dir.exists() else []

    def read_label_lines(self, stem: str) -> list[tuple[int, str]] | None:
        """[(số dòng từ 1, nội dung)] bỏ dòng trống; None nếu KHÔNG có file nhãn."""
        p = self.label_path(stem)
        if not p.exists():
            return None
        return [(i, ln) for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1) if ln.strip()]

    def valid_boxes(self, stem: str) -> list[tuple[int, float, float, float, float]]:
        """Các dòng parse được và có id lớp hợp lệ (bỏ qua dòng hỏng — check khác sẽ báo)."""
        out = []
        for _, ln in self.read_label_lines(stem) or []:
            try:
                b = parse_yolo_line(ln)
            except ValueError:
                continue
            if 0 <= b[0] < len(self.classes):
                out.append(b)
        return out

    # --- data.yaml
    def yaml_names(self) -> dict[int, str]:
        if not self.yaml_path.exists():
            return {}
        d = yaml.safe_load(self.yaml_path.read_text(encoding="utf-8")) or {}
        n = d.get("names", {})
        return {i: v for i, v in enumerate(n)} if isinstance(n, list) else {int(k): v for k, v in n.items()}


def write_issues_csv(issues: list[Issue], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cols = ["check", "severity", "code", "image", "line", "message", "extra"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for i in issues:
            w.writerow(i.row())
