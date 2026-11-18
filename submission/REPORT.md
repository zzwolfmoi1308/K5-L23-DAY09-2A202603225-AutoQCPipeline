# Báo cáo Day 09 — Ngô Xuân Tùng, 2A202603225

## 1. Kết luận trước
Pipeline đưa ra quyết định: **HOLD** (mã thoát hệ thống: `10`).
- **Số lượng ảnh vào:** 224 ảnh thô (`data/raw/images`).
- **Số lượng ảnh nhận qua cửa vào:** 203 ảnh (loại bỏ 21 ảnh gồm: 2 ảnh hỏng, 3 ảnh kích thước quá nhỏ, 11 ảnh trùng lặp exact/near, và 5 ảnh rò rỉ từ tập test).
- **Số lượng ảnh xuất dataset:** 203 ảnh (xuất bản nháp tại `submission/export/clean_v1/` để phục vụ thử nghiệm đánh giá; chưa được phát hành chính thức do ở trạng thái Hold).
- **Lý do chính:** Toàn bộ 100% lỗi bắt buộc (`ERROR`) đã được giải quyết sạch (35 lỗi cú pháp do máy tự sửa và 6 ảnh thiếu nhãn được người gán nhãn bù). Tuy nhiên, sau khi người duyệt xử lý hết ngân sách 80 ảnh, vẫn còn **38 / 203** ảnh chứa cảnh báo nghi ngờ lỗi ngữ nghĩa chưa được thẩm định (tỉ lệ **18.72%**, vượt ngưỡng trần cho phép **10.00%**). Do đó, cửa chặn tự động giữ lại (Hold) lô dữ liệu để tránh phát hành dữ liệu có rủi ro.

---

## 2. Lỗi và phân việc

Bảng tổng hợp từ `02_error_list_v1.csv` (danh sách lỗi trước khi sửa):

| Mã lỗi | Số lượng (ảnh/dòng) | Ai sửa | Vì sao |
|---|---:|---|---|
| `CORRUPT_IMAGE` | 2 ảnh | Máy (Intake) | Ảnh lỗi định dạng/cắt cụt, không đọc được dữ liệu pixel; máy tự động loại bỏ ở cửa vào. |
| `BAD_SIZE` | 3 ảnh | Máy (Intake) | Ảnh có cạnh nhỏ hơn 250px theo quy định dự án; máy tự động loại bỏ. |
| `DUP_IMAGE_EXACT` | 8 ảnh | Máy (Intake) | Ảnh trùng từng byte (trùng MD5); máy tự động loại bỏ bản sao. |
| `DUP_IMAGE_NEAR` | 3 ảnh | Máy (Intake) | Ảnh biến đổi gần trùng (pHash distance $\le$ 8); máy tự động loại bỏ bản sao. |
| `LEAK_TEST` | 5 ảnh | Máy (Intake) | Ảnh trùng hoặc gần trùng với tập test/gold_val; máy loại bỏ để chống rò rỉ dữ liệu. |
| `BAD_FORMAT` | 3 dòng | Máy (Autofix) | Dòng nhãn thiếu cột toạ độ hoặc chứa ký tự không phải số; máy tự động xóa dòng hỏng. |
| `BOX_ZERO` | 4 dòng | Máy (Autofix) | Bounding box có chiều rộng hoặc chiều cao bằng 0; máy tự động xóa dòng rỗng. |
| `BOX_OUT_OF_IMAGE` | 8 dòng | Máy (Autofix) | Box bị tràn ra ngoài viền ảnh ($> 0.002$); máy tự động cắt (clip) toạ độ về khoảng $[0, 1]$. |
| `DUP_BOX` | 7 dòng | Máy (Autofix) | Bounding box bị lặp lại trong cùng file nhãn; máy tự động xóa dòng trùng lặp. |
| `BAD_CLASS_NAME` | 2 dòng | Máy (Autofix) | Tên lớp ở dạng chuỗi văn bản thay vì số nguyên; máy tự động ánh xạ về ID chuẩn. |
| `BAD_CLASS_ID` | 6 dòng | Máy (Autofix) | ID lớp ngoài danh mục (hoặc ID lạ); máy map lại nếu có quy tắc hoặc xóa bỏ. |
| `MISSING_LABEL_FILE`| 6 ảnh | Người (Ưu tiên 1) | Ảnh hoàn toàn không có file nhãn đi kèm; máy không thể tự bịa nhãn mà bắt buộc phải đưa lên đầu hàng đợi để con người gán nhãn bù. |
| `POSSIBLE_MISSING` | 53 cảnh báo | Người (Hàng đợi) | Model checker phát hiện vật thể rõ ràng ($conf \ge 0.60$) nhưng nhãn bỏ sót; cần mắt người xác minh. |
| `POSSIBLE_FALSE_POS`| 29 cảnh báo | Người (Hàng đợi) | Box nhãn không khớp với bất kỳ dự đoán nào của model checker; cần người kiểm tra xem có gán nhầm vật thể lạ hay không. |
| `POSSIBLE_LOOSE_BOX`| 28 cảnh báo | Người (Hàng đợi) | Box nhãn bị lệch hoặc vẽ quá rộng so với vật thể ($IoU < 0.5$); cần người nắn lại viền. |
| `POSSIBLE_WRONG_CLASS`| 18 cảnh báo | Người (Hàng đợi) | Box trùng toạ độ cao nhưng lệch tên lớp; cần người phân định ngữ nghĩa thực tế. |
| `EMPTY_LABEL` | 12 ảnh | Người (Hàng đợi) | File nhãn trống hoàn toàn (ảnh âm tính hoặc bị quên gán); cần người xác nhận. |
| `BOX_TINY` / `BOX_HUGE`| 9 box | Người (Hàng đợi) | Box quá nhỏ ($< 20px$) hoặc quá lớn ($> 90\%$ diện tích); cần người xác thực ngữ cảnh. |
| `CLASS_RARE` | 4 cảnh báo | Người (Hàng đợi) | Ảnh chứa các lớp thiểu số cần lưu ý thống kê. |

