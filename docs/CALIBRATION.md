# Calibration: đo chính công cụ kiểm

Slide Day 09: *"Script bắt đủ lỗi đã chèn thì mới đáng tin trên dữ liệu thật."* Kiểm tra công cụ trước khi tin báo cáo của nó.

## Bộ `data/calib/`
- 30 ảnh nhãn **người** (sạch) + 9 ảnh trùng thêm vào (3 trùng byte, 6 gần trùng, mức biến đổi tăng dần).
- Đã **chèn lỗi cố ý** ở vị trí biết trước; `data/calib/MANIFEST.csv` ghi `type, image, line, detail`.
- Khác bộ `raw`: raw **không có đáp án** (đúng như dữ liệu thật).

## Cách chấm (`pipeline/calibrate.py`)
| Khái niệm | Nghĩa |
|---|---|
| TP | cờ đúng chỗ có lỗi chèn |
| FP | cờ chỗ **không** có lỗi chèn loại đó (báo động giả: người kiểm phải mở xem uổng công) |
| FN | lỗi chèn mà không cờ (**bỏ sót**: lỗi lọt vào dataset) |
| precision = TP/(TP+FP) | cờ có đáng tin không |
| recall = TP/(TP+FN) | bắt được bao nhiêu lỗi |

Lỗi cú pháp so theo (ảnh, **dòng**); lỗi khác so theo ảnh. Ảnh sạch cũng có thể có lệch tự nhiên giữa model và nhãn người — vẫn tính FP,
vì đó đúng là báo động giả bạn sẽ gặp.

## Đọc bảng sweep
```
second_opinion.conf=0.25  WRONG_CLASS 0.56 / 0.83 / 0.67  MISSING 0.50 / 1.00 / 0.67 …
second_opinion.conf=0.80  WRONG_CLASS 1.00 / 0.83 / 0.91  MISSING 0.67 / 0.75 / 0.71 …
```
Mỗi ô là `precision / recall / F1`. Tăng `conf`: ít cờ hơn, chắc hơn (precision ↑) nhưng bỏ sót nhiều hơn (recall ↓).

## Chọn ngưỡng thế nào
- **Lỗi bắt buộc tự sửa/loại** (`phash_dist`): ưu tiên **precision cao** — cờ sai nghĩa là xoá nhầm ảnh/box tốt.
- **Cảnh báo cho người** (`second_opinion.conf`): chấp nhận precision thấp hơn để recall cao, nhưng **hàng đợi lớn hơn ngân sách duyệt (80 ảnh) thì phần dư không ai xem**:
  nếu ≥ 10% ảnh còn cảnh báo chưa duyệt, gate sẽ Hold. Nhưng đừng hạ recall chỉ để hàng đợi "vừa": một hàng đợi nhỏ vì checker mù là Release giả.
- Đừng chỉ chọn "F1 lớn nhất": hỏi *giá của một FP* và *giá của một FN* trong dự án này.

## Hạn chế cần nhớ
1. Calib chỉ 39 ảnh: ô nào chỉ có 2–5 lỗi chèn thì precision/recall nhảy từng bước 20–50%.
2. Lỗi chèn là **lỗi dễ hình dung**. Lỗi thật hiếm khi sạch sẽ như vậy.
3. Ngưỡng tối ưu cho calib chưa chắc tối ưu cho raw. **Luôn mở xem** vài kết quả trên raw (`viz_labels.py`), đặc biệt các cặp ảnh bị cho là trùng.
4. Lỗi chèn trong calib **không giống hệt** lỗi tự nhiên trong raw: calib dựng từ nhãn người (sạch), raw từ nhãn model; các lỗi `WRONG_CLASS` trong calib chủ yếu là person→car, còn raw nghiêng về car/truck/bus; calib **không có** ca `LEAK_TEST`. Đừng tin recall trên calib như recall trên raw.
5. Có lỗi mà không ngưỡng nào bắt được (vd. ảnh bị cắt 80% rồi thu nhỏ): ghi vào báo cáo như một **điểm mù đã biết**.
