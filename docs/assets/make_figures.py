"""Sinh hình minh hoạ cho README (sơ đồ do giảng viên vẽ, không phải ảnh chụp màn hình). Học viên không cần chạy.

    python docs/assets/make_figures.py
Cần Pillow + matplotlib (font DejaVu có đủ dấu tiếng Việt). Ảnh mẫu lấy từ data/gold_val (nhãn đã đúng).
"""
from __future__ import annotations

import math
from pathlib import Path

from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
NAVY, TEAL, ORANGE, GREEN, RED, PURPLE, GRAY = "#0b1f3a", "#12b3a8", "#ff8a3d", "#2fbf71", "#e5484d", "#7b61ff", "#6b7686"
CLS = {0: ("car", ORANGE), 1: ("person", GREEN), 2: ("truck", PURPLE), 3: ("bus", RED)}


def font(size, bold=False):
    p = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal"))
    return ImageFont.truetype(p, size)


def text(d, xy, s, size=20, fill="white", bold=False, anchor="la"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def rrect(d, box, r=14, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def gradient(w, h, c1, c2):
    im = Image.new("RGB", (w, h))
    px = im.load()
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    for x in range(w):
        for y in range(h):
            t = x / w * 0.7 + y / h * 0.3
            px[x, y] = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
    return im


def arrow(d, p1, p2, fill=GRAY, width=4):
    d.line([p1, p2], fill=fill, width=width)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    for s in (-0.5, 0.5):
        d.line([p2, (p2[0] - 14 * math.cos(ang + s), p2[1] - 14 * math.sin(ang + s))], fill=fill, width=width)


def fit(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def sample(n):
    """n ảnh gold_val có vẽ box nhãn đúng."""
    out = []
    for p in sorted((ROOT / "data/gold_val/images").glob("*.jpg"))[: n * 3]:
        lab = (ROOT / "data/gold_val/labels" / (p.stem + ".txt"))
        if not lab.exists() or not lab.read_text().strip():
            continue
        im = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(im)
        for ln in lab.read_text().splitlines():
            c, x, y, w, h = ln.split()[:5]
            c, x, y, w, h = int(c), float(x), float(y), float(w), float(h)
            nm, col = CLS.get(c, ("?", GRAY))
            box = ((x - w / 2) * im.width, (y - h / 2) * im.height, (x + w / 2) * im.width, (y + h / 2) * im.height)
            d.rectangle(box, outline=col, width=3)
        out.append(im)
        if len(out) == n:
            break
    return out


def hero():
    W, H = 1600, 520
    im = gradient(W, H, NAVY, "#0f5f66")
    d = ImageDraw.Draw(im)
    text(d, (70, 70), "DAY 09 · LAB", 22, TEAL, True)
    text(d, (70, 112), "Pipeline kiểm nhãn", 56, "white", True)
    text(d, (70, 176), "tự động", 56, "white", True)
    text(d, (70, 252), "Nhận · QC · Sửa · Cửa chặn · Xuất", 28, "white")
    text(d, (70, 300), "Máy kiểm quy tắc, người kiểm ý nghĩa.", 22, "#cfe8ee")
    text(d, (70, 332), "Một lệnh chạy hết; bạn phải chứng minh nó có ích.", 22, "#cfe8ee")
    x = 70
    for name, c in [("Release", GREEN), ("Hold", ORANGE), ("Rework", RED), ("calibration", PURPLE), ("Colab", TEAL)]:
        w = d.textlength(name, font=font(20, True)) + 36
        rrect(d, (x, 380, x + w, 424), 22, fill=c)
        text(d, (x + 18, 391), name, 20, "white", True)
        x += w + 14
    text(d, (70, 455), "224 ảnh · 4 lớp car/person/truck/bus · 22 mã lỗi", 20, "#9fc7cf")
    for k, s in enumerate(sample(3)):
        t = fit(s, 330, 220)
        im.paste(t, (860 + (k % 2) * 350, 30 + (k // 2) * 250 + (k % 2) * 40))
    im.save(HERE / "hero.png")


def pipeline():
    W, H = 1600, 520
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    text(d, (40, 24), "Pipeline (MỘT lệnh: python -m pipeline.run)", 30, NAVY, True)
    steps = [("Nhận dữ liệu", "máy", "ảnh hỏng, nhỏ,\ntrùng, rò rỉ test", TEAL),
             ("Gán, sửa", "người", "hàng đợi ưu tiên\nngân sách 80 ảnh", ORANGE), ("QC tự động", "máy", "5 check + sửa tự động\n+ cửa chặn", PURPLE), ("Xuất", "máy", "dataset + manifest\n(truy vết)", GREEN)]
    x0, y0, w, h, gap = 40, 110, 350, 190, 50
    for i, (t, who, sub, c) in enumerate(steps):
        x = x0 + i * (w + gap)
        rrect(d, (x, y0, x + w, y0 + h), 18, fill=c)
        text(d, (x + 20, y0 + 18), t, 26, "white", True)
        text(d, (x + 20, y0 + 58), who, 20, "#ffffffcc")
        text(d, (x + 20, y0 + 100), sub, 19, "white")
        if i < 3:
            arrow(d, (x + w + 4, y0 + h // 2), (x + w + gap - 4, y0 + h // 2))
    # cửa chặn
    text(d, (40, 350), "Cửa chặn (sau QC tự động):", 24, NAVY, True)
    for i, (t, sub, c) in enumerate([("Release", "0 lỗi bắt buộc,\ncảnh báo < 10% ảnh", GREEN), ("Hold", "cảnh báo ≥ 10%\n→ người xem thêm", ORANGE), ("Rework", "còn lỗi bắt buộc\n→ KHÔNG xuất", RED)]):
        x = 40 + i * 330
        rrect(d, (x, 395, x + 300, 495), 14, fill=c)
        text(d, (x + 16, 405), t, 24, "white", True)
        text(d, (x + 16, 440), sub, 18, "white")
    text(d, (1040, 405), "Mã thoát: 0 · 10 · 20", 24, NAVY, True)
    text(d, (1040, 445), "30 = tạm dừng chờ người duyệt", 20, GRAY)
    im.save(HERE / "pipeline.png")


def machine_human():
    W, H = 1600, 520
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    text(d, (40, 24), "Máy kiểm quy tắc, người kiểm ý nghĩa", 30, NAVY, True)
    cols = [("MÁY bắt chắc", GREEN, ["thiếu file nhãn", "ID lớp không tồn tại", "box tràn ngoài ảnh", "ảnh trùng hệt / gần đúng", "ảnh hỏng, quá nhỏ"]),
            ("MÁY gợi ý (second opinion)", ORANGE, ["thiếu box (model lớn thấy, nhãn không có)", "box thừa", "box lỏng", "nghi gán nhầm lớp"]),
            ("NGƯỜI quyết", RED, ["nhầm lớp hợp lệ (xe tải/bus)", "vật bị che, mơ hồ", "đúng/sai theo guideline", "box lệch nhẹ"])]
    for i, (t, c, items) in enumerate(cols):
        x = 40 + i * 520
        rrect(d, (x, 90, x + 490, 480), 18, outline=c, width=4)
        rrect(d, (x, 90, x + 490, 150), 18, fill=c)
        text(d, (x + 20, 105), t, 26, "white", True)
        for k, s in enumerate(items):
            text(d, (x + 24, 175 + k * 56), "• " + s, 22, NAVY)
    im.save(HERE / "machine_human.png")


def sample_grid():
    ims = sample(8)
    W = 4 * 400
    g = Image.new("RGB", (W, 2 * 300), "white")
    for k, s in enumerate(ims):
        g.paste(fit(s, 400, 300), ((k % 4) * 400, (k // 4) * 300))
    g.save(HERE / "sample_grid.jpg", quality=88)


if __name__ == "__main__":
    hero(); pipeline(); machine_human(); sample_grid()
    print("ok")