**Giải thích cơ chế hàng đợi người duyệt (`05_review_queue.csv`):**
- **Vì sao xếp ảnh đầu hàng như vậy:** Hàng đợi được sắp xếp theo điểm ưu tiên giảm dần. Các ảnh bị lỗi `NEEDS_LABEL` (tức 6 ảnh thiếu file nhãn `MISSING_LABEL_FILE`) cùng các ảnh vừa có sửa đổi cú pháp vừa có nhiều cảnh báo nghiêm trọng (`img_0020`, priority 11.52) được đẩy lên đầu hàng đợi (priority $\ge 10.0$). Điều này đảm bảo người duyệt tập trung xử lý dứt điểm các lỗi bắt buộc trước tiên để tránh việc pipeline bị rơi vào trạng thái Rework.
- **Hiệu quả xử lý ngữ nghĩa với ngân sách 80 ảnh:** Trong tổng số 125 ảnh trong hàng đợi, người duyệt đã thẩm định và xử lý trọn vẹn 80 ảnh đầu bảng (giải quyết triệt để 6 ca thiếu file nhãn và thẩm định 74 ảnh có cảnh báo phức tạp nhất). Nhờ đó, số ảnh có cảnh báo nghi ngờ lỗi ngữ nghĩa đã giảm mạnh từ 102 ảnh xuống còn 38 ảnh.

---

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | 8 | P: 1.00 → 1.00<br>R: 0.50 → 0.67 | Ngưỡng 2 quá chặt (bỏ sót 50% ảnh gần trùng). Chọn 8 tăng recall lên 0.67 mà vẫn giữ precision 1.00; tránh bẫy của ngưỡng 16 trên tập raw gây xóa nhầm ảnh thật. |
| `second_opinion.conf` | 0.25 | 0.60 | Missing: P: 0.50 → 0.57, R: 1.00 → 1.00<br>Wrong class: P: 0.56 → 0.62, R: 0.83 → 0.83 | Ngưỡng 0.25 tạo quá nhiều báo động giả (P=0.50) khiến hàng đợi phình to 106 ảnh (vượt ngân sách 80). Chọn 0.60 tăng precision lên 62% cho wrong class và 57% cho missing, giảm số ảnh cảnh báo xuống 65 ảnh (vừa ngân sách duyệt 80 ảnh) mà vẫn giữ nguyên 100% recall cho lỗi thiếu nhãn, trước khi recall sụt giảm ở ngưỡng >= 0.70. |

