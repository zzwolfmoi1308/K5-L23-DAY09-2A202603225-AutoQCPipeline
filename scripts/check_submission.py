#!/usr/bin/env python3
"""Tự kiểm tra bài nộp trước khi push (ĐÃ VIẾT SẴN). `python scripts/check_submission.py`  — hết LỖI mới nộp.
`--no-train`: bỏ qua phần train (chưa có Colab/GPU). Phần train được chấm riêng (15 điểm), không chặn phần còn lại."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NO_TRAIN = "--no-train" in sys.argv
errs, warns = [], []


def need(path, why=""):
    p = ROOT / path
    if not p.exists():
        errs.append(f"thiếu {path} {why}")
        return None
    return p


def no_todo(path):
    p = need(path)
    if p:
        t = p.read_text(encoding="utf-8")
        if "TODO(học viên)" in t:
            errs.append(f"{path} còn dấu TODO(học viên) chưa điền")
        if len(t.strip()) < 300:
            errs.append(f"{path} quá ngắn (<300 ký tự)")


# 1. README
first = next((l for l in (ROOT / "README.md").read_text(encoding="utf-8").splitlines() if l.startswith("# ")), "")
if not re.match(r"# Day 09 Lab — .+: \S+ - .+", first):
    errs.append("dòng tiêu đề (dòng `# ...` đầu tiên) của README.md phải là: '# Day 09 Lab — <Họ và tên>: <MSHV> - <Họ và tên>' (xem SUBMISSION.md)")

# 2. unit test
r = subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=no", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True)
last = [l for l in r.stdout.splitlines() if l.strip()][-1:] or ["(không có kết quả)"]
print("pytest:", last[0])
if r.returncode != 0:
    errs.append("pytest chưa xanh hết: " + last[0])

# 2b. file/giá trị KHÔNG được đổi (RULES.md) + không đọc đáp án
def sha1(p):
    return hashlib.sha1(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()    # chuẩn hoá CRLF (Windows) -> LF


pin = ROOT / "scripts/_protected.json"
if pin.exists():
    pinned = json.loads(pin.read_text(encoding="utf-8"))
    fixed_cfg = pinned.pop("__config_fixed__", None)
    for f, h in pinned.items():
        if not (ROOT / f).exists() or sha1(ROOT / f) != h:
            errs.append(f"{f} bị sửa so với bản đề (RULES.md: không sửa file đã viết sẵn / test / dữ liệu)")
    try:
        import yaml
        cur_cfg = yaml.safe_load((ROOT / "configs/pipeline.yaml").read_text(encoding="utf-8"))
        for s_, k_ in [("duplicates", "phash_dist"), ("second_opinion", "conf")]:
            cur_cfg[s_].pop(k_, None)
        if fixed_cfg is not None and cur_cfg != fixed_cfg:
            diff = sorted({k for k in set(cur_cfg) | set(fixed_cfg) if cur_cfg.get(k) != fixed_cfg.get(k)})
            errs.append(f"configs/pipeline.yaml: đã đổi mục ngoài 2 khoá `# <-- CALIBRATE` (bị cấm, RULES.md): {diff}")
    except Exception as e:  # noqa: BLE001
        errs.append(f"không đọc được configs/pipeline.yaml: {e}")
else:
    warns.append("thiếu scripts/_protected.json: không kiểm được file đề/cấu hình cố định")
prot = set(json.loads(pin.read_text(encoding="utf-8"))) if pin.exists() else set()
for f in [p for p in (ROOT / "pipeline").rglob("*.py") if str(p.relative_to(ROOT)) not in prot]:
    t = f.read_text(encoding="utf-8")
    for bad in ("review_reference", "MANIFEST", "answer_key", "data/test", "data/calib", "gold_val"):
        if bad in t and not (f.name == "duplicates.py" and bad in ("data/test", "gold_val")):
            errs.append(f"{f.relative_to(ROOT)} nhắc tới '{bad}': code kiểm không được đọc đáp án/tập test (duy nhất duplicates.py dùng reference_dirs từ cfg)")

# 3. báo cáo pipeline
for f in ["01_intake.csv", "02_error_list_v1.csv", "02_error_list_v1.txt", "03_fixes.csv", "04_error_list_v2.csv", "05_review_queue.csv",
          "06_review_log.csv", "07_error_list_v3.txt", "08_summary.json", "class_stats.csv"]:
    need(f"submission/reports/{f}", "(chạy `python -m pipeline.run`)")
s = ROOT / "submission/reports/08_summary.json"
if s.exists():
    v = json.loads(s.read_text(encoding="utf-8"))["verdict"]
    print("kết luận pipeline:", v["decision"], "-", "; ".join(v["reasons"]))
    d_all = json.loads(s.read_text(encoding="utf-8"))
    if d_all.get("config_sha1") != sha1(ROOT / "configs/pipeline.yaml"):
        errs.append("08_summary.json được sinh bởi cấu hình khác với configs/pipeline.yaml hiện tại: chạy lại `make run`")
    rp = ROOT / "submission/REPORT.md"
    if rp.exists() and v["decision"].lower() not in rp.read_text(encoding="utf-8").lower():
        errs.append(f"REPORT.md không nhắc tới kết luận của pipeline ({v['decision']})")
    if v["decision"] != "Rework":
        need("submission/export/clean_v1/manifest.json", "(pipeline phải xuất dataset khi không Rework)")
    e = ROOT / "submission/reports/07_error_list_v3.csv"
    if e.exists() and any(r["severity"] == "error" for r in csv.DictReader(open(e, encoding="utf-8"))) and v["decision"] != "Rework":
        errs.append("còn lỗi bắt buộc trong danh sách v3 nhưng kết luận không phải Rework (gate sai)")

# 4. calibration
need("submission/calibration/calibration_report.md", "(chạy `make calibrate`)")
cj = ROOT / "submission/calibration/calibration.json"
if cj.exists() and len(json.loads(cj.read_text(encoding="utf-8")).get("sweeps", {})) < 2:
    errs.append("calibration.json có < 2 sweep: chạy `make calibrate`")
try:
    import yaml
    cur = yaml.safe_load((ROOT / "configs/pipeline.yaml").read_text(encoding="utf-8"))
    if cur["second_opinion"]["conf"] > 0.85:
        errs.append(f"second_opinion.conf={cur['second_opinion']['conf']} > 0.85: ngưỡng quá cao làm hàng đợi rỗng giả (Release giả). Chọn theo sweep, không theo kết luận gate")
    if cur["duplicates"]["phash_dist"] > 20:
        errs.append("phash_dist > 20: ngưỡng ngoài vùng hợp lý")
    if (cur["duplicates"]["phash_dist"], cur["second_opinion"]["conf"]) == (2, 0.25):
        errs.append("configs/pipeline.yaml vẫn là giá trị khởi đầu: chưa calibrate?")
except Exception as e:  # noqa: BLE001
    errs.append(f"không đọc được configs/pipeline.yaml: {e}")

# 5. báo cáo
no_todo("submission/REPORT.md")

# 6. train so sánh (chấm riêng; --no-train để bỏ qua)
if NO_TRAIN:
    warns.append("bỏ qua phần train (--no-train): phần train 15 điểm chấm riêng, làm sau khi có Colab")
else:
    res = sorted((ROOT / "submission/results").glob("*_seed*.json"))
    by = {}
    for p in res:
        d = json.loads(p.read_text(encoding="utf-8"))
        by.setdefault(d["variant"], []).append(d["seed"])
    mf = ROOT / "submission/export/clean_v1/manifest.json"
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in res]
    for r in runs:
        if r["variant"] in ("clean",) and mf.exists():
            if r.get("manifest_sha1") != sha1(mf):
                errs.append(f"{r['variant']}_seed{r['seed']}.json: manifest_sha1 không khớp export hiện tại (train trên dữ liệu khác?)")
            if r.get("train_images") != json.loads(mf.read_text(encoding="utf-8"))["n_images"]:
                errs.append(f"{r['variant']}_seed{r['seed']}.json: train_images khác manifest.n_images")
    if len({(r["epochs"], r.get("batch"), r.get("model")) for r in runs}) > 1:
        errs.append("các lần train dùng epoch/batch/model khác nhau: so sánh không công bằng")
    if len({tuple(sorted(r["seed"] for r in runs if r["variant"] == v)) for v in by if v in ("raw", "clean")}) > 1:
        warns.append("raw và clean không có cùng danh sách seed")
    for v in ("raw", "clean"):
        if v not in by:
            errs.append(f"thiếu kết quả train biến thể '{v}' trong submission/results/")
        elif len(by[v]) < 2:
            warns.append(f"biến thể '{v}' chỉ có {len(by[v])} seed: nên ≥ 2 để biết nhiễu")
    need("submission/results/comparison.md", "(python scripts/summarize_results.py)")


print()
for w in warns:
    print("CẢNH BÁO:", w)
for e in errs:
    print("LỖI:", e)
print(f"\n{len(errs)} lỗi, {len(warns)} cảnh báo")
sys.exit(1 if errs else 0)
