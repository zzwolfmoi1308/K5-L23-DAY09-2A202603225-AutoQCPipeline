#!/usr/bin/env python3
"""Train yolo26n trên dữ liệu GỐC và dữ liệu SAU PIPELINE, đo trên cùng tập test (ĐÃ VIẾT SẴN).

    python scripts/train_compare.py --variants raw clean --seeds 0 1 2 --epochs 40
    python scripts/train_compare.py --variants raw clean oracle --seeds 0 --epochs 40 --device cpu   # chạy thử nhanh

Công bằng: cùng model khởi tạo (yolo26n.pt), cùng siêu tham số, cùng seed, cùng val (gold_val), cùng test.
Mỗi lần chạy ghi `submission/results/<variant>_seed<k>.json`; tổng hợp bằng scripts/summarize_results.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from materialize_dataset import NAMES, materialize  # noqa: E402


def pick_device(req: str):
    if req != "auto":
        return req
    import torch
    return 0 if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variants", nargs="+", default=["raw", "clean"], choices=["raw", "clean", "auto", "oracle"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--model", default="yolo26n.pt")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--export", default="submission/export/clean_v1")
    ap.add_argument("--export-auto", default="submission/export/clean_auto")
    ap.add_argument("--skip-existing", action="store_true", help="bỏ qua lần chạy đã có JSON (chạy tiếp sau khi Colab rớt)")
    ap.add_argument("--out", default="submission/results")
    ap.add_argument("--work", default="work/train")
    a = ap.parse_args()

    from ultralytics import YOLO
    device = pick_device(a.device)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    for variant in a.variants:
        exp = ROOT / (a.export_auto if variant == "auto" else a.export)
        yaml_path = None
        for seed in a.seeds:
            name = f"{variant}_seed{seed}"
            if a.skip_existing and (out / f"{name}.json").exists():
                print("bỏ qua", name)
                continue
            if yaml_path is None:
                yaml_path = materialize(variant, ROOT / a.work / variant, exp)
            t0 = time.time()
            model = YOLO(a.model)
            model.train(data=str(yaml_path), epochs=a.epochs, imgsz=a.imgsz, batch=a.batch, seed=seed, deterministic=True,
                        device=device, project=str(ROOT / a.work / "runs"), name=name, exist_ok=True, plots=False,
                        workers=2, verbose=False, patience=0)
            best = YOLO(str(ROOT / a.work / "runs" / name / "weights" / "best.pt"))
            m = best.val(data=str(yaml_path), split="test", imgsz=a.imgsz, device=device, plots=False, verbose=False)
            per_class = {NAMES[int(c)]: round(float(v), 4) for c, v in zip(m.box.ap_class_index, m.box.ap50)}
            res = dict(variant=variant, seed=seed, epochs=a.epochs, model=a.model, device=str(device),
                       map50=round(float(m.box.map50), 4), map50_95=round(float(m.box.map), 4),
                       precision=round(float(m.box.mp), 4), recall=round(float(m.box.mr), 4),
                       ap50_per_class=per_class, manifest_sha1=(hashlib.sha1((exp / "manifest.json").read_bytes()).hexdigest() if variant != "raw" and (exp / "manifest.json").exists() else None),
                       config_sha1=hashlib.sha1((ROOT / "configs/pipeline.yaml").read_bytes()).hexdigest(), batch=a.batch, imgsz=a.imgsz, train_images=len(list((ROOT / a.work / variant / "train" / "images").iterdir())),
                       seconds=round(time.time() - t0, 1))
            (out / f"{name}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
            print("=>", json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
