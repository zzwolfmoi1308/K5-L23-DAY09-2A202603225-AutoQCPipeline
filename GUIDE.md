# Hướng dẫn làm lab (5 bước)

Bài **cá nhân**, khoảng **4,5 giờ** (có thể chia 2 buổi: buổi 1 = Bước 1–2, buổi 2 = Bước 3–5). **Train Colab là phần tùy chọn, chấm riêng** (~35', chạy nền ~20'): không làm thì `make check-core`, tối đa 85/100. Mốc giờ ở [CHECKPOINTS.md](CHECKPOINTS.md) là mốc tự kiểm, chậm hơn là bình thường. Lệnh chạy **từ thư mục gốc repo**.
Quy tắc: [RULES.md](RULES.md) · Chấm điểm: [RUBRIC.md](RUBRIC.md) · Nộp: [SUBMISSION.md](SUBMISSION.md).

| Bước | Việc | Lệnh chính | Sản phẩm | Thời gian |
|---|---|---|---|---|
| 1 | Chuẩn bị, nhìn dữ liệu | `pip install -r requirements.txt`, `python -m pytest -q` | — | ~30' |
| 2 | **Viết 4 module** (TDD) | `pytest tests/test_<tên>.py -q` | test xanh hết | ~2 giờ 15' |
| 3 | Calibrate 2 ngưỡng | `make calibrate` | `calibration/`, `configs/pipeline.yaml` | ~30' |
| 4 | Chạy pipeline (+ train Colab: tùy chọn) | `make run` | `reports/`, `export/` | ~20' (train +35') |
| 5 | Viết `REPORT.md`, kiểm, nộp | `make check-core` | `submission/REPORT.md` | ~45' |

## Bước 1 — Chuẩn bị (~30')

```bash
pip install -r requirements.txt
python -m pytest -q                              # 55 failed, 24 passed: bình thường, bạn chưa viết 4 module
python scripts/viz_labels.py img_0001 img_0030   # xem nhãn vẽ lên ảnh -> work/viz/
```
Đọc [data/README.md](data/README.md): lô raw gồm gì, tập test/val/calib để làm gì, **không** có đáp án lỗi của lô raw (bạn phải tự tìm bằng máy).
Mở ~10 ảnh `work/viz/*.png`, ghi lại 3 lỗi bạn tự nhìn thấy (dùng cho `REPORT.md` mục 4).
5 check đã **viết sẵn** (`missing_labels`, `class_names`, `images`, `stats`, `duplicates`: Script 1, 3, 4, 5 của slide): đọc chúng làm mẫu trước khi viết. Đọc kỹ `duplicates.py`: bạn sẽ calibrate `phash_dist` của nó ở Bước 3.

## Bước 2 — Viết 4 module (~2 giờ 15', TDD)

Mỗi file là một **stub** có docstring mô tả chính xác đầu vào/đầu ra. Làm theo thứ tự dễ → khó (bảng dưới); vòng lặp: đọc docstring → viết → `pytest tests/test_<tên>.py -q` → sửa → commit.

| # | File | Test | Slide | Gợi ý |
|---|---|---|---|---|
| 1 | `pipeline/checks/label_format.py` | `tests/test_label_format.py` | Script 2 | ~30' |
| 2 | `pipeline/steps/gate.py` | `tests/test_gate.py` | Release / Hold / Rework | ~15' |
| 3 | `pipeline/steps/autofix.py` | `tests/test_autofix.py` | sửa lỗi bắt buộc, ghi log | ~35' |
| 4 | `pipeline/checks/second_opinion.py` | `tests/test_second_opinion.py` | máy cho ý kiến thứ hai | ~55' |

Test cũng là danh sách bẫy từ slide: đuôi `.JPG`, dòng thiếu cột, ảnh cắt cụt, ảnh thu nhỏ 90% mà md5 không bắt được…
`second_opinion` so nhãn với **yolo26l** (dự đoán đã lưu sẵn trong `data/cache/`, **không cần GPU**) và chỉ **cảnh báo**.
**Test xanh chưa chắc đúng**: test chỉ phủ ca điển hình. Với `label_format`, `autofix`, `second_opinion`, sau khi xanh hãy tự thử thêm 3 ca: một dòng dính 2 lỗi, file có dòng trống ở giữa, một ảnh có nhiều dự đoán (và để `make run` + `viz_labels.py` bắt các lỗi còn sót).
Khi `python -m pytest -q` xanh hết (79 test), thử ngay: `python -m pipeline.run` (có thể ra Hold: ngưỡng còn là giá trị khởi đầu).

> Dùng AI? OK, theo [docs/PROMPTING.md](docs/PROMPTING.md): mô tả đủ 4 ý, **đọc lướt có xoá/ghi đè file không**, chạy test. Ghi 3 dòng trong `REPORT.md` mục 6.

## Bước 3 — Calibrate 2 ngưỡng (~30')

