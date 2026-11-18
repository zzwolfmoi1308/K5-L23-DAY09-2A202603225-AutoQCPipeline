# Rubric — 100 điểm

Điểm dựa trên **bằng chứng trong repo**, không dựa vào việc được Release hay mAP cao. Báo **Hold/Rework** trung thực, có phân tích, vẫn được điểm tốt.

| # | Hạng mục | Điểm | Bằng chứng |
|---|---|---:|---|
| 1 | 4 module đúng (unit test) | 40 | `pipeline/`, `pytest` |
| 2 | Pipeline tự động hoá một lệnh | 15 | `make run`, `submission/reports/`, test e2e |
| 3 | Calibration (2 ngưỡng) | 10 | `submission/calibration/`, `REPORT.md` §3 |
| 4 | Báo cáo lỗi, phân việc, quyết định | 15 | `submission/REPORT.md` §1, 2, 4, 6 |
| 5 | Train so sánh raw vs clean (**tùy chọn, chấm riêng**) | 15 | `submission/results/`, `REPORT.md` §5 |
| 6 | Tái lập và git | 5 | `check_submission.py`, commit |

## 1. 4 module đúng (40)
Chấm tự động bằng `pytest` (trên máy chấm, có thêm vài ca ẩn cùng kiểu). Trọng số: `second_opinion` 13 · `autofix` 11 · `label_format` 10 · `gate` 6. Năm check viết sẵn (gồm `duplicates`) không chấm.
- Trừ: đọc ngưỡng viết cứng trong code thay vì `cfg`; check làm script chết với dòng hỏng; xoá/ghi đè `data/raw`.

## 2. Pipeline tự động hoá (15)
- 5: `make run` chạy từ đầu đến cuối **không cần can thiệp**, mã thoát đúng (0/10/20), ra đủ 8 file báo cáo.
- 4: **Tái lập**: chạy 2 lần cho cùng kết quả (test e2e); không phụ thuộc thứ tự file / thời gian.
- 3: **Cửa chặn thật sự chặn**: lỗi bắt buộc còn lại → Rework, **không xuất** dataset; bạn chứng minh bằng ví dụ (`REPORT.md` §4).
- 3: Mỗi thay đổi tự động có dấu vết (`03_fixes.csv` trước → sau); không sửa `data/raw`.

## 3. Calibration (10)
- 3: chạy 2 sweep, có `calibration_report.md` do script sinh.
- 4: bảng **trước / sau** và **lý do** chọn từng giá trị bằng precision/recall (không chỉ "F1 cao nhất").
- 3: nêu **một điểm đánh lừa** của calibration (calib nhỏ, phân bố khác, ngưỡng ăn khớp calib nhưng sai trên raw…) có bằng chứng từ dữ liệu của bạn.

## 4. Báo cáo lỗi, phân việc, quyết định (15)
- 3: số lỗi theo từng mã (kèm mẫu số), "kết luận trước, chi tiết sau".
- 5: **phân việc sửa**: lỗi nào máy sửa, lỗi nào người, ảnh nào ưu tiên; giải thích hàng đợi.
- 5: quyết định Release/Hold/Rework **khớp số liệu**, có điều kiện để đổi quyết định; thừa nhận ≥ 2 điểm pipeline **không** bắt được.
- 2: ghi chú dùng AI (prompt, cách kiểm, 1 lần AI sai) hoặc "không dùng".
- Bị trừ nặng: báo Release trong khi `07_error_list_v3` còn lỗi bắt buộc hoặc cảnh báo ≥ ngưỡng.

## 5. Train so sánh (15, tùy chọn, chấm riêng)
Không làm: tối đa 85/100. Báo "chưa chạy" trung thực ở `REPORT.md` §5, `make check-core` vẫn qua.
- 4: đúng quy trình công bằng: cùng val/test/siêu tham số/seed; ≥ 2 seed mỗi biến thể.
- 4: `comparison.md` do script sinh, đủ mAP50, mAP50-95, precision, recall (TB ± độ lệch).
- 4: `REPORT.md` §5 so sánh chênh lệch với độ nhiễu giữa seed; ≥ 2 nguyên nhân có thể (ảnh trùng/rò rỉ test, box lỏng, thiếu nhãn, lớp ít ảnh…) và cách kiểm.
- 3: kết luận **trung thực** (không nói "tốt hơn" nếu khác biệt nằm trong nhiễu) + việc tiếp theo.

## 6. Tái lập và git (5)
- 2: `make check` hết LỖI; repo chạy từ `git clone` + `pip install -r requirements.txt`.
- 3: ≥ 5 commit có thông điệp rõ, mang tên bạn; không commit `work/`, `*.pt`.

## Cách chấm trên máy giảng viên
- Ghi đè mọi file "ĐÃ VIẾT SẴN" bằng bản gốc (so `scripts/_protected.json`), giữ 4 module của học viên và `configs/pipeline.yaml`; chạy `pytest` (có thêm ca ẩn), `make run`, và `check_submission.py`.
- Chấm lại trên lô khác (đổi tên ảnh, xáo trộn vị trí lỗi) để phát hiện code cứng đáp án.
- Số trong báo cáo được đối chiếu với `08_summary.json`, `calibration.json`, `results/*.json` (có `manifest_sha1`, `config_sha1`).

## Thưởng (tối đa +5, không vượt 100)
- +3: thêm một check mới (box tiny/dense, lệch tỉ lệ khung hình, class imbalance) có test.
- +2: CVAT ([docs/CVAT_FILTER.md](docs/CVAT_FILTER.md)): lọc box nhỏ trên ≥ 1 ảnh (≥ 5 ảnh nếu làm kỹ), đối chiếu `BOX_TINY`, 1 câu về `can_review`, kèm ảnh chụp.
