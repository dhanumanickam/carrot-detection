"""
Camera Video Streaming & Frame Acquisition Module
=================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Handles real-time video capture from:
1. Physical USB Webcams (Index 0, 1, 2)
2. Raspberry Pi Camera Module (CSI/V4L2)
3. Simulated Industrial Conveyor Stream (Synthetic video mode for PC development)
"""

import time
import threading
import cv2
import numpy as np
from pathlib import Path


class CameraStream:
    """Thread-safe multi-source camera streaming service."""

    def __init__(self, camera_index=0, width=640, height=480, fps=30, force_simulation=False):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.force_simulation = force_simulation

        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.lock = threading.Lock()
        self.is_simulation = False

        # Simulation animation states
        self._sim_offset = 0
        self._last_carrot_time = 0
        self._current_sim_carrot = None

        self._initialize_camera()

    def _initialize_camera(self):
        """Attempts to open physical camera; falls back to simulation if missing."""
        if not self.force_simulation:
            print(f"[Camera] Probing physical camera device index {self.camera_index}...")
            # On Windows, try cv2.CAP_DSHOW or default
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if cv2.CAP_DSHOW else cv2.CAP_ANY)
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    print(f"[Camera] Physical camera successfully initialized at {self.width}x{self.height} @ {self.fps}fps")
                    self.is_simulation = False
                    return
                else:
                    self.cap.release()

        # Fallback to simulation mode
        print("[Camera] No physical camera hardware detected or force_simulation=True.")
        print("[Camera] Initializing Simulated Conveyor Camera Feed (Auto-PC Mode).")
        self.is_simulation = True
        self.cap = None

    def start(self):
        """Starts background frame polling thread."""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        """Continuous frame polling loop."""
        delay = 1.0 / self.fps
        while self.is_running:
            start_t = time.time()
            if not self.is_simulation and self.cap is not None:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    with self.lock:
                        self.current_frame = frame
                else:
                    # Camera disconnected; switch to simulation
                    self.is_simulation = True
            else:
                sim_frame = self._generate_simulation_frame()
                with self.lock:
                    self.current_frame = sim_frame

            elapsed = time.time() - start_t
            sleep_t = max(0.001, delay - elapsed)
            time.sleep(sleep_t)

    def _generate_simulation_frame(self):
        """Generates dynamic synthetic conveyor feed with moving belt and carrots."""
        frame = np.full((self.height, self.width, 3), (50, 52, 54), dtype=np.uint8)
        
        # Draw conveyor belt surface
        belt_top = int(self.height * 0.15)
        belt_bot = int(self.height * 0.85)
        cv2.rectangle(frame, (0, belt_top), (self.width, belt_bot), (40, 42, 44), -1)

        # Draw moving conveyor tracks / ribs
        self._sim_offset = (self._sim_offset + 3) % 40
        for x in range(self._sim_offset, self.width, 40):
            cv2.line(frame, (x, belt_top), (x, belt_bot), (30, 32, 34), 2)

        # Draw conveyor side rails
        cv2.rectangle(frame, (0, belt_top - 10), (self.width, belt_top), (120, 125, 130), -1)
        cv2.rectangle(frame, (0, belt_bot), (self.width, belt_bot + 10), (120, 125, 130), -1)

        # Conveyor inspection zone guide
        cv2.rectangle(frame, (int(self.width * 0.3), belt_top + 10), (int(self.width * 0.7), belt_bot - 10), (0, 180, 255), 1)
        cv2.putText(frame, "[INSPECTION ZONE]", (int(self.width * 0.32), belt_top + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 180, 255), 1)

        # Add simulated carrot passing across the camera
        now = time.time()
        if self._current_sim_carrot is None and (now - self._last_carrot_time > 4.0):
            import random
            self._current_sim_carrot = {
                "x": -80,
                "y": self.height // 2,
                "quality": random.choice([0, 0, 1, 2]), # 50% good, 25% damaged, 25% rotten
                "speed": random.uniform(4.5, 7.0)
            }
            self._last_carrot_time = now

        if self._current_sim_carrot is not None:
            c = self._current_sim_carrot
            c["x"] += c["speed"]

            # Draw carrot body
            cx = int(c["x"])
            cy = int(c["y"])
            if -100 <= cx <= self.width + 100:
                q = c["quality"]
                color = (25, 130, 240) if q == 0 else ((35, 105, 210) if q == 1 else (30, 60, 110))
                
                # Draw elongated carrot ellipse
                cv2.ellipse(frame, (cx, cy), (65, 22), 0, 0, 360, color, -1)
                # Crown
                cv2.circle(frame, (cx - 60, cy), 12, (20, 160, 40), -1)
                
                if q == 1: # Crack defect
                    cv2.line(frame, (cx - 10, cy - 15), (cx + 15, cy + 15), (10, 15, 30), 3)
                elif q == 2: # Rot spots
                    cv2.circle(frame, (cx - 15, cy), 12, (15, 20, 35), -1)
                    cv2.circle(frame, (cx + 20, cy - 5), 10, (15, 20, 35), -1)

            if c["x"] > self.width + 120:
                self._current_sim_carrot = None
                self._last_carrot_time = now

        # Timestamp & Status HUD
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"CAM FEED (SIMULATION) | {timestamp}", (12, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        return frame

    def read_frame(self):
        """Returns the most recent captured frame (thread-safe)."""
        with self.lock:
            if self.current_frame is None:
                # Return blank placeholder if not yet ready
                return np.zeros((self.height, self.width, 3), dtype=np.uint8)
            return self.current_frame.copy()

    def generate_mjpeg_frames(self):
        """Yields MJPEG byte streams for Flask /video_feed route."""
        while self.is_running:
            frame = self.read_frame()
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(1.0 / self.fps)

    def stop(self):
        """Terminates camera capture and releases hardware resources."""
        self.is_running = False
        if hasattr(self, "thread"):
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("[Camera] Camera stream stopped successfully.")
