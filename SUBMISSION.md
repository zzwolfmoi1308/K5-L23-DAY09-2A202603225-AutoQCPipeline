# Nộp bài

## Repo
Một người **một repo public**. Tên repo: `K5-L23-DAY09-<MSHV>-AutoQCPipeline` (không dấu, nối bằng `-`). Theo hướng dẫn lớp nếu giảng viên đặt quy ước khác.

## Trước khi nộp
1. Đổi dòng tiêu đề `# Day 09 Lab ...` của `README.md`: `# Day 09 Lab — <Họ và tên>: <MSHV> - <Họ và tên>`.
2. Điền `submission/REPORT.md` (xoá mọi dòng `TODO(học viên)`).
3. `make check-core` (phần lõi) hoặc `make check` (nếu đã train; tức `python scripts/check_submission.py [--no-train]`) hết **LỖI**.
4. Nộp link repo lên LMS **https://aithucchien.vinuni.edu.vn** hoặc kênh giảng viên chỉ định.

## Cấu trúc bắt buộc
```text
README.md                         # dòng tiêu đề có MSHV - Họ và tên
configs/pipeline.yaml             # ĐÃ calibrate (khác giá trị khởi đầu)
pipeline/ …                       # code của bạn; pytest xanh
submission/
├── REPORT.md                     # báo cáo duy nhất (6 mục)
├── calibration/                  # calibration_report.md|json (sinh bởi `make calibrate`)
├── reports/                      # 01_intake … 08_summary.json, class_stats.csv  (sinh bởi `make run`)
├── export/clean_v1/              # labels/, data.yaml, manifest.json
└── results/                      # (tùy chọn, chấm riêng) raw_seed*.json, clean_seed*.json, comparison.md|json|png
```
Không commit `work/`, `*.pt`.
