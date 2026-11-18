# Báo cáo Day 09 — <Ngô Xuân Tùng>, <2A202603225>

> Xoá mọi `TODO(học viên)` và dòng gợi ý. Mỗi ý trả lời bằng **số lấy từ `submission/reports/`**, kèm mẫu số. Cả báo cáo ~1–2 trang.

## 1. Kết luận trước
TODO(học viên): pipeline kết luận **Release / Hold / Rework**? Bao nhiêu ảnh vào, bao nhiêu ảnh ra dataset? Lý do chính (1–3 câu).

## 2. Lỗi và phân việc
Lấy từ `02_error_list_v1` (gom theo mã lỗi). Cột "ai sửa": **máy** (autofix) hay **người** (hàng đợi); chỉ ghi những mã có mặt trong lô của bạn.

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| TODO(học viên) | | | |

TODO(học viên): vì sao `05_review_queue.csv` xếp ảnh đầu hàng như vậy? Với ngân sách 80 ảnh, người xem được bao nhiêu lỗi ngữ nghĩa?

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | 8 | P: 1.00 → 1.00<br>R: 0.50 → 0.67 | Ngưỡng 2 quá chặt (bỏ sót 50% ảnh gần trùng). Chọn 8 tăng recall lên 0.67 mà vẫn giữ precision 1.00; tránh bẫy của ngưỡng 16 trên tập raw gây xóa nhầm ảnh thật. |
| `second_opinion.conf` | 0.25 | 0.60 | Missing: P: 0.50 → 0.57, R: 1.00 → 1.00<br>Wrong class: P: 0.56 → 0.62, R: 0.83 → 0.83 | Ngưỡng 0.25 tạo quá nhiều báo động giả (P=0.50) khiến hàng đợi phình to 106 ảnh (vượt ngân sách 80). Chọn 0.60 tăng precision lên 62% cho wrong class và 57% cho missing, giảm số ảnh cảnh báo xuống 65 ảnh (vừa ngân sách duyệt 80 ảnh) mà vẫn giữ nguyên 100% recall cho lỗi thiếu nhãn, trước khi recall sụt giảm ở ngưỡng >= 0.70. |

**Một chỗ calibration có thể đánh lừa:**
Tập calib chỉ có 39 ảnh với 6 cặp ảnh gần trùng mẫu. Nếu chỉ tối ưu mù quáng theo "F1 lớn nhất" trên calib, ta sẽ dễ chọn `phash_dist = 16` (F1 đạt 0.91). Tuy nhiên, khi thử nghiệm thực tế trên tập raw 224 ảnh:
- Với `phash_dist = 8`: Phát hiện ổn định 16 ảnh (8 trùng byte, 3 gần trùng, 5 rò rỉ test).
- Với `phash_dist = 16`: Số ảnh bị cờ rò rỉ test (`LEAK_TEST`) nhảy vọt từ 5 lên 11 ảnh và gần trùng (`DUP_IMAGE_NEAR`) tăng lên 7 ảnh. Rất nhiều ảnh có bối cảnh tương tự bị nhận nhầm là trùng lặp và bị hệ thống tự động xóa oan (`remove_image`). Do đó, không thể chỉ nhìn vào F1 của tập calib nhỏ mà phải đối chiếu trực tiếp với dữ liệu raw.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
TODO(học viên): (a) chứng minh gate chặn đúng: chạy `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` (không có người duyệt nên ảnh thiếu file nhãn còn nguyên), chỉ ra kết luận **Rework**, mã thoát 20 và việc **không xuất** dataset. (Đừng sửa tay `work/run/ds`: pipeline dựng lại thư mục này từ raw mỗi lần chạy.)

**(b) Các lỗi và điểm mù quan sát thấy bằng mắt thường (từ `work/viz/`):**
1. **`img_0001.png` (Bỏ sót đối tượng - Missing box):** Người chiến sĩ mặc áo rằn ri đứng ở giữa/bên phải hoàn toàn không có bounding box nào, trong khi người mặc vest và người ngồi góc dưới đều có nhãn.
2. **`img_0004.png` (Thiếu nhãn hoàn toàn - Missing label file):** Bức ảnh chụp nhà ga có 2 xe ô tô đỗ rất rõ ở góc dưới bên phải (chiếc màu bạc và chiếc màu đen), nhưng cả bức ảnh không có bất kỳ bounding box nào.
3. **`img_0005.png` (Gán nhầm lớp - False positive / Wrong class):** Một thùng rác / trụ kim loại màu xanh lam ở vỉa hè phía xa bên trái (sau đuôi xe buýt) bị gán nhãn nhầm thành `person`.
4. **`img_0007.png` (Thiếu nhất quán trong cùng ảnh):** Bãi đỗ xe phía sau máy bay có một hàng dài ô tô, nhưng chỉ một vài chiếc được gán nhãn `car`, các xe khác đỗ ngay cạnh (như chiếc ô tô màu trắng) bị bỏ sót hoàn toàn.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Chưa train: ghi "chưa chạy" và lý do, rồi bỏ qua phần còn lại của mục này. Nếu đã train: dán bảng từ `submission/results/comparison.md` (model, epoch, seed, số ảnh train mỗi biến thể).

TODO(học viên): chênh mAP50 (clean − raw) so với **độ lệch chuẩn giữa các seed**; kết luận **trung thực** (nằm trong nhiễu thì nói là chưa kết luận được); ≥ 2 giả thuyết giải thích (ảnh trùng/rò rỉ test trong `raw`, nhãn máy còn lại trong `clean`, test chỉ 100 ảnh…) và cách kiểm.

## 6. Quyết định và ghi chú AI
TODO(học viên): (a) quyết định cuối; nếu Hold/Rework cần làm gì để thành Release? (b) Dùng AI viết code? Ghi 3 dòng: prompt chính, cách bạn kiểm code AI, 1 lần AI sai. Không dùng: ghi "không dùng".

*(Thưởng +2, tùy chọn)* CVAT: lọc `width < 20`, ảnh/số box khớp, đối chiếu `BOX_TINY` (xem docs/CVAT_FILTER.md), 1 câu về `can_review`.
