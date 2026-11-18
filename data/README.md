# Dữ liệu

Nguồn: **COCO val2017** (annotations CC BY 4.0). Ảnh chỉ lấy các giấy phép Flickr cho phép tác phẩm phái sinh
(CC BY 2.0, CC BY-SA 2.0, no known copyright restrictions, US Government Work). Chi tiết: [ATTRIBUTION.csv](ATTRIBUTION.csv).
Bốn lớp của dự án, **đúng thứ tự id**: `0 car · 1 person · 2 truck · 3 bus`.

| Thư mục | Ảnh | Nhãn | Dùng để |
|---|---:|---|---|
| `raw/` | 224 | **nhãn gán sẵn + lỗi** (không có đáp án) | đầu vào của pipeline |
| `calib/` | 39 | nhãn người + **lỗi chèn có đáp án** (`MANIFEST.csv`) | calibration (đo công cụ kiểm) |
| `gold_val/` | 40 | nhãn người (sạch) | `val` khi train (chọn checkpoint) |
| `test/` | 100 | nhãn người (sạch) | **chỉ** để đánh giá cuối. Không dùng để sửa nhãn/chọn ngưỡng |
| `review_reference/labels/` | — | nhãn người cho ảnh của `raw` | **chỉ** `scripts/human_review_sim.py` đọc (mô phỏng người duyệt) |
| `cache/` | — | dự đoán model đã lưu | `checker_preds.json` (yolo26l — ý kiến thứ hai cho check `second_opinion`) |

## Lô `raw` có gì?
Nhãn do máy gán rồi qua một vòng sửa cẩu thả nên lẫn lỗi. Có **lỗi tự nhiên** (bỏ sót vật nhỏ, nhầm xe tải/xe con…)
và **lỗi cố ý** thuộc các nhóm dưới đây. Số lượng chính xác **không công bố** — nhiệm vụ của pipeline là tìm ra.

| Nhóm | Dấu hiệu |
|---|---|
| Ảnh | hỏng/cắt cụt, quá nhỏ, trùng byte, trùng gần đúng (thu nhỏ, cắt, đổi sáng), **trùng ảnh test** |
| File | thiếu file nhãn; đuôi `.JPG`/`.png` (bẫy đuôi hoa/thường) |
| Dòng nhãn | thiếu cột / `nan`, ID lớp sai (93, 4, −1), box tràn ảnh, box rộng/cao 0, box lặp |
| `data.yaml` | tên lớp viết hoa sai |
| Ngữ nghĩa | gán nhầm lớp hợp lệ (car↔truck↔bus), xoá mất box, box phình to, box thừa |

Lỗi cú pháp máy bắt gần như chắc chắn; lỗi ngữ nghĩa chỉ **nghi ngờ** được bằng ý kiến thứ hai của model — rồi cần người xem.

## Bẫy giấy phép / đạo đức
Ảnh người trong COCO là ảnh công khai trên Flickr; vẫn **không** dán ảnh lên dịch vụ AI bên ngoài (Day 06). Không đưa thêm dữ liệu riêng tư vào repo.