**Một chỗ calibration có thể đánh lừa:**
Tập calib chỉ có 39 ảnh với 6 cặp ảnh gần trùng mẫu. Nếu chỉ tối ưu mù quáng theo "F1 lớn nhất" trên calib, ta sẽ dễ chọn `phash_dist = 16` (F1 đạt 0.91). Tuy nhiên, khi thử nghiệm thực tế trên tập raw 224 ảnh:
- Với `phash_dist = 8`: Phát hiện ổn định 16 ảnh (8 trùng byte, 3 gần trùng, 5 rò rỉ test).
- Với `phash_dist = 16`: Số ảnh bị cờ rò rỉ test (`LEAK_TEST`) nhảy vọt từ 5 lên 11 ảnh và gần trùng (`DUP_IMAGE_NEAR`) tăng lên 7 ảnh. Rất nhiều ảnh có bối cảnh tương tự bị nhận nhầm là trùng lặp và bị hệ thống tự động xóa oan (`remove_image`). Do đó, không thể chỉ nhìn vào F1 của tập calib nhỏ mà phải đối chiếu trực tiếp với dữ liệu raw.

---

## 4. Cửa chặn và điều pipeline KHÔNG bắt được

**(a) Chứng minh cửa chặn (Gate) hoạt động chính xác:**
- Khi chạy thử nghiệm mô phỏng không có ngân sách người duyệt:
  `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb`
- Kết quả thu được:
  * Do ngân sách bằng 0, không có nhân viên nào gán nhãn cho 6 ảnh thiếu file nhãn (`MISSING_LABEL_FILE`).
  * Cửa chặn Gate phát hiện còn 6 lỗi bắt buộc (`ERROR`) chưa được giải quyết và lập tức ra kết luận: **`REWORK — Còn 6 lỗi bắt buộc (ERROR) chưa được khắc phục.`**
  * Mã thoát trả về chính xác: **`$LASTEXITCODE = 20`**.
  * Cửa chặn đã **chặn đứng hoàn toàn việc xuất dữ liệu**: Thư mục `work/exp_nb` hoàn toàn không được tạo ra (`Test-Path work/exp_nb` trả về `False`).

**(b) Các lỗi và điểm mù quan sát thấy bằng mắt thường (từ `work/viz/`):**
1. **`img_0001.png` (Bỏ sót đối tượng - Missing box):** Người chiến sĩ mặc áo rằn ri đứng ở giữa/bên phải hoàn toàn không có bounding box nào, trong khi người mặc vest và người ngồi góc dưới đều có nhãn.
2. **`img_0004.png` (Thiếu nhãn hoàn toàn - Missing label file):** Bức ảnh chụp nhà ga có 2 xe ô tô đỗ rất rõ ở góc dưới bên phải (chiếc màu bạc và chiếc màu đen), nhưng cả bức ảnh không có bất kỳ bounding box nào.
3. **`img_0005.png` (Gán nhầm lớp - False positive / Wrong class):** Một thùng rác / trụ kim loại màu xanh lam ở vỉa hè phía xa bên trái (sau đuôi xe buýt) bị gán nhãn nhầm thành `person`.
4. **`img_0007.png` (Thiếu nhất quán trong cùng ảnh):** Bãi đỗ xe phía sau máy bay có một hàng dài ô tô, nhưng chỉ một vài chiếc được gán nhãn `car`, các xe khác đỗ ngay cạnh (như chiếc ô tô màu trắng) bị bỏ sót hoàn toàn.

---

## 5. Train: raw vs clean (Thực nghiệm so sánh trên Google Colab)

