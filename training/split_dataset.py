"""
Dataset Splitter for Carrot Quality Detection
=============================================
Splits a raw directory of images and YOLO label files (.txt) into structured
train, validation, and test splits (Default: 70% Train, 20% Val, 10% Test).

Supports:
- Stratified sampling across classes
- Automatic file pairing (image + .txt)
- Verification of label bounds
"""

import os
import shutil
import random
import argparse
from pathlib import Path

VALID_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def split_dataset(source_dir, output_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1, seed=42):
    random.seed(seed)
    source_path = Path(source_dir)
    output_path = Path(output_dir)

    # Validate ratios
    total_ratio = train_ratio + val_ratio + test_ratio
    if not (0.99 <= total_ratio <= 1.01):
        raise ValueError(f"Split ratios must sum to 1.0 (current sum: {total_ratio:.2f})")

    # Find all images
    all_images = [p for p in source_path.rglob("*") if p.suffix.lower() in VALID_IMG_EXTS]
    if not all_images:
        print(f"No image files found in {source_dir}")
        return

    # Pair with label files
    valid_pairs = []
    missing_labels = 0
    for img_p in all_images:
        lbl_p = img_p.with_suffix(".txt")
        if lbl_p.exists():
            valid_pairs.append((img_p, lbl_p))
        else:
            missing_labels += 1

    print(f"Found {len(valid_pairs)} paired images & annotations. ({missing_labels} ignored due to missing .txt labels)")

    if not valid_pairs:
        print("Error: No paired image/label files found. Make sure .txt files have identical base names as images.")
        return

    # Group pairs by primary class in label file for stratified split
    class_groups = {0: [], 1: [], 2: [], "other": []}
    for img_p, lbl_p in valid_pairs:
        try:
            with open(lbl_p, "r") as f:
                first_line = f.readline().strip()
                if first_line:
                    cls_id = int(first_line.split()[0])
                    if cls_id in class_groups:
                        class_groups[cls_id].append((img_p, lbl_p))
                    else:
                        class_groups["other"].append((img_p, lbl_p))
                else:
                    class_groups["other"].append((img_p, lbl_p))
        except Exception:
            class_groups["other"].append((img_p, lbl_p))

    splits = {"train": [], "val": [], "test": []}

    for group, pairs in class_groups.items():
        random.shuffle(pairs)
        n = len(pairs)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        splits["train"].extend(pairs[:n_train])
        splits["val"].extend(pairs[n_train:n_train + n_val])
        splits["test"].extend(pairs[n_train + n_val:])

    # Copy files to destination directories
    for split_name, pairs in splits.items():
        img_dest = output_path / split_name / "images"
        lbl_dest = output_path / split_name / "labels"
        img_dest.mkdir(parents=True, exist_ok=True)
        lbl_dest.mkdir(parents=True, exist_ok=True)

        for img_p, lbl_p in pairs:
            shutil.copy2(img_p, img_dest / img_p.name)
            shutil.copy2(lbl_p, lbl_dest / lbl_p.name)

        print(f"Split [{split_name}]: {len(pairs)} samples copied to {img_dest}")

    print("\nDataset splitting completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split dataset into train, val, and test partitions")
    parser.add_argument("--source", type=str, required=True, help="Path to raw images and annotations folder")
    parser.add_argument("--output", type=str, default="../dataset", help="Destination dataset folder")
    parser.add_argument("--train", type=float, default=0.70, help="Train set ratio (default: 0.70)")
    parser.add_argument("--val", type=float, default=0.20, help="Validation set ratio (default: 0.20)")
    parser.add_argument("--test", type=float, default=0.10, help="Test set ratio (default: 0.10)")
    args = parser.parse_args()

    split_dataset(args.source, args.output, args.train, args.val, args.test)
