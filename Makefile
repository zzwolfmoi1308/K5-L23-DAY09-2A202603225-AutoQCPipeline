# Lệnh tắt. Chạy từ thư mục gốc repo. Windows không có make: chạy trực tiếp các lệnh python bên dưới.
PY ?= $(shell command -v python3 >/dev/null 2>&1 && echo python3 || echo python)
export PYTHONUTF8=1

test:            ## chạy unit test (tiến độ của bạn: xanh hết = xong phần code)
	$(PY) -m pytest -q

calibrate:       ## chạy 2 sweep và ghi submission/calibration/calibration_report.md
	$(PY) -m pipeline.calibrate --sweep duplicates.phash_dist=2,4,6,8,10,12,14,16,20 --sweep second_opinion.conf=0.1,0.25,0.4,0.5,0.6,0.7,0.8 --out submission/calibration

run:             ## MỘT LỆNH chạy cả pipeline. Kết luận 0/10/20 (Release/Hold/Rework) = make thành công (kết luận in ở cuối); mã khác = lỗi thật
	$(PY) -m pipeline.run; rc=$$?; case $$rc in 0|10|20) exit 0;; *) echo "pipeline lỗi hoặc tạm dừng (mã $$rc)"; exit $$rc;; esac

train:           ## train raw vs clean (cần GPU; nên chạy trên Colab)
	$(PY) scripts/train_compare.py --variants raw clean --seeds 0 1 --epochs 20
	$(PY) scripts/summarize_results.py

check:           ## kiểm tra bài nộp (đầy đủ, gồm train)
	$(PY) scripts/check_submission.py

check-core:      ## kiểm tra bài nộp, BỎ QUA train (chưa có Colab)
	$(PY) scripts/check_submission.py --no-train

all: test run check
