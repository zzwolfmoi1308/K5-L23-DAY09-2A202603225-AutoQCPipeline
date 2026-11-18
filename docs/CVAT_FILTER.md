# CVAT: lọc box bất thường (TÙY CHỌN, thưởng +2, ~20 phút)

Pipeline tìm lỗi trên **toàn bộ** dữ liệu; CVAT dùng để **xem và sửa tay** vài ca. Slide Day 09, mục "Dùng công cụ kiểm có sẵn".

1. Tạo project CVAT: *Projects → + → Raw* dán nội dung [cvat/labels.json](../cvat/labels.json) (nhãn `car, person, truck, bus` đúng thứ tự, có thuộc tính `can_review`), tạo task từ ~20 ảnh trong `work/run/ds/images/`
   (lấy từ đầu `05_review_queue.csv`), import nhãn dạng *YOLO 1.1* (zip gồm `obj.names`, `obj.data`, `train.txt`, `obj_train_data/*.txt`).
2. Mở **Filters** của job → *Add rule*:
   - box nhỏ: `width < 20` (hoặc `height < 20`);
   - theo lớp: `label=="truck"`;
   - ca khó: `attr["can_review"]==true`.
3. Duyệt bằng `→` / `←` (nhảy tới/lui ảnh khớp bộ lọc), `Tab` (chuyển object), `Del` (xoá 1 box).
4. **Trước khi xoá hàng loạt** (`Ctrl+E` → *Remove filtered shapes*): đếm box khớp, `Ctrl+S`, chắc chắn bộ lọc hiển thị đúng tập cần xoá.
5. Export YOLO 1.1, so sánh với nhãn pipeline: CVAT sửa gì mà pipeline chưa thấy?

**Thưởng +2:** làm bước 1–2 với ≥ 1 ảnh, lọc `width < 20`, và ghi vào `REPORT.md` mục 6(b): tên ảnh khớp, số box khớp, đối chiếu với các dòng `BOX_TINY` của pipeline (cùng ảnh không? ngưỡng 12 px của pipeline vs 20 của slide), và 1 câu về `can_review` (người gán dùng thuộc tính này khi nào, pipeline dùng thông tin tương tự ở đâu?).
Muốn làm kỹ hơn: duyệt ≥ 5 ảnh, kèm ảnh chụp bộ lọc và so sánh với pipeline (vẫn tính trong mức +2, tổng thưởng tối đa +5).
