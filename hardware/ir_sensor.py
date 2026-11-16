"""
Infrared (IR) Optical Proximity Sensor Driver
=============================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Monitors the conveyor belt entrance. When a carrot interrupts the infrared beam,
signals the Raspberry Pi to trigger camera image capture and quality inference.
"""

import time
import logging
from .gpio_controller import gpio_controller

logger = logging.getLogger("IR_Sensor")


class IRSensor:
    """Manages IR obstacle/break-beam sensor with hardware interrupts and software debouncing."""

    def __init__(self, pin=17, active_low=True, debounce_seconds=1.5):
        self.pin = pin
        self.active_low = active_low
        self.debounce_seconds = debounce_seconds
        
        self._last_trigger_time = 0.0
        self._callback = None

        self._setup_sensor()

    def _setup_sensor(self):
        """Initializes GPIO pin and interrupt handler."""
        gpio_controller.setup(self.pin, gpio_controller.IN)
        # Register interrupt: FALLING edge if active low (detection causes 0V), else RISING
        edge = gpio_controller.FALLING if self.active_low else gpio_controller.RISING
        gpio_controller.add_event_detect(
            self.pin,
            edge=edge,
            callback=self._handle_interrupt,
            bouncetime=int(self.debounce_seconds * 1000)
        )
        logger.info(f"IR Sensor initialized on BCM GPIO Pin {self.pin} (Active Low: {self.active_low})")

    def register_callback(self, callback_func):
        """Attaches external handler to be invoked when a carrot is detected."""
        self._callback = callback_func

    def _handle_interrupt(self, channel=None):
        """Internal debounced interrupt handler."""
        now = time.time()
        if now - self._last_trigger_time < self.debounce_seconds:
            return # Debounced

        self._last_trigger_time = now
        logger.info(f"Carrot detected by IR Sensor on Pin {self.pin}!")
        if self._callback is not None:
            try:
                self._callback()
            except Exception as e:
                logger.error(f"Error executing IR detection callback: {e}")

    def is_object_present(self):
        """Polls current real-time sensor state."""
        state = gpio_controller.input(self.pin)
        return state == gpio_controller.LOW if self.active_low else state == gpio_controller.HIGH

    def simulate_detection(self):
        """Programmatic trigger for simulation / UI manual trigger."""
        logger.info("[IR Simulation] Simulated carrot passage triggered.")
        self._handle_interrupt(self.pin)