`data/calib/` có 39 ảnh nhãn sạch **đã chèn lỗi cố ý**, `MANIFEST.csv` là đáp án. Đọc [docs/CALIBRATION.md](docs/CALIBRATION.md) (5'), rồi:
```bash
make calibrate     # 2 sweep: duplicates.phash_dist và second_opinion.conf -> submission/calibration/ (Windows: copy lệnh một dòng trong Makefile)
```
Chọn giá trị cho **2 tham số** `# <-- CALIBRATE` trong `configs/pipeline.yaml` (các ngưỡng khác đã cố định). Điền `REPORT.md` mục 3: bảng trước/sau, vì sao chọn (đánh đổi precision–recall) và **một chỗ calibration có thể đánh lừa bạn**.
> Gợi ý: calib chỉ có 39 ảnh. Sau khi chọn, chạy pipeline và **mở xem** các cặp ảnh bị cho là trùng: số ảnh bị loại có hợp lý không?

*Thưởng +2 (tùy chọn): CVAT, lọc box nhỏ, xem [docs/CVAT_FILTER.md](docs/CVAT_FILTER.md).*

## Bước 4 — Chạy pipeline (~20'); train Colab là phần tùy chọn

```bash
make run          # = python -m pipeline.run. make trả 0 cho cả Release/Hold/Rework (kết luận in ở cuối + trong report); mã thoát thật: `python -m pipeline.run; echo $?` -> 0 Release, 10 Hold, 20 Rework
```
Pipeline ghi báo cáo vào `submission/reports/`:

| File | Nội dung |
|---|---|
| `01_intake.*` | ảnh bị loại ở cửa vào (hỏng, nhỏ, trùng, rò rỉ test) |
| `02_error_list_v1.*` | **danh sách lỗi TRƯỚC khi sửa** (đây là "báo cáo lỗi" của slide) |
| `03_fixes.csv` | mọi thay đổi do máy tự sửa (trước → sau) |
| `04_error_list_v2.*`, `05_review_queue.csv`, `06_review_log.csv` | lỗi sau sửa · hàng đợi **người duyệt** · ảnh đã duyệt (mô phỏng, ngân sách 80 ảnh) |
| `07_error_list_v3.*` | lỗi sau người duyệt + **kết luận** |
| `08_summary.json`, `class_stats.csv` | tóm tắt, đếm box theo lớp |

Đọc báo cáo (kết luận trước, chi tiết sau — như slide). **Ảnh chưa có file nhãn** (`MISSING_LABEL_FILE`): máy không bịa nhãn; ảnh đó vào hàng đợi người, nếu người không gán thì kết luận là Rework.
Ngân sách duyệt 80 ảnh là đánh đổi có chủ đích (slide: "mọi nhãn nháp đều phải qua mắt người"): ảnh chưa duyệt vẫn tính vào tỉ lệ cảnh báo của cổng (≥ 10% là Hold).

**Train (tùy chọn, chấm riêng 15 điểm; làm khi đã xong Bước 5 hoặc ở buổi khác)** (sau khi `make run` xong; Rework thì xuất bản nháp bằng `python -m pipeline.run --export-on-rework` và ghi rõ trong báo cáo):
1. `git add submission/export submission/reports && git commit && git push` (repo **public**).
2. Mở [notebooks/day09_train_compare.ipynb](notebooks/day09_train_compare.ipynb) trên Colab ([docs/COLAB.md](docs/COLAB.md)), runtime T4, điền `REPO_URL`, **Run all**: train `raw` và `clean` (yolo26n, 20 epoch, 2 seed) ~20 phút.
3. Tải `submission/results/` về, commit. Trong lúc chờ, viết `REPORT.md`. Nếu chưa train: ghi "chưa chạy" ở mục 5 của `REPORT.md`.

## Bước 5 — Báo cáo và nộp (~45')

Điền `submission/REPORT.md` (6 mục, 1–2 trang): kết luận, lỗi và phân việc, calibration, cửa chặn + điểm mù, kết quả train (nếu có), quyết định và ghi chú AI. Rồi:
```bash
python scripts/summarize_results.py    # (nếu đã train) comparison.md, dán vào REPORT.md mục 5
make check-core                         # kiểm phần lõi, bỏ qua train (python scripts/check_submission.py --no-train)
make check                              # kiểm đầy đủ, gồm train
```
Sửa hết `LỖI`, đổi dòng tiêu đề README, đối chiếu [SUBMISSION.md](SUBMISSION.md), nộp link repo.

## Lỗi hay gặp

| Triệu chứng | Cách xử lý |
|---|---|
| `NotImplementedError` ở e2e | còn module chưa viết: chạy `pytest -q` xem file nào đỏ |
| `pytest` xanh nhưng `make run` ra nhiều lỗi lạ | test chỉ phủ ca điển hình; mở `02_error_list_v1.txt` đọc vài dòng và so với `viz_labels.py` |
| `make run` báo 0 lỗi | check của bạn quá lỏng, hoặc chạy sai thư mục (slide: "luôn in số ảnh đã quét") |
| Số ảnh bị loại ở bước 1 quá nhiều | `phash_dist` quá lớn → ảnh khác nhau bị coi là trùng |
| Ra Hold dù đã calibrate | ≥ 10% ảnh còn cảnh báo chưa được người duyệt (hàng đợi lớn hơn ngân sách 80): ngưỡng cảnh báo lỏng quá → calibrate lại; nếu hợp lý thì ghi Hold + lý do |
| Colab báo thiếu `manifest.json` | bạn chưa commit/push `submission/export/clean_v1/` |
| `ModuleNotFoundError: imagehash` | `pip install -r requirements.txt` |

> **Vì sao cổng Hold ở 10% mà slide ví dụ 2%?** Slide nói rõ "ngưỡng 2% là ví dụ, dự án đặt trong guideline". Ở lab này `warn_ratio_hold = 0.10` (`configs/pipeline.yaml`, đã ghim, không đổi được) vì hàng đợi duyệt chỉ có 80 ảnh trên ~200 ảnh. Với 2% gần như mọi lô đều Hold. Trong dự án thật, ngưỡng do guideline quyết định.
