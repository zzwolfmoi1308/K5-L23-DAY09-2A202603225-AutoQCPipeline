# Nhờ AI viết script: mô tả đủ 4 ý (slide Day 09)

```
Viết script Python 3 kiểm thư mục labels/ (YOLO txt).                  # (1) định dạng vào
Mỗi dòng: id x_tam y_tam rong cao, tỉ lệ 0-1. Ví dụ: 1 0.50 0.50 0.20 0.30
In "tên file, số dòng, lý do" cho dòng có box tràn ảnh.               # (2) quy tắc kiểm + (3) kiểu in ra
Chỉ đọc file, không sửa, không xóa. Dưới 12 dòng.                      # (4) giới hạn an toàn
Giải thích từng dòng bằng tiếng Việt.
```

| Mơ hồ | Rõ ràng |
|---|---|
| Viết code kiểm nhãn | Kiểm box tràn ảnh trong `labels/` |
| Sửa lỗi giúp | Chỉ in lỗi, không sửa file |
| (không nêu định dạng) | Nêu 5 cột của dòng YOLO + 1 dòng mẫu |

**Trong lab này**, mỗi `checks/*.py` đã có docstring mô tả vào/ra. Hãy **dán docstring + 1 test** vào prompt thay vì mô tả lại bằng lời.
Chỉ dán vài dòng nhãn mẫu: **không dán ảnh** (Day 06: mặt người, biển số).

## Kiểm code do AI viết (3 việc, ghi 3 dòng vào `REPORT.md` mục 6)
1. **Đọc lướt:** có xoá/ghi đè file không? có `except: pass` nuốt lỗi không? có viết cứng ngưỡng không?
2. **Chạy test** và chạy trên **bản sao**, thử trên các ca đã biết có lỗi (tập calib).
3. **Gặp lỗi đỏ:** dán 5 dòng cuối của traceback cho AI. Dòng cuối thường nói rõ: `FileNotFoundError` (sai thư mục), `ValueError`/`IndexError` (dòng nhãn thiếu cột).

Mẫu ghi nhật ký: *Prompt → AI trả gì → tôi kiểm bằng cách nào → chỗ AI sai/thiếu và tôi sửa thế nào.*
