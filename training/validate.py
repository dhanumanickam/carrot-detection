"""
YOLO11 Model Validation Script for Carrot Quality Detection
============================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Validates the trained YOLO11 model on test/val partitions and extracts:
- Mean Average Precision (mAP@0.5, mAP@0.5:0.95)
- Precision, Recall, and F1-Scores per class
- Confusion Matrix
- Inference speed (preprocess, inference, postprocess latencies in ms)
"""

import os
import sys
import argparse
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_YAML = PROJECT_ROOT / "dataset" / "data.yaml"
MODELS_DIR = PROJECT_ROOT / "models"
DEFAULT_MODEL = MODELS_DIR / "best.pt"


def validate_yolo11(
    model_path=str(DEFAULT_MODEL),
    data_yaml=str(DATA_YAML),
    split="val",
    img_size=640,
    batch_size=16,
    project_dir=str(PROJECT_ROOT / "runs" / "val"),
    experiment_name="carrot_val_results"
):
    """
    Runs model validation and outputs academic evaluation metrics.
    """
    print("=" * 70)
    print("YOLO11 Model Validation & Academic Performance Evaluation")
    print("=" * 70)
    print(f"Model Path  : {model_path}")
    print(f"Data Config : {data_yaml}")
    print(f"Split       : {split}")
    
    if not os.path.exists(model_path):
        # Fallback to yolo11n.pt if best.pt is not yet trained
        fallback = "yolo11n.pt"
        print(f"[Notice] Model {model_path} not found. Attempting validation with base weights: {fallback}")
        model_path = fallback

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] Ultralytics is not installed. Please run: pip install ultralytics")
        sys.exit(1)

    model = YOLO(model_path)

    metrics = model.val(
        data=str(data_yaml),
        split=split,
        imgsz=img_size,
        batch=batch_size,
        project=project_dir,
        name=experiment_name,
        plots=True,
        save_json=True
    )

    print("\n" + "=" * 70)
    print("VALIDATION METRICS SUMMARY")
    print("=" * 70)

    try:
        # Extract metrics
        precision = metrics.box.mp
        recall = metrics.box.mr
        map50 = metrics.box.map50
        map50_95 = metrics.box.map
        f1_score = 2 * (precision * recall) / (precision + recall + 1e-16)

        print(f"Overall Precision (P)    : {precision * 100:.2f}%")
        print(f"Overall Recall (R)       : {recall * 100:.2f}%")
        print(f"F1-Score                 : {f1_score * 100:.2f}%")
        print(f"mAP @ 0.50 (PASCAL VOC)  : {map50 * 100:.2f}%")
        print(f"mAP @ 0.50:0.95 (COCO)   : {map50_95 * 100:.2f}%")

        # Class breakdown
        print("\n--- Per-Class Performance ---")
        class_names = ["Good_Carrot", "Damaged_Carrot", "Rotten_Carrot"]
        if hasattr(metrics.box, "p") and len(metrics.box.p) > 0:
            for idx, cname in enumerate(class_names):
                if idx < len(metrics.box.p):
                    cp = metrics.box.p[idx]
                    cr = metrics.box.r[idx]
                    cmap = metrics.box.all_ap[idx][0] if len(metrics.box.all_ap) > idx else 0.0
                    cf1 = 2 * (cp * cr) / (cp + cr + 1e-16)
                    print(f"Class [{idx}] {cname:<15}: P={cp*100:5.2f}% | R={cr*100:5.2f}% | F1={cf1*100:5.2f}% | mAP50={cmap*100:5.2f}%")

        # Speed metrics
        if hasattr(metrics, "speed"):
            print("\n--- Inference Latency (Raspberry Pi / System Benchmark) ---")
            print(f"Preprocess latency : {metrics.speed.get('preprocess', 0):.2f} ms")
            print(f"Inference latency  : {metrics.speed.get('inference', 0):.2f} ms")
            print(f"Postprocess latency: {metrics.speed.get('postprocess', 0):.2f} ms")
            total_lat = sum(metrics.speed.values())
            print(f"Total Pipeline     : {total_lat:.2f} ms (~{1000.0/max(total_lat, 1):.1f} FPS)")

    except Exception as e:
        print(f"[Notice] Metrics formatting note: {e}")

    print("=" * 70)
    print(f"Evaluation plots and confusion matrices saved to: {Path(project_dir) / experiment_name}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate YOLO11 Carrot Quality Model")
    parser.add_argument("--model", type=str, default=str(DEFAULT_MODEL), help="Path to .pt weights file")
    parser.add_argument("--data", type=str, default=str(DATA_YAML), help="Path to data.yaml")
    parser.add_argument("--split", type=str, default="val", choices=["val", "test"], help="Data split to evaluate")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    args = parser.parse_args()

    validate_yolo11(
        model_path=args.model,
        data_yaml=args.data,
        split=args.split,
        img_size=args.imgsz
    )
