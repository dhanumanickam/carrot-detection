# System Architecture Specification
## Automated Carrot Quality Detection and Sorting System Using Deep Learning, Computer Vision and IoT
**Academic Master of Engineering (M.E.) Project**

---

## 1. Executive Architecture Overview

The system operates as an autonomous, closed-loop cyber-physical sorting machine. It integrates high-speed computer vision, deep convolutional feature extraction (YOLO11), real-time embedded hardware control (Raspberry Pi GPIO), and an industrial IoT web monitoring dashboard.

```mermaid
graph TD
    subgraph SENSING ["1. SENSING STAGE"]
        A[Conveyor Belt Entry] --> B[IR Proximity Sensor]
        B -->|Hardware Interrupt Pin 17| C[Raspberry Pi 4 / 5]
    end

    subgraph VISION ["2. VISION & AI INFERENCE"]
        C -->|Trigger Capture| D[High-Resolution Camera]
        D -->|Raw Frame 640x480| E[OpenCV Preprocessing & CLAHE]
        E -->|Normalized Tensor| F[YOLO11 Neural Network]
        F -->|Bounding Box + Class + Conf| G[Decision Engine]
    end

    subgraph ACTUATION ["3. PHYSICAL SORTING & ACTUATION"]
        G -->|Calculate Velocity & Delay| H[Conveyor Timing Scheduler]
        H -->|PWM Angle Trigger Pin 12| I[3-Position Servo Diverter]
        I -->|30 deg| J[Bin 1: Good Carrots]
        I -->|90 deg| K[Bin 2: Damaged Carrots]
        I -->|150 deg| L[Bin 3: Rotten Carrots]
        I -->|0 deg Neutral| M[Reject / Manual Chute]
    end

    subgraph IOT ["4. IOT & WEB ANALYTICS"]
        G -->|Commit Record| N[(SQLite Database)]
        D -->|MJPEG Live Stream| O[Flask Web Server]
        N -->|REST API /api/stats| P[IoT Web Dashboard]
        P -->|Manual Control Override| C
    end

    style J fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style K fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    style L fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff
    style M fill:#6b7280,stroke:#4b5563,stroke-width:2px,color:#fff
```

---

## 2. Sequence of Operations (Closed-Loop Automation)

```mermaid
sequenceDiagram
    autonumber
    actor Carrot as Carrot on Belt
    participant IR as IR Optical Sensor
    participant RPi as Raspberry Pi Controller
    participant Cam as Camera Subsystem
    participant YOLO as YOLO11 Inference Engine
    participant DE as Decision Engine
    participant Servo as 3-Way Servo Sorter
    participant DB as SQLite DB & Dashboard

    Carrot->>IR: Breaks optical IR beam
    IR-->>RPi: Active-LOW interrupt signal (GPIO 17)
    RPi->>Cam: Trigger frame acquisition
    Cam-->>RPi: Transmit inspection frame (BGR 640x480)
    RPi->>RPi: CLAHE lighting enhancement & ROI crop
    RPi->>YOLO: Pass tensor through YOLO11 backbone
    YOLO-->>DE: Detected BBox, Class (0/1/2), Confidence (%)
    DE->>DE: Compute travel delay t = Distance / Belt_Velocity
    DE->>DB: Log inspection event & store annotated image
    DB-->>RPi: Broadcast event to Web UI via polling
    Note over RPi,Servo: Carrot moves from camera station to diverter gate
    RPi->>Servo: Actuate to target bin angle (30°, 90°, or 150°)
    Servo->>Servo: Hold diverter for 1.2s dwell time
    Servo->>Carrot: Directs carrot into designated physical bin
    Servo->>RPi: Return diverter arm to neutral 0° (Home)
```

---

## 3. Mathematical Formulations & Mechanical Timing

### 3.1 Conveyor Belt Linear Velocity
The linear velocity of the conveyor belt $v$ is determined by the DC motor rotational speed and the conveyor drive pulley radius $R_p$:

$$v = \omega \cdot R_p = \left( \frac{2\pi \cdot N}{60} \right) \cdot R_p$$

