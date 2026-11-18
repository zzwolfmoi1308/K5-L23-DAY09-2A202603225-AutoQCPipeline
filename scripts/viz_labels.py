#!/usr/bin/env python3
"""Vẽ nhãn lên ảnh để nhìn lỗi bằng mắt (ĐÃ VIẾT SẴN).

    python scripts/viz_labels.py img_0001 img_0030 --src data/raw        # -> work/viz/<tên>.png
    python scripts/viz_labels.py --from-csv submission/reports/05_review_queue.csv --top 12 --src work/run/ds
Mỗi lớp một màu: car xanh dương, person đỏ, truck cam, bus tím. Dòng hỏng được bỏ qua.
"""
import argparse
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.common import Dataset, parse_yolo_line  # noqa: E402

COLORS = ["#2563eb", "#dc2626", "#ea580c", "#9333ea"]
NAMES = ["car", "person", "truck", "bus"]


def draw(ds, stem, out):
    p = ds.image_path(stem)
    try:
        im = Image.open(p).convert("RGB")
    except Exception as e:  # noqa: BLE001  ảnh hỏng (CORRUPT_IMAGE) là một phần của bài: báo và bỏ qua
        print(f"bỏ qua {stem}: không mở được ảnh ({type(e).__name__}) — đây chính là lỗi mà check `images` phải bắt")
        return
    W, H = im.size
    d = ImageDraw.Draw(im)
    for no, ln in ds.read_label_lines(stem) or []:
        try:
            c, x, y, w, h = parse_yolo_line(ln)
        except ValueError:
            continue
        col = COLORS[c % 4] if 0 <= c < 4 else "#000000"
        box = [(x - w / 2) * W, (y - h / 2) * H, (x + w / 2) * W, (y + h / 2) * H]
        d.rectangle(box, outline=col, width=3)
        d.text((box[0] + 3, box[1] + 2), f"{no}:{NAMES[c] if 0 <= c < 4 else c}", fill=col)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stems", nargs="*")
    ap.add_argument("--src", default="data/raw")
    ap.add_argument("--from-csv")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--out", default="work/viz")
    a = ap.parse_args()
    stems = list(a.stems)
    if a.from_csv:
        stems += [r["image"] for r in list(csv.DictReader(open(ROOT / a.from_csv, encoding="utf-8")))[: a.top]]
    ds = Dataset(ROOT / a.src, ["car", "person", "truck", "bus"])
    for s in stems:
        draw(ds, s, ROOT / a.out / f"{s}.png")
    print(f"đã vẽ {len(stems)} ảnh vào {a.out}/")
