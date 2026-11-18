"""Đăng ký các check (ĐÃ VIẾT SẴN). Thứ tự = thứ tự chạy và thứ tự trong báo cáo.

Mỗi module trong thư mục này phải có `run(ds, cfg) -> list[Issue]`.
- INTAKE_CHECKS chạy ở bước 1 (cửa vào, rẻ nhất khi lỗi chưa tốn công).
- QC_CHECKS chạy ở bước 4 (QC tự động, lặp nhiều vòng).
"""
from importlib import import_module

INTAKE_CHECKS = ["images", "duplicates"]
QC_CHECKS = ["missing_labels", "label_format", "class_names", "stats", "second_opinion"]


def load(name):
    return import_module(f"pipeline.checks.{name}")


def run_checks(names, ds, cfg):
    out = []
    for n in names:
        out.extend(load(n).run(ds, cfg))
    return out
