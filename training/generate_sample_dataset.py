"""
Sample Dataset Generator for Carrot Quality Detection Pipeline Verification.
=============================================================================
This utility programmatically creates synthetic carrot images with realistic
visual features and corresponding normalized YOLO bounding box label files (.txt)
for all three classes:
    Class 0: Good_Carrot    (Bright uniform orange, intact tip, fresh green crown)
    Class 1: Damaged_Carrot (Broken body, mechanical cracks, splits, blunt ends)
    Class 2: Rotten_Carrot  (Discoloration, black/dark-brown fungal rot patches, mold)

NOTE: This script is provided so researchers, examiners, and students can
verify the entire training, validation, and inference pipeline end-to-end
immediately without needing external downloads. For production M.E. thesis
results, follow the instructions in docs/DATASET_GUIDE.md to collect and annotate
real laboratory/farm carrot images.
"""

import os
import random
import math
import numpy as np
import cv2

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")

CLASSES = {
    0: "Good_Carrot",
    1: "Damaged_Carrot",
    2: "Rotten_Carrot"
}


def draw_realistic_carrot(img_size=(640, 640), category=0):
    """
    Renders a synthetic carrot with specific morphological and surface
    characteristics corresponding to Good, Damaged, or Rotten quality.
    
    Returns:
        image (np.ndarray): BGR image of dimensions img_size.
        bbox (tuple): Normalized (x_center, y_center, width, height) in YOLO format.
    """
    w, h = img_size
    # Create realistic conveyor / inspection background (neutral matte gray or dark conveyor belt)
    belt_color = random.randint(45, 65)
    img = np.full((h, w, 3), (belt_color, belt_color + 3, belt_color + 2), dtype=np.uint8)
    
    # Add subtle conveyor texture noise
    noise = np.random.normal(0, 4, (h, w, 3)).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Random carrot geometry and orientation
    angle = random.uniform(-40, 40)
    center_x = random.randint(int(w * 0.35), int(w * 0.65))
    center_y = random.randint(int(h * 0.35), int(h * 0.65))
    
    carrot_length = random.randint(int(h * 0.45), int(h * 0.70))
    carrot_width = random.randint(int(w * 0.12), int(w * 0.18))

    # Base polygon for conical carrot shape
    # Crown is wide at top, tapering down to a narrow tip
    half_w = carrot_width / 2
    half_l = carrot_length / 2

    if category == 1:
        # Damaged carrot: may be broken in half, have a blunt tip, or severe crack
        damage_type = random.choice(["snapped", "cracked", "bitten"])
        if damage_type == "snapped":
            half_l *= random.uniform(0.55, 0.75) # shortened broken carrot

    pts = [
        (-half_w * 0.85, -half_l),       # top-left crown
        (half_w * 0.85, -half_l),        # top-right crown
        (half_w * 0.95, -half_l * 0.5),  # upper body
        (half_w * 0.60, 0),              # mid body
        (half_w * 0.25, half_l * 0.7),   # lower body
        (0 if category != 1 else half_w * 0.3, half_l), # tip (sharp for good, blunt/broken for damaged)
        (-half_w * 0.25, half_l * 0.7),
        (-half_w * 0.60, 0),
        (-half_w * 0.95, -half_l * 0.5),
    ]

    # Rotate and translate points to image coordinates
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    
    transformed_pts = []
    for px, py in pts:
        rx = px * cos_a - py * sin_a + center_x
        ry = px * sin_a + py * cos_a + center_y
        transformed_pts.append([int(rx), int(ry)])
    
    pts_arr = np.array(transformed_pts, dtype=np.int32)

    # Base carrot colors (BGR)
    # Bright healthy carrot: Orange B: 20-35, G: 110-140, R: 220-250
    if category == 0:
        base_color = (random.randint(15, 30), random.randint(115, 145), random.randint(225, 255))
    elif category == 1:
        # Damaged: slightly dried cut edges
        base_color = (random.randint(25, 45), random.randint(100, 130), random.randint(200, 235))
    else:
        # Rotten: discolored, brownish-dark orange to sickly pale
        base_color = (random.randint(20, 50), random.randint(60, 95), random.randint(120, 170))

    # Fill base carrot polygon
    cv2.fillPoly(img, [pts_arr], base_color)
    cv2.polylines(img, [pts_arr], True, (max(0, base_color[0]-15), max(0, base_color[1]-15), max(0, base_color[2]-15)), 2)

    # Add green foliage crown at top if healthy/damaged
    if category in [0, 1]:
        crown_x = int(-half_l * sin_a + center_x)
        crown_y = int(-half_l * cos_a + center_y)
        green_color = (random.randint(20, 45), random.randint(140, 180), random.randint(30, 60))
        cv2.circle(img, (crown_x, crown_y), int(carrot_width * 0.25), green_color, -1)

    # Category-specific defect features
    if category == 1:
        # Damaged Carrot: Add cracks, fissures, or mechanical slices
        num_cracks = random.randint(1, 3)
        for _ in range(num_cracks):
            cx = center_x + random.randint(int(-carrot_width * 0.4), int(carrot_width * 0.4))
            cy = center_y + random.randint(int(-carrot_length * 0.3), int(carrot_length * 0.3))
            c_len = random.randint(20, 50)
            crack_angle = angle + random.uniform(50, 110)
            c_rad = math.radians(crack_angle)
            x2 = int(cx + c_len * math.cos(c_rad))
            y2 = int(cy + c_len * math.sin(c_rad))
            cv2.line(img, (cx, cy), (x2, y2), (10, 15, 35), thickness=random.randint(3, 5))
            # inner exposed paler flesh
            cv2.line(img, (cx, cy), (x2, y2), (60, 160, 240), thickness=1)

    elif category == 2:
        # Rotten Carrot: Add dark brown/black necrotic rot patches, fungal spots, fuzzy mold
        num_rot_spots = random.randint(3, 7)
        for _ in range(num_rot_spots):
            rx = center_x + random.randint(int(-carrot_width * 0.5), int(carrot_width * 0.5))
            ry = center_y + random.randint(int(-carrot_length * 0.4), int(carrot_length * 0.4))
            r_radius = random.randint(12, 32)
            rot_color = (random.randint(15, 35), random.randint(20, 45), random.randint(30, 60))
            cv2.circle(img, (rx, ry), r_radius, rot_color, -1)
            # Fungal mold halo
            cv2.circle(img, (rx, ry), int(r_radius * 1.3), (random.randint(70, 110), random.randint(80, 120), random.randint(70, 110)), 1)

    # Compute bounding box around carrot points
    xs = [p[0] for p in transformed_pts]
    ys = [p[1] for p in transformed_pts]
    min_x = max(0, min(xs) - 8)
    max_x = min(w - 1, max(xs) + 8)
    min_y = max(0, min(ys) - 8)
    max_y = min(h - 1, max(ys) + 8)

    # Convert to normalized YOLO format: center_x, center_y, width, height
    box_w = (max_x - min_x) / float(w)
    box_h = (max_y - min_y) / float(h)
    box_x = (min_x + max_x) / 2.0 / float(w)
    box_y = (min_y + max_y) / 2.0 / float(h)

    # Clip to valid (0.0, 1.0)
    box_x = max(0.01, min(0.99, box_x))
    box_y = max(0.01, min(0.99, box_y))
    box_w = max(0.01, min(0.99, box_w))
    box_h = max(0.01, min(0.99, box_h))

    return img, (box_x, box_y, box_w, box_h)