Where:
- $N$ = Effective motor rotational speed (RPM) under load, modulated by PWM duty cycle $D$:
  $$N(D) = N_{\text{max}} \cdot \left(\frac{D}{100}\right)$$
- $R_p$ = Drive pulley radius ($0.025\text{ m} = 25\text{ mm}$)
- $v_{\text{max}}$ = Nominal maximum velocity at $D=100\%$ ($0.20\text{ m/s}$)

### 3.2 Time-of-Flight (Travel Delay)
The time interval $t_{\text{delay}}$ required for a carrot to travel from the camera optical inspection centerline to the physical sorting diverter gate located at distance $L$ is:

$$t_{\text{delay}} = \frac{L}{v} = \frac{L}{v_{\text{max}} \cdot \left(\frac{D}{100}\right)}$$

For a physical separation of $L = 0.35\text{ m}$ (35 cm) and operating duty cycle $D = 70\%$:
$$v = 0.20 \cdot 0.70 = 0.14\text{ m/s}$$
$$t_{\text{delay}} = \frac{0.35\text{ m}}{0.14\text{ m/s}} = 2.50\text{ seconds}$$

The Raspberry Pi scheduler starts a non-blocking asynchronous timer for $t_{\text{delay}}$ before driving the servo diverter.

### 3.3 50Hz PWM Duty Cycle Formula for Servos
Standard analog and digital hobby/industrial servos (TowerPro SG90, MG995, MG996R) operate with a $50\text{ Hz}$ frame frequency ($T = 20\text{ ms}$ period). The control pulse width $W_p$ varies between $0.5\text{ ms}$ ($0^\circ$) and $2.5\text{ ms}$ ($180^\circ$):

$$\text{Duty Cycle } (\%) = \left( \frac{W_p}{T} \right) \cdot 100 = \left( \frac{0.5\text{ ms} + \frac{\theta}{180^\circ} \cdot 2.0\text{ ms}}{20\text{ ms}} \right) \cdot 100$$

$$\text{Duty Cycle } (\%) = 2.5 + \left(\frac{\theta}{180}\right) \cdot 10.0$$

| Destination Position | Target Angle ($\theta$) | Pulse Width ($W_p$) | PWM Duty Cycle (\%) |
| :--- | :---: | :---: | :---: |
| **Neutral / Reject Tray** | $0^\circ$ | $0.50\text{ ms}$ | $2.50\%$ |
| **Bin 1 (Good Carrots)** | $30^\circ$ | $0.83\text{ ms}$ | $4.17\%$ |
| **Bin 2 (Damaged Carrots)** | $90^\circ$ | $1.50\text{ ms}$ | $7.50\%$ |
| **Bin 3 (Rotten Carrots)** | $150^\circ$ | $2.17\text{ ms}$ | $10.83\%$ |

---

## 4. Software Architecture Layers

1. **Hardware Abstraction Layer (`hardware/`)**:
   Provides uniform device control. Uses hardware `RPi.GPIO` when on Raspberry Pi OS; seamlessly falls back to `MockPWM` and virtual interrupts when running on development PCs.
2. **Vision & Preprocessing Layer (`camera/`)**:
   Captures frames via `cv2.VideoCapture` or synthetic animated conveyor generator; applies CLAHE (Contrast Limited Adaptive Histogram Equalization) on Lightness channel to remove conveyor belt shadows.
3. **Deep Learning Inference Layer (`training/predict.py`)**:
   Loads Ultralytics YOLO11 model, performs multi-scale inference, extracts bounding box tensors and class probabilities.
4. **Decision & Routing Engine (`sorting/decision_engine.py`)**:
   Applies confidence thresholding ($C_{\text{min}} = 0.50$). If $C < C_{\text{min}}$, directs object to Reject Chute. Otherwise, maps class $0 \to \text{Bin }1$, class $1 \to \text{Bin }2$, class $2 \to \text{Bin }3$.
5. **Persistence & Analytics Layer (`backend/database.py`)**:
   SQLite engine storing inspection history, classification counts, and time-stamped images.
6. **Presentation & IoT Layer (`backend/app.py` & `web_dashboard/`)**:
   Flask-powered REST API, MJPEG video feed, responsive Bootstrap 5 interface, and Chart.js telemetry graphs.
