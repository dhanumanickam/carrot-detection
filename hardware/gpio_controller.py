"""
Hardware GPIO Abstraction Layer with Auto-Simulation
====================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Provides a unified interface for Raspberry Pi GPIO pins.
Automatically enters Simulation Mode when running on non-RPi systems
(Windows, macOS, Linux PC) without crashing or requiring hardware.
"""

import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GPIO_Controller")


class GPIOController:
    """Manages physical and simulated GPIO pins on Raspberry Pi."""

    # Pin numbering modes
    BCM = "BCM"
    BOARD = "BOARD"

    # Pin directions
    IN = "IN"
    OUT = "OUT"

    # Edge detection
    RISING = "RISING"
    FALLING = "FALLING"
    BOTH = "BOTH"

    # Pin states
    HIGH = 1
    LOW = 0

    def __init__(self, mode=BCM):
        self.mode = mode
        self.is_raspberry_pi = False
        self.rpi_gpio = None
        self._mock_pin_states = {}
        self._mock_pwm_instances = {}
        self._callbacks = {}

        self._detect_hardware()

    def _detect_hardware(self):
        """Checks if RPi.GPIO or gpiozero is accessible on Raspberry Pi."""
        try:
            import RPi.GPIO as GPIO
            self.rpi_gpio = GPIO
            self.rpi_gpio.setmode(self.rpi_gpio.BCM if self.mode == self.BCM else self.rpi_gpio.BOARD)
            self.rpi_gpio.setwarnings(False)
            self.is_raspberry_pi = True
            logger.info("Physical Raspberry Pi GPIO subsystem initialized successfully.")
        except (ImportError, RuntimeError):
            self.is_raspberry_pi = False
            self.rpi_gpio = None
            logger.info("Running in SIMULATION MODE (Non-Raspberry Pi / Development Host).")

    def setup(self, pin, direction, pull_up_down=None, initial=LOW):
        """Configures a GPIO pin."""
        self._mock_pin_states[pin] = initial
        if self.is_raspberry_pi and self.rpi_gpio is not None:
            if pull_up_down is not None:
                self.rpi_gpio.setup(pin, self.rpi_gpio.IN if direction == self.IN else self.rpi_gpio.OUT,
                                    pull_up_down=pull_up_down)
            else:
                self.rpi_gpio.setup(pin, self.rpi_gpio.IN if direction == self.IN else self.rpi_gpio.OUT,
                                    initial=initial)
        else:
            logger.debug(f"[Mock GPIO] Pin {pin} configured as {direction} (Initial: {initial})")

    def output(self, pin, state):
        """Sets pin output state (HIGH or LOW)."""
        self._mock_pin_states[pin] = state
        if self.is_raspberry_pi and self.rpi_gpio is not None:
            self.rpi_gpio.output(pin, state)
        else:
            logger.debug(f"[Mock GPIO] Pin {pin} -> {'HIGH' if state else 'LOW'}")

    def input(self, pin):
        """Reads pin state."""
        if self.is_raspberry_pi and self.rpi_gpio is not None:
            return self.rpi_gpio.input(pin)
        return self._mock_pin_states.get(pin, self.LOW)

    def PWM(self, pin, frequency_hz):
        """Creates a PWM instance for motor speed or servo position control."""
        if self.is_raspberry_pi and self.rpi_gpio is not None:
            return self.rpi_gpio.PWM(pin, frequency_hz)
        else:
            mock_pwm = MockPWM(pin, frequency_hz)
            self._mock_pwm_instances[pin] = mock_pwm
            return mock_pwm

    def add_event_detect(self, pin, edge, callback=None, bouncetime=200):
        """Attaches edge-detection interrupt or callback."""
        self._callbacks[pin] = callback
        if self.is_raspberry_pi and self.rpi_gpio is not None:
            rpi_edge = self.rpi_gpio.RISING if edge == self.RISING else (
                self.rpi_gpio.FALLING if edge == self.FALLING else self.rpi_gpio.BOTH
            )
            self.rpi_gpio.add_event_detect(pin, rpi_edge, callback=callback, bouncetime=bouncetime)
        else:
            logger.debug(f"[Mock GPIO] Edge interrupt callback registered on pin {pin} ({edge})")

    def simulate_pin_trigger(self, pin, state=LOW):
        """Utility for test suites and web dashboard to simulate physical sensor trigger."""
        self._mock_pin_states[pin] = state
        if pin in self._callbacks and self._callbacks[pin] is not None:
            logger.info(f"[Mock Trigger] Firing simulated interrupt callback for pin {pin}")
            self._callbacks[pin](pin)

    def cleanup(self):
        """Releases GPIO resources."""
        if self.is_raspberry_pi and self.rpi_gpio is not None:
            self.rpi_gpio.cleanup()
        self._mock_pin_states.clear()
        self._mock_pwm_instances.clear()
        logger.info("GPIO cleanup finished.")


class MockPWM:
    """Mock PWM controller for development systems."""

    def __init__(self, pin, frequency_hz):
        self.pin = pin
        self.frequency = frequency_hz
        self.duty_cycle = 0.0
        self.is_active = False

    def start(self, duty_cycle):
        self.duty_cycle = duty_cycle
        self.is_active = True
        logger.debug(f"[Mock PWM Pin {self.pin}] Started at {self.duty_cycle}% duty cycle @ {self.frequency}Hz")

    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        logger.debug(f"[Mock PWM Pin {self.pin}] Changed duty cycle -> {self.duty_cycle:.2f}%")

    def ChangeFrequency(self, frequency_hz):
        self.frequency = frequency_hz

    def stop(self):
        self.is_active = False
        logger.debug(f"[Mock PWM Pin {self.pin}] Stopped.")


# Global Singleton instance
gpio_controller = GPIOController()