def generate_dataset(num_samples_per_class=30):
    """
    Generates balanced samples across all 3 classes and populates
    train, val, and test splits (70% train, 20% val, 10% test).
    """
    print(f"Generating synthetic verification dataset: {num_samples_per_class} samples/class...")
    
    splits = {
        "train": int(num_samples_per_class * 0.70),
        "val": int(num_samples_per_class * 0.20),
        "test": num_samples_per_class - int(num_samples_per_class * 0.70) - int(num_samples_per_class * 0.20)
    }

    total_images = 0

    for cls_id, cls_name in CLASSES.items():
        sample_idx = 0
        for split, count in splits.items():
            img_dir = os.path.join(DATASET_DIR, split, "images")
            lbl_dir = os.path.join(DATASET_DIR, split, "labels")
            os.makedirs(img_dir, exist_ok=True)
            os.makedirs(lbl_dir, exist_ok=True)

            for i in range(count):
                sample_idx += 1
                img, bbox = draw_realistic_carrot(img_size=(640, 640), category=cls_id)
                
                filename = f"{cls_name.lower()}_{split}_{i+1:04d}"
                img_path = os.path.join(img_dir, f"{filename}.jpg")
                lbl_path = os.path.join(lbl_dir, f"{filename}.txt")

                # Save Image
                cv2.imwrite(img_path, img)

                # Save YOLO Annotation: <class> <x_center> <y_center> <width> <height>
                with open(lbl_path, "w") as f:
                    f.write(f"{cls_id} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")
                
                total_images += 1

    print(f"Verification dataset created successfully!")
    print(f"Total synthetic images generated: {total_images}")
    print(f"Split breakdown: Train: {splits['train']*3}, Val: {splits['val']*3}, Test: {splits['test']*3}")
    print(f"Dataset root: {DATASET_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic carrot dataset for YOLO11 pipeline verification")
    parser.add_argument("--samples", type=int, default=30, help="Number of samples per class (default: 30)")
    args = parser.parse_args()
    
    generate_dataset(num_samples_per_class=args.samples)
