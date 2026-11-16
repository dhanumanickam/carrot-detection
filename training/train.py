"""
YOLO11 Model Training Script for Carrot Quality Detection
==========================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

This script trains a YOLO11 object detection model to detect and classify
carrots into three quality tiers:
    0: Good_Carrot
    1: Damaged_Carrot
    2: Rotten_Carrot
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_YAML = PROJECT_ROOT / "dataset" / "data.yaml"
MODELS_DIR = PROJECT_ROOT / "models"


def get_available_device():
    """Detects available hardware acceleration (CUDA, MPS, or CPU)."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"[Device Selection] CUDA GPU detected: {gpu_name}")
            return 0
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("[Device Selection] Apple Silicon MPS detected.")
            return "mps"
        else:
            print("[Device Selection] Hardware acceleration unavailable. Using CPU.")
            return "cpu"
    except ImportError:
        print("[Warning] PyTorch not loaded directly; defaulting to auto.")
        return "auto"


def train_yolo11(
    data_yaml=str(DATA_YAML),
    base_model="yolo11n.pt",
    epochs=50,
    batch_size=16,
    img_size=640,
    project_dir=str(PROJECT_ROOT / "runs" / "train"),
    experiment_name="carrot_yolo11_run",
    device=None,
    seed=42,
    save_to_models=True
):
    """
    Trains the YOLO11 model on the carrot quality dataset.
    """
    print("=" * 70)
    print("YOLO11 Carrot Quality Detection Training Pipeline")
    print("=" * 70)
    print(f"Data Config : {data_yaml}")
    print(f"Base Weights: {base_model}")
    print(f"Epochs      : {epochs}")
    print(f"Batch Size  : {batch_size}")
    print(f"Image Size  : {img_size}")
    
    if not os.path.exists(data_yaml):
        raise FileNotFoundError(
            f"Dataset configuration not found at {data_yaml}. "
            "Please check dataset directory or run 'python training/generate_sample_dataset.py'."
        )

    try:
        from ultralytics import YOLO
    except ImportError:
        print("\n[ERROR] Ultralytics is not installed.")
        print("Please install via: pip install ultralytics")
        sys.exit(1)

    if device is None:
        device = get_available_device()

    print(f"\nInitializing YOLO model with base architecture: {base_model}...")
    model = YOLO(base_model)

    print("\nStarting model training...")
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project=project_dir,
        name=experiment_name,
        seed=seed,
        plots=True,
        save=True,
        verbose=True
    )

    print("\n" + "=" * 70)
    print("Training Completed Successfully!")
    print("=" * 70)

    # Locate best.pt
    run_dir = Path(project_dir) / experiment_name
    best_weights = run_dir / "weights" / "best.pt"
    
    if best_weights.exists() and save_to_models:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        dest_weights = MODELS_DIR / "best.pt"
        shutil.copy2(best_weights, dest_weights)
        print(f"Exported top weights to: {dest_weights}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO11 on Carrot Quality Dataset")
    parser.add_argument("--data", type=str, default=str(DATA_YAML), help="Path to data.yaml")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="Base model weights (yolo11n.pt, yolo11s.pt, etc.)")
    parser.add_argument("--epochs", type=int, default=30, help="Training epochs (default: 30)")
    parser.add_argument("--batch", type=int, default=8, help="Batch size (default: 8)")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image dimension (default: 640)")
    parser.add_argument("--device", type=str, default=None, help="Device to use: '0', 'cpu', 'mps'")
    parser.add_argument("--name", type=str, default="carrot_run", help="Experiment name")
    args = parser.parse_args()

    train_yolo11(
        data_yaml=args.data,
        base_model=args.model,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.imgsz,
        device=args.device,
        experiment_name=args.name
    )
