# Hardware Wiring and Interface Guide
## Automated Carrot Quality Detection and Sorting System Using Deep Learning, Computer Vision and IoT
**Academic Master of Engineering (M.E.) Project**

---

## 1. Pinout Connection Table (Raspberry Pi 40-Pin GPIO)

The table below specifies the exact electrical connections between the Raspberry Pi header and external sensors/actuators.

| Raspberry Pi Pin (Physical) | BCM GPIO Number | Connected Component | Component Terminal | Signal / Description |
| :---: | :---: | :--- | :--- | :--- |
| **Pin 11** | **GPIO 17** | IR Proximity Sensor | OUT / Signal | Digital Input (Active LOW on detection) |
| **Pin 12** | **GPIO 18** | L298N Motor Driver | ENA (Enable A) | Hardware PWM Output (Speed Control) |
| **Pin 13** | **GPIO 27** | L298N Motor Driver | IN1 | Direction Control (Forward Logic: HIGH) |
| **Pin 15** | **GPIO 22** | L298N Motor Driver | IN2 | Direction Control (Reverse Logic: LOW) |
| **Pin 32** | **GPIO 12** | 3-Way Servo Sorter | PWM Signal (Orange/Yellow) | 50Hz PWM Actuation (Diverter Arm) |
| **Pin 33** | **GPIO 13** | Secondary Servo Gate (Optional) | PWM Signal (Orange/Yellow) | Auxiliary Flap Gate for dual-servo setup |
| **Pin 2** / **Pin 4** | **5V DC** | IR Sensor | VCC | 5V Logic Power (Only for IR Sensor) |
| **Pin 6** / **Pin 14** / **Pin 20** | **GND** | All Subsystems | Common GND | Essential: Ties RPi GND to Power Supply GND |

> [!CAUTION]
> **Power Supply Isolation Rule:**
> NEVER power the high-torque servo motor (MG996R) or DC conveyor motor directly from the Raspberry Pi 5V rail. Inductive spikes and current surges (> 1.5A during motor stall) will reset the Pi and can permanently damage the Broadcom SoC. Use an independent external 5V/12V power supply with a common ground.

---

## 2. Power Distribution & Common Ground Architecture

```
[12V 2A DC Power Adapter]
       │
       ├───(+) 12V ───────> L298N Motor Driver (+12V terminal for DC Motor)
       │
       └───(-) 12V ───────┐
                          │
[5V 3A Step-Down / Supply]│
       │                  │
       ├───(+) 5V ────────┼───────────────────> Servo Motor VCC (Red Wire)
       │                  │
       └───(-) 5V ────────┼───────────────────> Servo Motor GND (Brown/Black Wire)
                          │
[Raspberry Pi 4 / 5]      │
       │                  │
       └─── Pin 6 (GND) ──┴──[COMMON GROUND JUNCTION]
```

### Key Wiring Notes:
1. **Common Ground:** Connect the GND of the Raspberry Pi, the GND of the L298N driver, and the GND of the external 5V servo supply together. Without a shared ground reference, PWM pulses float and cause erratic jitter.
2. **L298N 5V Jumper:** Keep the onboard 5V regulator jumper on the L298N ENABLED if powering from 12V.
3. **IR Sensor Tuning:** Rotate the onboard potentiometer on the IR module until the indicator LED turns OFF in clear air and turns ON when a carrot passes within $5\text{ cm} - 15\text{ cm}$.

---

## 3. Diverter Mechanism Assembly (Three-Way Physical Sorting)

The sorting actuator utilizes a **three-position angular diverter chute** mounted at the discharge end of the conveyor belt:

```
                  [ Conveyor Belt ===> ]
                             │
                             ▼
                     [ 3-Way Servo Arm ]
                    /        |        \
                   /         |         \
         (30° Left)    (90° Center)   (150° Right)
              │              │              │
              ▼              ▼              ▼
         [ BIN 1 ]       [ BIN 2 ]      [ BIN 3 ]
       (Good Carrots) (Damaged Carrots) (Rotten Carrots)

       [ Neutral 0° Position: Carrot bypasses to Reject / Manual Inspection ]
```

### Physical Alignment Angles:
- **Angle 30°:** Deflector arm angles 30° toward the left chute, funneling premium **Good Carrots** into Bin 1.
- **Angle 90°:** Deflector arm centers at 90°, funneling **Damaged / Cut Carrots** into Bin 2.
- **Angle 150°:** Deflector arm swings 150° toward the right chute, dumping **Rotten / Diseased Carrots** into Bin 3.
- **Angle 0° (Home / Fail-Safe):** In case of low confidence ($<50\%$) or system pause, diverter remains at 0° letting the carrot slide into the **Reject / Manual Inspection Tray**.

---

## 4. Complete Bill of Materials (BOM)

| Component | Specification / Model | Qty | Function |
| :--- | :--- | :---: | :--- |
| **SBC Controller** | Raspberry Pi 4 Model B (4GB RAM) | 1 | Runs OpenCV, Flask backend, YOLO inference & GPIO |
| **Camera** | USB 2.0 HD Webcam (1080p/720p, 30fps) | 1 | Top-down inspection over conveyor inspection station |
| **Optical Sensor** | Active-LOW Infrared Proximity Module (FC-51 / TCRT5000) | 1 | Detects carrot presence to trigger camera capture |
| **Drive Motor** | 12V DC Geared Motor (100 RPM, High Torque) | 1 | Powers conveyor belt drive pulley |
| **Motor Driver** | L298N Dual H-Bridge Module | 1 | Modulates motor speed (PWM) and direction |
| **Sorting Actuator** | MG996R High-Torque Metal Gear Servo (or SG90) | 1 | Actuates 3-position angular deflector chute |
| **Conveyor Frame** | Mini Tabletop Conveyor (500mm x 100mm) | 1 | Continuous transport mechanism |
| **Power Supply** | 12V 2A DC Adapter + LM2596 5V 3A Buck Converter | 1 | Dedicated power for motor and servo |
| **Sorting Bins** | Plastic Collection Bins (Color Coded: Green/Amber/Red) | 3 | Physical storage destinations |
