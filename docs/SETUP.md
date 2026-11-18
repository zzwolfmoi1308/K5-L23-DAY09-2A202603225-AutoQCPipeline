# Cài đặt môi trường

| Việc | Lệnh |
|---|---|
| Python 3.9–3.13 | `python --version` |
| Môi trường ảo | `python -m venv .venv` rồi `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`) |
| Thư viện (nhẹ, **không** cần torch/GPU) | `pip install -r requirements.txt` |
| Kiểm tra | `python -m pytest -q` → lúc đầu **55 failed, 24 passed** (đúng như dự kiến: 5 check đã viết sẵn) |

- **Windows:** không có `make`; chạy thẳng các lệnh `python ...` trong [Makefile](../Makefile). Đặt `set PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8=1`).
- **Mã thoát:** `python -m pipeline.run; echo $?` (PowerShell: `$LASTEXITCODE`): 0 Release · 10 Hold · 20 Rework · 30 tạm dừng chờ người duyệt.
- **Train cục bộ (không bắt buộc):** `pip install -r requirements-train.txt`; nên dùng Colab, xem [COLAB.md](COLAB.md).
- Mọi dữ liệu và cache model đã nằm trong repo; **không** cần tải model.
