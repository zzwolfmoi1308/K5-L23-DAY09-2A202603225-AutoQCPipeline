# Quy tắc làm bài

## Hình thức
**Bài cá nhân.** Mỗi người một repo (fork/template từ repo đề). Commit dưới tên của bạn.

## Sản phẩm là của bạn
- 4 module `pipeline/checks/{label_format,second_opinion}.py`, `pipeline/steps/autofix.py`, `pipeline/steps/gate.py` do **bạn** viết (5 check còn lại, gồm `duplicates`, đã viết sẵn). Không sao chép bài người khác.
- Được dùng AI để viết script **nếu** bạn (1) mô tả đủ 4 ý như slide ([docs/PROMPTING.md](docs/PROMPTING.md)), (2) đọc và hiểu từng dòng,
  (3) kiểm bằng unit test **và** bằng lỗi chèn sẵn. Ghi 3 dòng (prompt chính, cách bạn kiểm, 1 lần AI sai) trong `submission/REPORT.md` mục 6.
  Bạn phải giải thích được mọi dòng trong file mình nộp.
- **Không** dùng `_instructor/` hay tìm đáp án lỗi cố ý của lô raw; `data/calib/MANIFEST.csv` là đáp án **được phép** dùng (đó là bộ calibration).

## Tính trung thực của số liệu
- Không sửa tay các file do script sinh ra trong `submission/reports/`, `submission/calibration/*`, `submission/results/*.json|comparison.*`.
- **Không đổi** `gate.warn_ratio_hold`, `review.budget_images`, `review.weights`, `classes`, và không sửa `scripts/human_review_sim.py` để "đạt" Release.
  Bạn **chỉ** được chỉnh đúng 2 ngưỡng đánh dấu `# <-- CALIBRATE`; mọi mục khác của `configs/pipeline.yaml` là quy tắc dự án cố định (`make check` so sánh cả file).
  Không sửa `tests/`, `data/` và các file "ĐÃ VIẾT SẴN" (`make check` so sha1 các file đã viết sẵn, `tests/`, cache và MANIFEST; ảnh/nhãn trong `data/` giảng viên đối chiếu khi chấm). Giảng viên chấm bằng bản `check_submission.py` của mình và đọc code của bạn, không chỉ tin vào bản trong repo.
- **Không** đọc `data/review_reference/`, `data/test/labels`, `data/calib/MANIFEST.csv` từ trong code kiểm (`checks/`, `autofix`, `gate`) và không cố định danh sách ảnh/dòng lỗi trong code. `check_submission.py` quét tĩnh và giảng viên chấm lại trên bộ dữ liệu khác tên ảnh.
- **Không** dùng ảnh/nhãn trong `data/test/` để huấn luyện, chọn ngưỡng, hay sửa nhãn. Tập test chỉ để đo ở bước cuối.
- Báo **Hold** hoặc **Rework** trung thực vẫn được điểm tốt. Điều bị trừ điểm là báo Release khi số liệu không đạt, hoặc kết luận
  "clean tốt hơn raw" khi số liệu không ủng hộ (hoặc khác biệt nằm trong độ nhiễu giữa các seed).
- Không bịa kết quả train. File `submission/results/*.json` phải sinh từ `scripts/train_compare.py`.

## Dữ liệu và giấy phép
- Ảnh lấy từ COCO val2017 (annotations CC BY 4.0; ảnh chỉ chọn giấy phép cho phép tác phẩm phái sinh: CC BY, CC BY-SA, no known copyright, US Gov).
  Giữ nguyên `data/ATTRIBUTION.csv`. Không đưa dữ liệu riêng tư vào repo. Không sửa/thêm/bớt ảnh trong `data/`.
- Không commit `work/`, `.venv/`, file trọng số `*.pt`, token, API key.

## Git
- Commit nhỏ, thông điệp rõ (mỗi check một commit là tốt). Nộp theo commit cuối trước hạn.
