"""Dữ liệu giả cho test (ĐÃ VIẾT SẴN). Cấu hình test cố định, KHÔNG phụ thuộc configs/pipeline.yaml của bạn."""
import io
import random
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.common import Dataset  # noqa: E402

CFG = {
    "classes": ["car", "person", "truck", "bus"],
    "class_aliases": {"Person": "person"},
    "intake": {"min_side_px": 200, "reference_dirs": []},
    "duplicates": {"phash_dist": 8},
    "label_format": {"overflow_tol": 0.001, "min_box_px": 12, "max_box_frac": 0.95, "dup_box_iou": 0.9},
    "stats": {"rare_class_min_boxes": 3, "dense_image_max_boxes": 5},
    "second_opinion": {"conf": 0.5, "min_area_px": 600, "fp_conf": 0.25, "iou_missing": 0.3, "iou_match": 0.5, "iou_loose": 0.6},
    "gate": {"warn_ratio_hold": 0.10},
    "models": {"checker": {"weights": "yolo26l.pt", "conf": 0.1, "cache": "none.json"}},
}


@pytest.fixture
def cfg():
    import copy
    return copy.deepcopy(CFG)


def smooth_image(seed, size=(320, 240)):
    """Ảnh có cấu trúc ổn định (lưới màu 8x8 phóng to) → phash của bản thu nhỏ vẫn gần bản gốc."""
    r = random.Random(seed)
    grid = Image.new("RGB", (8, 8))
    grid.putdata([(r.randrange(256), r.randrange(256), r.randrange(256)) for _ in range(64)])
    return grid.resize(size, Image.BICUBIC)


def save(im, path, fmt="JPEG", q=92):
    im.save(path, fmt, quality=q) if fmt == "JPEG" else im.save(path, fmt)


@pytest.fixture
def make_ds(tmp_path, cfg):
    """make_ds(images={'a': seed|Image|bytes}, labels={'a': ['0 0.5 0.5 0.2 0.2', ...]}, names=[...], ext='.jpg') -> Dataset"""
    def _make(images=None, labels=None, names=None, ext=".jpg", size=(320, 240)):
        root = tmp_path / "ds"
        (root / "images").mkdir(parents=True, exist_ok=True)
        (root / "labels").mkdir(parents=True, exist_ok=True)
        for k, v in (images or {}).items():
            p = root / "images" / (k + (ext if "." not in k else ""))
            if isinstance(v, (bytes, bytearray)):
                p.write_bytes(v)
            else:
                im = v if isinstance(v, Image.Image) else smooth_image(v, size)
                save(im, p, "PNG" if p.suffix.lower() == ".png" else "JPEG")
        for k, lines in (labels or {}).items():
            (root / "labels" / f"{k}.txt").write_text("".join(l + "\n" for l in lines))
        n = names if names is not None else cfg["classes"]
        (root / "data.yaml").write_text("path: .\nnames:\n" + "".join(f"  {i}: {x}\n" for i, x in enumerate(n)))
        return Dataset(root, cfg["classes"])
    return _make
