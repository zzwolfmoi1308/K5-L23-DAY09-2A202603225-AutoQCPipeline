"""Kiểm tra tích hợp: cả pipeline chạy bằng MỘT lệnh trên data/raw (chỉ xanh khi các phần trước đã xong)."""
import csv
import json

from pipeline import run


def go(tmp_path, tag):
    argv = ["--work", str(tmp_path / f"w{tag}"), "--reports", str(tmp_path / f"r{tag}"), "--export-dir", str(tmp_path / f"e{tag}")]
    code = run.main(argv)
    return code, tmp_path / f"r{tag}", tmp_path / f"e{tag}"


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def test_one_command_pipeline(tmp_path):
    code, rep, exp = go(tmp_path, "1")
    assert code in (0, 10), f"mã thoát {code}: pipeline kết luận Rework (còn lỗi bắt buộc) hoặc sai"
    for f in ["01_intake.csv", "02_error_list_v1.csv", "03_fixes.csv", "04_error_list_v2.csv", "05_review_queue.csv", "06_review_log.csv", "07_error_list_v3.csv", "08_summary.json"]:
        assert (rep / f).exists(), f
    assert len(rows(rep / "01_intake.csv")) >= 15, "bước 1 nên loại ≥ 15 ảnh (hỏng, nhỏ, trùng, rò rỉ)"
    v1 = {r["code"] for r in rows(rep / "02_error_list_v1.csv")}
    assert {"MISSING_LABEL_FILE", "BAD_CLASS_ID", "BOX_OUT_OF_IMAGE", "BOX_ZERO", "BAD_FORMAT", "DUP_BOX", "BAD_CLASS_NAME"} <= v1
    assert not [r for r in rows(rep / "07_error_list_v3.csv") if r["severity"] == "error"], "sau sửa tự động + duyệt không được còn lỗi bắt buộc"
    assert (exp / "clean_v1" / "manifest.json").exists()


def test_deterministic_and_repeatable(tmp_path):
    c1, r1, _ = go(tmp_path, "a")
    c2, r2, _ = go(tmp_path, "b")
    assert c1 == c2
    assert (r1 / "02_error_list_v1.csv").read_text(encoding="utf-8") == (r2 / "02_error_list_v1.csv").read_text(encoding="utf-8")
    assert json.loads((r1 / "08_summary.json").read_text(encoding="utf-8"))["verdict"] == json.loads((r2 / "08_summary.json").read_text(encoding="utf-8"))["verdict"]


def test_pause_then_resume_with_human_edits(tmp_path):
    """Người duyệt thật: --no-review dừng (mã 30); sửa nhãn vài ảnh đầu hàng đợi; --resume-after-review tính đúng số ảnh đã duyệt."""
    base = ["--work", str(tmp_path / "w"), "--reports", str(tmp_path / "r"), "--export-dir", str(tmp_path / "e")]
    assert run.main(base + ["--no-review"]) == 30
    q = rows(tmp_path / "r" / "05_review_queue.csv")[:3]
    for r in q:                                            # "người" sửa: thêm một box vào ảnh
        p = tmp_path / "w" / "ds" / "labels" / f"{r['image']}.txt"
        p.write_text((p.read_text(encoding="utf-8") if p.exists() else "") + "0 0.5 0.5 0.1 0.1\n", encoding="utf-8")   # ảnh chưa có nhãn: người tạo file
    code = run.main(base + ["--resume-after-review"])
    assert code == 20, "3 ảnh đầu hàng đợi là ảnh CHƯA CÓ NHÃN; người mới gán 3/6 ảnh -> còn lỗi bắt buộc -> Rework (không được xuất)"
    assert json.loads((tmp_path / "r" / "08_summary.json").read_text(encoding="utf-8"))["reviewed"] == 3


def test_blank_line_edit_does_not_count_as_review(tmp_path):
    """Thêm dòng trống / khoảng trắng vào nhãn KHÔNG được tính là 'người đã duyệt' (chống gian lận ngân sách)."""
    base = ["--work", str(tmp_path / "w"), "--reports", str(tmp_path / "r"), "--export-dir", str(tmp_path / "e")]
    assert run.main(base + ["--no-review"]) == 30
    for r in rows(tmp_path / "r" / "05_review_queue.csv")[:5]:
        p = tmp_path / "w" / "ds" / "labels" / f"{r['image']}.txt"
        if p.exists():
            p.write_text(p.read_text(encoding="utf-8") + "\n\n   \n", encoding="utf-8")
    run.main(base + ["--resume-after-review"])
    assert json.loads((tmp_path / "r" / "08_summary.json").read_text(encoding="utf-8"))["reviewed"] == 0


def test_export_on_rework_flag(tmp_path):
    base = ["--work", str(tmp_path / "w"), "--reports", str(tmp_path / "r"), "--export-dir", str(tmp_path / "e"), "--budget", "0"]
    assert run.main(base) == 20 and not (tmp_path / "e" / "clean_v1").exists()
    assert run.main(base + ["--export-on-rework"]) == 20
    man = json.loads((tmp_path / "e" / "clean_v1" / "manifest.json").read_text(encoding="utf-8"))
    assert man["decision"]["decision"] == "Rework"
