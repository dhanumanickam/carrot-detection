"""
Three-Way Physical Servo Sorting Mechanism
==========================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Directs inspected carrots into THREE separate physical destination bins:
    - Bin 1: Good Carrots       (Class 0)
    - Bin 2: Damaged Carrots    (Class 1)
    - Bin 3: Rotten Carrots     (Class 2)
    - Reject Tray: Fallback route for uncertain/unclassified objects

Supports:
- 3-Position Angular Servo Diverter Arm (SG90 / MG996R)
- Optional Dual-Servo Cascade Flap Configuration
- Automatic return-to-neutral after divert cycle
"""

import time
import threading
import logging
from .gpio_controller import gpio_controller

logger = logging.getLogger("Servo_Sorter")


class Servo3WaySorter:
    """Manages 3-destination physical sorting actuator."""

    # 3-Way Diverter Angle Configuration (Degrees)
    ANGLE_BIN_1_GOOD = 30       # Diverts left chute -> Bin 1 (Good)
    ANGLE_BIN_2_DAMAGED = 90    # Center chute -> Bin 2 (Damaged)
    ANGLE_BIN_3_ROTTEN = 150    # Diverts right chute -> Bin 3 (Rotten)
    ANGLE_REJECT_NEUTRAL = 0    # Neutral bypass -> Manual Inspection / Reject Tray

    def __init__(self, servo_pin=12, secondary_pin=13, pwm_freq=50, hold_time_seconds=1.2):
        self.servo_pin = servo_pin
        self.secondary_pin = secondary_pin
        self.pwm_freq = pwm_freq
        self.hold_time_seconds = hold_time_seconds

        self.current_angle = self.ANGLE_REJECT_NEUTRAL
        self.current_bin = "Neutral / Reject"
        self.is_actuating = False
        self.lock = threading.Lock()

        self.pwm = None
        self._initialize_servo()

    def _initialize_servo(self):
        """Initializes 50Hz PWM signal on servo pin."""
        gpio_controller.setup(self.servo_pin, gpio_controller.OUT)
        self.pwm = gpio_controller.PWM(self.servo_pin, self.pwm_freq)
        self.pwm.start(self._angle_to_duty(self.ANGLE_REJECT_NEUTRAL))
        time.sleep(0.3)
        logger.info(f"3-Way Servo Sorter initialized on GPIO {self.servo_pin} at Neutral ({self.ANGLE_REJECT_NEUTRAL}°)")

    @staticmethod
    def _angle_to_duty(angle):
        """Converts angle (0-180°) to 50Hz PWM duty cycle percentage (2.5% to 12.5%)."""
        clipped = max(0.0, min(180.0, float(angle)))
        return 2.5 + (clipped / 180.0) * 10.0

    def set_angle(self, angle):
        """Drives servo to specified angle immediately."""
        duty = self._angle_to_duty(angle)
        self.current_angle = angle
        self.pwm.ChangeDutyCycle(duty)
        logger.debug(f"Servo set to {angle}° (Duty Cycle: {duty:.2f}%)")

    def sort_carrot(self, class_id, callback_on_complete=None):
        """
        Actuates diverter to the designated physical collection bin:
            class_id 0 -> Bin 1 (Good)
            class_id 1 -> Bin 2 (Damaged)
            class_id 2 -> Bin 3 (Rotten)
            otherwise  -> Reject Tray
        Runs in background thread so the conveyor and camera are non-blocking.
        """
        thread = threading.Thread(
            target=self._execute_sort_cycle,
            args=(class_id, callback_on_complete),
            daemon=True
        )
        thread.start()

    def _execute_sort_cycle(self, class_id, callback_on_complete):
        """Executes diverter movement, dwell time, and return to neutral."""
        with self.lock:
            self.is_actuating = True

            if class_id == 0:
                target_angle = self.ANGLE_BIN_1_GOOD
                bin_name = "Bin 1 (Good Carrots)"
            elif class_id == 1:
                target_angle = self.ANGLE_BIN_2_DAMAGED
                bin_name = "Bin 2 (Damaged Carrots)"
            elif class_id == 2:
                target_angle = self.ANGLE_BIN_3_ROTTEN
                bin_name = "Bin 3 (Rotten Carrots)"
            else:
                target_angle = self.ANGLE_REJECT_NEUTRAL
                bin_name = "Reject / Manual Inspection"

            self.current_bin = bin_name
            logger.info(f"[Actuation] Diverter positioning -> {target_angle}° for {bin_name}")
            self.set_angle(target_angle)

            # Hold diverter in place while the carrot travels down the chute
            time.sleep(self.hold_time_seconds)

            # Return diverter to neutral rest position
            logger.info(f"[Actuation] Returning diverter to Neutral ({self.ANGLE_REJECT_NEUTRAL}°)")
            self.set_angle(self.ANGLE_REJECT_NEUTRAL)
            time.sleep(0.2)

            self.is_actuating = False

            if callback_on_complete is not None:
                try:
                    callback_on_complete(bin_name)
                except Exception as e:
                    logger.error(f"Error executing sort completion callback: {e}")

    def test_bin_position(self, bin_number):
        """Direct test method for web dashboard hardware calibration."""
        if bin_number == 1:
            self.set_angle(self.ANGLE_BIN_1_GOOD)
            self.current_bin = "Bin 1 (Good)"
        elif bin_number == 2:
            self.set_angle(self.ANGLE_BIN_2_DAMAGED)
            self.current_bin = "Bin 2 (Damaged)"
        elif bin_number == 3:
            self.set_angle(self.ANGLE_BIN_3_ROTTEN)
            self.current_bin = "Bin 3 (Rotten)"
        else:
            self.set_angle(self.ANGLE_REJECT_NEUTRAL)
            self.current_bin = "Neutral / Reject"

        logger.info(f"Manual calibration position: {self.current_bin} ({self.current_angle}°)")

    def get_status(self):
        """Returns actuator status."""
        return {
            "current_angle": self.current_angle,
            "current_bin": self.current_bin,
            "is_actuating": self.is_actuating,
            "servo_pin": self.servo_pin
        }

    def cleanup(self):
        """Stops servo PWM."""
        if self.pwm is not None:
            self.pwm.stop()
