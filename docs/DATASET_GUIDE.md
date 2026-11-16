# Carrot Quality Dataset Collection and Annotation Guide
## Automated Carrot Quality Detection and Sorting System Using Deep Learning, Computer Vision and IoT
**Academic Master of Engineering (M.E.) Project**

---

## 1. Class Taxonomy and Quality Criteria

The computer vision model classifies carrots into three distinct quality grades based on physical morphology, surface defects, and pathological decay:

| Class ID | Label Name | Morphological & Surface Characteristics | Grading Standard | Physical Sorting Destination |
| :---: | :--- | :--- | :--- | :--- |
| **0** | **Good_Carrot** | - Vibrant, uniform orange pigmentation<br>- Straight, conical tapering shape<br>- Intact tip with no mechanical snaps<br>- Fresh foliage crown (minimal dry crown)<br>- Free from fissures, pest tunnels, or rot | **Grade A (Premium)**: Suitable for direct retail and supermarket distribution. | **Bin 1** (Servo Diverter 30°) |
| **1** | **Damaged_Carrot** | - Mechanical fracture, snaps, or blunt broken tips<br>- Surface cracking or longitudinal growth splits<br>- Harvester knife cuts or skin bruises<br>- Deformed shape (forked/curved bodies)<br>- **Crucial:** No active microbial fungal decay | **Grade B (Industrial/Processing)**: Unsuitable for whole retail; redirected for puree, baby food, or animal feed. | **Bin 2** (Servo Diverter 90°) |
| **2** | **Rotten_Carrot** | - Black or dark brown necrotic lesions (*Alternaria radicina*)<br>- Soft watery bacterial rot (*Pectobacterium carotovorum*)<br>- Fuzzy white, gray, or bluish fungal mycelium mold<br>- Sunken discolored surface cavities | **Grade C (Reject/Hazard)**: Bio-contaminant; immediate segregation to prevent batch spoilage. | **Bin 3** (Servo Diverter 150°) |

---

## 2. Image Collection Protocol

To achieve high generalization accuracy ($>95\%$ mAP@0.5) under real industrial packaging conditions, follow these acquisition rules:

1. **Mounting Geometry:**
   - Mount the USB camera directly perpendicular (top-down view, $90^\circ$ nadir angle) above the conveyor belt at a fixed height of $25\text{ cm} - 35\text{ cm}$.
2. **Illumination Setup:**
   - Use diffuse, ring-style or strip white LED lighting ($5000\text{K} - 6500\text{K}$ daylight color temperature).
   - Avoid direct point-source glare that creates white specular highlights on carrot skins.
3. **Background Contrast:**
   - Use a uniform conveyor belt color (matte black, dark green, or industrial blue belt).
4. **Dataset Size Recommendation for M.E. Project:**
   - Minimum 600 - 1,200 labeled images (approx. 200 - 400 images per class) across different orientations, rotations, and single vs. double carrot placements.

---

## 3. Annotation via Roboflow (Step-by-Step)

1. **Create Project:**
   - Visit [Roboflow](https://roboflow.com), create a free research account, and click **New Project**.
   - Project Type: **Object Detection**.
   - Name: `Carrot-Quality-YOLO11`.
2. **Define Classes:**
   - Add the exact three classes: `Good_Carrot`, `Damaged_Carrot`, `Rotten_Carrot`.
3. **Draw Bounding Boxes:**
   - Draw tight rectangular bounding boxes around every carrot on the belt.
   - If a carrot has visible cracks or broken tips, label as `Damaged_Carrot`.
   - If a carrot has dark fungal rot spots or mold, label as `Rotten_Carrot`.
   - If completely healthy and intact, label as `Good_Carrot`.
4. **Apply Preprocessing & Augmentations:**
   - Resize: $640 \times 640$ (Stretch or Auto-Orient).
   - Augmentations:
     - Flip: Horizontal and Vertical.
     - Rotation: Between $-30^\circ$ and $+30^\circ$.
     - Brightness: $\pm 15\%$.
     - Hue: $\pm 10^\circ$ (simulates varying carrot orange shades).
5. **Export Format:**
   - Select **YOLOv11 PyTorch** (or YOLOv8 PyTorch format, which is $100\%$ compatible).
   - Download the zip and extract contents into the `dataset/` directory.

---

## 4. Dataset Directory Layout

The dataset must follow the standard Ultralytics YOLO layout:

```
dataset/
│
├── data.yaml              <-- Specifies paths, classes, and nc: 3
│
├── train/
│   ├── images/            <-- Training images (e.g., carrot_001.jpg)
│   └── labels/            <-- YOLO annotations (e.g., carrot_001.txt)
│
├── val/
│   ├── images/            <-- Validation images (for checkpoint evaluation)
│   └── labels/
│
└── test/
    ├── images/            <-- Unseen test images (for final mAP metrics)
    └── labels/
```

### YOLO Annotation File Format (`.txt`)
Each `.txt` label file contains one line per detected object:
```text
<class_id> <x_center> <y_center> <width> <height>
```
All coordinates are normalized between `0.0` and `1.0` relative to image dimensions.

---

## 5. Training and Evaluation Workflow

### Step 1: Verify Pipeline with Synthetic Data (Optional)
If your physical laboratory dataset is not yet collected, run the built-in generator:
```bash
python training/generate_sample_dataset.py --samples 50
```

### Step 2: Split Unpartitioned Images
If you have raw annotated images in a single folder:
```bash
python training/split_dataset.py --source /path/to/raw_dataset --output dataset/
```

### Step 3: Train YOLO11 Model
```bash
python training/train.py --epochs 50 --batch 16 --imgsz 640
```
Upon completion, the best weights are automatically saved to `models/best.pt`.

### Step 4: Validate and Generate Academic Metrics
```bash
python training/validate.py --model models/best.pt --split test
```

### Step 5: Test Single Image Prediction
```bash
python training/predict.py --source dataset/test/images/good_carrot_test_0001.jpg
```
