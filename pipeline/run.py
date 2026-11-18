"""Orchestrator: chạy cả pipeline 5 bước bằng MỘT lệnh (ĐÃ VIẾT SẴN — đọc kỹ để hiểu luồng).

    python -m pipeline.run                       # 1 lệnh: nhận → QC → sửa tự động → QC → hàng đợi → người duyệt (mô phỏng) → QC → cửa chặn → xuất
    python -m pipeline.run --no-review           # dừng sau khi sinh hàng đợi (để người thật duyệt) -> mã thoát 30 (TẠM DỪNG)
    python -m pipeline.run --resume-after-review # chạy tiếp: ảnh có nhãn ĐỔI nội dung so với lúc dừng (băm sha1 sau chuẩn hoá) được tính là đã duyệt
    python -m pipeline.run --budget 0 --drop-unlabeled --export-name clean_auto --reports work/reports_auto   # thí nghiệm (BẮT BUỘC --reports riêng, kẻo ghi đè submission/reports): không có người duyệt (biến thể `auto` khi train)

Mã thoát (để CI / Makefile dùng): 0 = Release, 10 = Hold, 20 = Rework, 30 = tạm dừng chờ người duyệt, 1 = script lỗi.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

from . import checks
from .common import ERROR, ROOT, Dataset, load_config, write_issues_csv
from .steps import autofix, export, gate, intake, review_queue
from .steps.report import write_report

EXIT = {"Release": 0, "Hold": 10, "Rework": 20}
PAUSED = 30


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def qc(ds, cfg):
    return checks.run_checks(checks.QC_CHECKS, ds, cfg)


def sha(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else ""


def nsha(p: Path) -> str:
    """sha1 của nội dung nhãn đã chuẩn hoá (bỏ dòng trống, khoảng trắng thừa): thêm dòng trống KHÔNG tính là 'đã duyệt'."""
    if not p.exists():
        return ""
    return hashlib.sha1("\n".join(" ".join(l.split()) for l in p.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()).encode()).hexdigest()


def snapshot(ds: Dataset) -> dict:
    return {p.stem: nsha(ds.label_path(p.stem)) for p in ds.image_files()}


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--work", default="work/run", help="thư mục làm việc (không commit)")
    ap.add_argument("--reports", default="submission/reports", help="nơi ghi báo cáo (commit)")
    ap.add_argument("--export-dir", default="submission/export")
    ap.add_argument("--export-name", default="clean_v1")
    ap.add_argument("--config", default="configs/pipeline.yaml")
    ap.add_argument("--no-review", action="store_true", help="dừng sau khi sinh hàng đợi duyệt (mã thoát 30)")
    ap.add_argument("--resume-after-review", action="store_true")
    ap.add_argument("--export-on-rework", action="store_true",
                    help="vẫn xuất bản NHÁP khi kết luận Rework (manifest ghi decision=Rework) để bạn còn train so sánh; KHÔNG phải bản phát hành")
    ap.add_argument("--drop-unlabeled", action="store_true",
                    help="THÍ NGHIỆM (không người duyệt): loại ảnh vẫn chưa có file nhãn sau bước duyệt, thay vì để pipeline Rework")
    ap.add_argument("--budget", type=int, help="ngân sách người duyệt (chỉ được NHỎ HƠN hoặc bằng cấu hình), dùng cho thí nghiệm")
    a = ap.parse_args(argv)

    cfg = load_config(ROOT / a.config)
    budget = cfg["review"]["budget_images"]
    if a.budget is not None:
        if a.budget > budget:
            sys.exit(f"--budget {a.budget} vượt ngân sách cho phép {budget}")
        budget = a.budget
    work, rep = ROOT / a.work, ROOT / a.reports
    ds_dir = work / "ds"
    t0 = time.time()
    rep.mkdir(parents=True, exist_ok=True)

    if not a.resume_after_review:
        # dọn kết quả cũ: một lần chạy Rework không được để lại export của lần trước
        for f in list(rep.glob("0[1-8]*")) + [rep / "class_stats.csv"]:
            f.unlink(missing_ok=True)
        shutil.rmtree(ROOT / a.export_dir / a.export_name, ignore_errors=True)
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        # ---- Bước 1: nhận dữ liệu
        log("Bước 1/5  Nhận dữ liệu (ảnh hỏng, kích thước, trùng, rò rỉ test)")
        accepted, intake_issues = intake.run(ROOT / a.raw, ds_dir, cfg)
        n_scanned = len(Dataset(ROOT / a.raw, cfg["classes"]).image_files())
        write_report(intake_issues, rep / "01_intake", "Bước 1 — nhận dữ liệu: ảnh bị loại", n_scanned)
        ds = Dataset(ds_dir, cfg["classes"])
        log(f"          nhận {len(accepted)}/{n_scanned} ảnh, loại {len({i.image for i in intake_issues if i.severity == ERROR})}")

        # ---- Bước 4 (vòng 1): QC trên nhãn thô
        log("Bước 4/5  QC tự động — vòng 1 (nhãn thô)")
        issues1 = qc(ds, cfg)
        write_report(intake_issues + issues1, rep / "02_error_list_v1", "Danh sách lỗi — TRƯỚC khi sửa (v1)", len(accepted))
        n_err1 = sum(i.severity == ERROR for i in issues1)
        log(f"          {n_err1} lỗi bắt buộc, {len(issues1) - n_err1} cảnh báo")

        # ---- Sửa tự động lỗi bắt buộc (bước 2 "pre-label" đã diễn ra TRƯỚC khi lô tới tay bạn: giảng viên chạy yolo26n)
        log("Bước 4/5  Sửa tự động lỗi bắt buộc (ảnh chưa có nhãn -> chuyển người gán)")
        fixes = autofix.fix(ds, issues1, cfg)
        write_csv(rep / "03_fixes.csv", fixes, ["image", "line", "action", "before", "after"])
        log(f"          {len(fixes)} thay đổi -> 03_fixes.csv")

        # ---- Bước 4 (vòng 2)
        log("Bước 4/5  QC tự động — vòng 2 (sau sửa tự động)")
        issues2 = qc(ds, cfg)
        stems = {p.stem for p in ds.image_files()}
        write_report(issues2, rep / "04_error_list_v2", "Danh sách lỗi — SAU sửa tự động (v2)", len(stems))
        queue = review_queue.build_queue(issues2, fixes, stems, cfg)
        write_csv(rep / "05_review_queue.csv", queue, ["image", "priority", "codes"])
        log(f"          {len([i for i in issues2 if i.severity == ERROR])} lỗi bắt buộc còn lại; hàng đợi người duyệt: {len(queue)} ảnh")
        (work / "snapshot.json").write_text(json.dumps(snapshot(ds)), encoding="utf-8")

        # ---- Bước 3: người duyệt
        if a.no_review:
            log("TẠM DỪNG: sửa nhãn các ảnh đầu 05_review_queue.csv trong work/run/ds/labels/ (tối đa "
                f"{budget} ảnh), rồi chạy lại với --resume-after-review")
            return PAUSED
        from scripts.human_review_sim import simulate
        log(f"Bước 3/5  Người duyệt (MÔ PHỎNG) — ngân sách {budget} ảnh")
        reviewed = simulate(rep / "05_review_queue.csv", ds_dir, budget, rep / "06_review_log.csv")
    else:
        ds = Dataset(ds_dir, cfg["classes"])
        before = json.loads((work / "snapshot.json").read_text(encoding="utf-8"))
        now = snapshot(ds)
        reviewed = sorted(k for k in now if now[k] != before.get(k))
        if len(reviewed) > budget:
            log(f"LỖI: {len(reviewed)} ảnh bị đổi nhãn > ngân sách duyệt {budget}")
            return 1
        write_csv(rep / "06_review_log.csv", [dict(image=k, result="đã duyệt: nhãn đổi nội dung (sha1)", codes="") for k in reviewed], ["image", "result", "codes"])
        log(f"Bước 3/5  Người duyệt (thật): {len(reviewed)} ảnh có nhãn đã đổi")
    (work / "reviewed.txt").write_text("\n".join(reviewed) + "\n", encoding="utf-8")

    # ---- Bước 4 (vòng 3) + cửa chặn
    ds = Dataset(ds_dir, cfg["classes"])
    stems = {p.stem for p in ds.image_files()}
    log("Bước 4/5  QC tự động — vòng 3 (sau người duyệt) + cửa chặn")
    if a.drop_unlabeled:
        dropped = [p.stem for p in ds.image_files() if not ds.label_path(p.stem).exists()]
        for s in dropped:
            ds.image_path(s).unlink()
        write_csv(rep / "03c_dropped_unlabeled.csv", [dict(image=s, reason="chưa có nhãn, không có người gán (--drop-unlabeled)") for s in dropped], ["image", "reason"])
        log(f"          --drop-unlabeled: loại {len(dropped)} ảnh chưa có nhãn -> 03c_dropped_unlabeled.csv")
        ds = Dataset(ds_dir, cfg["classes"])
        stems = {p.stem for p in ds.image_files()}
    issues3 = qc(ds, cfg)
    if any(i.severity == ERROR for i in issues3):         # người duyệt cũng có thể để lại lỗi cú pháp: máy sửa lại một vòng
        fixes2 = autofix.fix(ds, issues3, cfg)
        write_csv(rep / "03b_fixes_after_review.csv", fixes2, ["image", "line", "action", "before", "after"])
        log(f"          {len(fixes2)} sửa tự động sau người duyệt -> 03b_fixes_after_review.csv")
        issues3 = qc(ds, cfg)
    verdict = gate.decide(issues3, stems, cfg, set(reviewed))
    write_report(issues3, rep / "07_error_list_v3", "Danh sách lỗi — SAU người duyệt (v3)", len(stems), verdict)
    from .checks.stats import class_counts
    with open(rep / "class_stats.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class_token", "boxes"])
        w.writerows(sorted(class_counts(ds).items()))
    log(f"          kết luận: {verdict['decision'].upper()} — {'; '.join(verdict['reasons'])}")

    # ---- Bước 5: xuất (chỉ khi không Rework)
    exported = None
    if verdict["decision"] != "Rework" or a.export_on_rework:
        exported = export.export(ds, ROOT / a.export_dir, a.export_name, verdict, cfg)
        where = exported.relative_to(ROOT) if exported.is_relative_to(ROOT) else exported
        note = "bản phát hành" if verdict["decision"] == "Release" else f"bản NHÁP để thử nghiệm — {verdict['decision']}: CHƯA được phát hành"
        log(f"Bước 5/5  Xuất dataset: {where}  ({note})")
    else:
        log("Bước 5/5  KHÔNG xuất: còn lỗi bắt buộc (Rework) — trả về bước 3")
    (rep / "08_summary.json").write_text(json.dumps(dict(
        verdict=verdict, reviewed=len(reviewed), budget=budget, seconds=round(time.time() - t0, 1), exported=str(exported) if exported else None,
        config_sha1=sha(ROOT / a.config), review_sim_sha1=sha(ROOT / "scripts/human_review_sim.py")), indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"xong trong {time.time() - t0:.1f}s")
    return EXIT[verdict["decision"]]


if __name__ == "__main__":
    sys.exit(main())
