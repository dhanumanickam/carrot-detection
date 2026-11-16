"""
Computer Vision Image Processing & Enhancement Pipeline
========================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Handles preprocessing, adaptive contrast enhancement (CLAHE), illumination
correction, and inspection zone cropping for carrots moving on a conveyor.
"""

import cv2
import numpy as np


class ImageProcessor:
    """Preprocesses raw camera frames to maximize YOLO feature extraction."""

    def __init__(self, target_size=(640, 640), apply_clahe=True, clip_limit=2.0, tile_grid_size=(8, 8)):
        self.target_size = target_size
        self.apply_clahe = apply_clahe
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    def enhance_lighting(self, frame):
        """
        Applies CLAHE on the Lightness (L) channel in LAB color space.
        Normalizes conveyor lighting variations and shadow artifacts.
        """
        if not self.apply_clahe:
            return frame

        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Equalize L channel
        cl = self.clahe.apply(l)

        # Merge and convert back to BGR
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return enhanced

    def crop_inspection_roi(self, frame, roi_coords=None):
        """
        Crops frame to conveyor inspection zone.
        roi_coords: tuple of normalized coordinates (ymin, xmin, ymax, xmax)
        """
        if roi_coords is None:
            return frame

        h, w = frame.shape[:2]
        ymin, xmin, ymax, xmax = roi_coords
        y1, y2 = int(ymin * h), int(ymax * h)
        x1, x2 = int(xmin * w), int(xmax * w)
        return frame[y1:y2, x1:x2]

    def resize_with_pad(self, frame, target_size=None):
        """
        Resizes frame preserving aspect ratio with black letterboxing pads,
        identical to YOLO letterbox preprocessing.
        """
        if target_size is None:
            target_size = self.target_size

        target_w, target_h = target_size
        h, w = frame.shape[:2]

        scale = min(target_w / w, target_h / h)
        nw, nh = int(w * scale), int(h * scale)

        resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)

        # Create padded canvas
        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        dx = (target_w - nw) // 2
        dy = (target_h - nh) // 2
        canvas[dy:dy+nh, dx:dx+nw] = resized

        return canvas, scale, (dx, dy)

    def draw_inspection_overlay(self, frame, status_text="MONITORING"):
        """Draws professional industrial inspection HUD on camera frame."""
        h, w = frame.shape[:2]
        overlay = frame.copy()

        # Conveyor inspection bounding guide
        cv2.rectangle(overlay, (int(w * 0.15), int(h * 0.15)), (int(w * 0.85), int(h * 0.85)), (0, 255, 255), 2)
        
        # Header bar
        cv2.rectangle(overlay, (0, 0), (w, 36), (20, 20, 20), -1)
        cv2.putText(overlay, f"INSPECTION HUD: {status_text}", (15, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

        # Blend overlay
        return cv2.addWeighted(overlay, 0.9, frame, 0.1, 0)
