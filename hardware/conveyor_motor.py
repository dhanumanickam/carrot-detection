"""
Conveyor Belt DC Geared Motor Controller (L298N Driver)
======================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Controls the conveyor belt drive motor via L298N H-Bridge:
- Variable speed control using PWM (Pulse-Width Modulation)
- Directional control (Forward / Reverse)
- Linear velocity estimation for sorting time-of-flight calculations
"""

import logging
from .gpio_controller import gpio_controller

logger = logging.getLogger("Conveyor_Motor")


class ConveyorMotor:
    """Controls DC conveyor motor speed and state through L298N driver."""

    def __init__(self, ena_pin=18, in1_pin=27, in2_pin=22, pwm_freq=1000, max_velocity_mps=0.20):
        self.ena_pin = ena_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.pwm_freq = pwm_freq
        self.max_velocity_mps = max_velocity_mps  # Linear speed at 100% duty cycle (0.20 m/s = 20 cm/s)

        self.is_running = False
        self.current_speed_percent = 70.0 # Default optimal 70% speed
        self.direction = "FORWARD"
        self.pwm = None

        self._initialize_pins()

    def _initialize_pins(self):
        """Sets up GPIO pins for L298N."""
        gpio_controller.setup(self.in1_pin, gpio_controller.OUT, initial=gpio_controller.LOW)
        gpio_controller.setup(self.in2_pin, gpio_controller.OUT, initial=gpio_controller.LOW)
        gpio_controller.setup(self.ena_pin, gpio_controller.OUT)

        self.pwm = gpio_controller.PWM(self.ena_pin, self.pwm_freq)
        self.pwm.start(0)
        logger.info(f"Conveyor Motor initialized: ENA={self.ena_pin}, IN1={self.in1_pin}, IN2={self.in2_pin}")

    def start(self, speed_percent=None):
        """Starts conveyor belt motor forward at specified or default speed."""
        if speed_percent is not None:
            self.current_speed_percent = max(0.0, min(100.0, float(speed_percent)))

        # Forward rotation
        gpio_controller.output(self.in1_pin, gpio_controller.HIGH)
        gpio_controller.output(self.in2_pin, gpio_controller.LOW)
        self.pwm.ChangeDutyCycle(self.current_speed_percent)

        self.is_running = True
        self.direction = "FORWARD"
        logger.info(f"Conveyor started: Speed = {self.current_speed_percent}% ({self.get_velocity_mps():.2f} m/s)")

    def set_speed(self, speed_percent):
        """Updates motor speed (0 - 100%)."""
        self.current_speed_percent = max(0.0, min(100.0, float(speed_percent)))
        if self.is_running:
            self.pwm.ChangeDutyCycle(self.current_speed_percent)
            logger.info(f"Conveyor speed adjusted to {self.current_speed_percent}%")

    def stop(self):
        """Stops conveyor belt motor."""
        gpio_controller.output(self.in1_pin, gpio_controller.LOW)
        gpio_controller.output(self.in2_pin, gpio_controller.LOW)
        self.pwm.ChangeDutyCycle(0)
        self.is_running = False
        logger.info("Conveyor belt motor stopped.")

    def reverse(self, speed_percent=None):
        """Reverses conveyor direction."""
        if speed_percent is not None:
            self.current_speed_percent = max(0.0, min(100.0, float(speed_percent)))
        
        gpio_controller.output(self.in1_pin, gpio_controller.LOW)
        gpio_controller.output(self.in2_pin, gpio_controller.HIGH)
        self.pwm.ChangeDutyCycle(self.current_speed_percent)
        self.is_running = True
        self.direction = "REVERSE"
        logger.info(f"Conveyor running in REVERSE: {self.current_speed_percent}%")

    def get_velocity_mps(self):
        """
        Estimates linear belt velocity in meters per second.
        Used to compute travel delay from camera to diverter gate.
        """
        if not self.is_running:
            return 0.0
        return (self.current_speed_percent / 100.0) * self.max_velocity_mps

    def get_status(self):
        """Returns motor telemetry dictionary."""
        return {
            "is_running": self.is_running,
            "speed_percent": self.current_speed_percent,
            "velocity_mps": round(self.get_velocity_mps(), 3),
            "direction": self.direction
        }