Bảng kết quả thực nghiệm huấn luyện mô hình YOLO (yolo26n, 20 epochs, 2 seeds) từ `submission/results/comparison.md`:

| biến thể | #ảnh train | số seed | map50 (TB ± độ lệch) | map50_95 (TB ± độ lệch) | precision (TB ± độ lệch) | recall (TB ± độ lệch) |
|---|---|---|---|---|---|---|
| raw | 224 | 2 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 203 | 2 | 0.699 ± 0.025 | 0.486 ± 0.013 | 0.796 ± 0.050 | 0.596 ± 0.049 |

Chênh mAP50 (clean − raw) = **-0.027**.

**Phân tích khoa học và kết luận trung thực:**
1. **So sánh chênh lệch với độ lệch chuẩn giữa các seed:**
   Mức chênh lệch mAP50 giữa `clean` và `raw` là `-0.027`. Tuy nhiên, độ biến thiên giữa các seed của `clean` lên tới `±0.025` (seed 0 đạt 0.6813, seed 1 đạt 0.7163; chênh lệch nội bộ giữa 2 seed là $0.035 > 0.027$). Do độ chênh lệch nằm hoàn toàn trong phạm vi nhiễu ngẫu nhiên của việc khởi tạo trọng số và xáo trộn dữ liệu (seed noise), **chưa thể kết luận mô hình clean kém hơn raw hay ngược lại khi chỉ đánh giá trên 2 seed**.
2. **Các nguyên nhân thực tế giải thích kết quả:**
   - *Rò rỉ dữ liệu kiểm thử trong tập `raw`:* Bước 1 của pipeline đã phát hiện 5 ảnh trong `raw` bị trùng/gần trùng với tập test 100 ảnh (`LEAK_TEST`). Khi huấn luyện trên `raw`, mô hình đã bị rò rỉ đề thi và học thuộc lòng các ảnh này, khiến mAP trên tập test bị thổi phồng giả tạo. Trong khi đó, `clean` đã loại bỏ hoàn toàn các ảnh rò rỉ, phản ánh năng lực khái quát hóa trung thực.
   - *Đánh đổi quy mô dữ liệu train:* Tập `clean` bị loại bỏ 21 ảnh kém chất lượng (chỉ còn 203 ảnh so với 224 ảnh). Với tập dữ liệu kích thước nhỏ (~200 ảnh), việc mất 10% lượng ảnh làm giảm số lượng mẫu của các lớp thiểu số như `truck` (AP50 của lớp truck giảm từ 0.648 xuống 0.536), kéo điểm recall chung xuống.
   - *Độ chính xác (Precision) của `clean` vượt trội:* Precision trung bình của `clean` đạt **0.796 ± 0.050**, cao hơn hẳn so với **0.764 ± 0.061** của `raw`. Điều này chứng minh dữ liệu sau khi làm sạch nhãn sai và loại bỏ box rác đã giúp mô hình học các biểu diễn chuẩn xác hơn, ít bị đoán bừa (false positives).
3. **Cách kiểm chứng mở rộng:** Cần tăng số lượng seed lên 5 để thu hẹp khoảng tin cậy thống kê, đồng thời bổ sung thêm ảnh mới cho lớp ít mẫu (`truck`) thay vì chỉ loại bỏ.

---

## 6. Quyết định và ghi chú AI

**(a) Quyết định cuối cùng và điều kiện để Release:**
- **Quyết định hiện tại:** Giữ nguyên quyết định **HOLD** (mã thoát `10`) theo đúng kết luận của cửa chặn Gate.
  * *Bản chất hệ thống:* Quyết định HOLD là một phản ứng chính xác và an toàn của hệ thống Auto QC. Toàn bộ 100% lỗi bắt buộc (`ERROR`) đã được khắc phục sạch sẽ, nhưng do ngân sách duyệt giới hạn ở 80 ảnh, phần dữ liệu nằm dưới "đường cắt" ngân sách vẫn còn 38 ảnh mang cảnh báo chưa được con người thẩm định. Với mẫu số sau intake là 203 ảnh, tỉ lệ cảnh báo tồn đọng là $38 / 203 = 18.72\% \ge 10.00\%$. Cổng chặn đã hoàn thành xuất sắc vai trò người gác cổng khi không cho phép phát hành một lô dữ liệu còn tiềm ẩn rủi ro vượt ngưỡng guideline. Kiên quyết không đẩy `conf > 0.85` để ép ra một "Release giả".
- **Điều kiện cụ thể để chuyển thành RELEASE trong thực tế:**
  1. *Tăng ngân sách người duyệt thêm tối thiểu 18 ảnh:* Với mẫu số 203 ảnh và ngưỡng trần $10.00\%$, số lượng ảnh cảnh báo tối đa được phép tồn đọng là $203 \times 10\% = 20.3 \approx 20$ ảnh. Hiện tại tử số đang là 38 ảnh (thừa đúng $38 - 20 = 18$ ảnh). Do đó, chỉ cần cấp thêm ngân sách cho con người duyệt thêm tối thiểu 18 ảnh (nâng ngân sách từ 80 lên ít nhất **98 ảnh** trong `05_review_queue.csv`), số ảnh cảnh báo chưa duyệt sẽ giảm xuống $\le 20$, tỉ lệ cảnh báo sẽ hạ xuống dưới $10.00\%$ và pipeline sẽ tự động chuyển thành **RELEASE** ngay lập tức.
  2. *Chuẩn hóa Guideline gán nhãn cho các cảnh báo cố định:* Nhiều cảnh báo trong danh sách v3 thuộc các mã có ngưỡng ghim cố định như `BOX_TINY` (vật thể $< 20px$), `EMPTY_LABEL` (ảnh âm tính không có vật thể). Trong dự án thực tế, chỉ cần cập nhật guideline: *"Chấp nhận ảnh âm tính và thống nhất không gán nhãn đối tượng nhỏ hơn 20px"* để loại bỏ các cảnh báo giả này khỏi tử số.
  3. *Bổ sung dữ liệu cho lớp thiểu số:* Thu thập thêm ảnh sạch cho lớp `truck` và `bus` để bù đắp cho các ảnh bị loại bỏ ở intake, giúp mô hình sau khi làm sạch đạt mAP cao và cân bằng giữa các lớp.

**(b) Ghi chú sử dụng công cụ AI:**
1. **Prompt chính:** "Đọc kỹ hướng dẫn GUIDE.md, quy định RUBRIC.md và các test case có sẵn trong tests/; triển khai 4 module theo đúng chuẩn TDD, chú trọng xử lý triệt để các ca biên như dòng nhãn trống, dòng chứa nhiều lỗi, toạ độ box tràn viền và tính toán IoU chính xác."
2. **Cách kiểm tra code AI:** Chạy bộ kiểm thử tự động toàn diện 79 unit tests bằng lệnh `python -m pytest -q`, kiểm tra mã thoát hệ thống, đối chiếu từng dòng nhật ký thay đổi trong `03_fixes.csv` và chạy script kiểm định tính toàn vẹn `check_submission.py`.
3. **Một lần AI gợi ý chưa tối ưu:** Ở bước calibration tham số `second_opinion.conf`, AI ban đầu đề xuất chọn ngưỡng `0.50`. Tuy nhiên, tôi đã trực tiếp đối chiếu bảng sweep và phản biện lại: ở ngưỡng `0.60`, Precision của `POSSIBLE_WRONG_CLASS` tăng từ 0.56 lên 0.62 (loại bớt 1 báo động giả) trong khi `POSSIBLE_MISSING` vẫn bảo toàn Recall tuyệt đối 1.00 (8/8 lỗi chèn), đồng thời giúp giảm số ảnh cảnh báo trên tập raw từ 70 xuống 65 ảnh để nằm gọn trong ngân sách duyệt 80 ảnh. AI đã thừa nhận phản biện chính xác của tôi và chúng tôi thống nhất chọn `conf = 0.60`.
