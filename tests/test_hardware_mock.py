"""
Unit Tests for Hardware Abstraction Layer & 3-Way Sorter Actuators
==================================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System
"""

import time
import unittest
from pathlib import Path
import sys

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hardware.gpio_controller import gpio_controller
from hardware.ir_sensor import IRSensor
from hardware.conveyor_motor import ConveyorMotor
from hardware.servo_sorter import Servo3WaySorter


class TestHardwareMock(unittest.TestCase):
    """Verifies physical hardware drivers and mock simulation."""

    def test_gpio_mock_initialization(self):
        """Verifies GPIO controller boots into Mock mode without physical Pi."""
        self.assertIsNotNone(gpio_controller)
        gpio_controller.setup(21, gpio_controller.OUT, initial=gpio_controller.LOW)
        self.assertEqual(gpio_controller.input(21), gpio_controller.LOW)

        gpio_controller.output(21, gpio_controller.HIGH)
        self.assertEqual(gpio_controller.input(21), gpio_controller.HIGH)

    def test_ir_sensor_simulation_trigger(self):
        """Tests IR sensor edge detection and debouncing."""
        triggered = []

        def on_detect():
            triggered.append(True)

        sensor = IRSensor(pin=17, active_low=True, debounce_seconds=0.1)
        sensor.register_callback(on_detect)

        # Trigger simulated detection
        sensor.simulate_detection()
        time.sleep(0.05)
        self.assertTrue(len(triggered) > 0)

    def test_conveyor_motor_pwm_and_velocity(self):
        """Tests conveyor motor PWM duty cycle and velocity estimation."""
        motor = ConveyorMotor(ena_pin=18, in1_pin=27, in2_pin=22, max_velocity_mps=0.20)
        
        motor.start(speed_percent=50.0)
        self.assertTrue(motor.is_running)
        self.assertEqual(motor.current_speed_percent, 50.0)
        self.assertAlmostEqual(motor.get_velocity_mps(), 0.10, places=2)

        motor.set_speed(100.0)
        self.assertAlmostEqual(motor.get_velocity_mps(), 0.20, places=2)

        motor.stop()
        self.assertFalse(motor.is_running)
        self.assertEqual(motor.get_velocity_mps(), 0.0)

    def test_three_way_servo_sorter_angles(self):
        """
        Crucial requirement: Verifies THREE distinct physical bin positions
        plus Neutral / Reject.
        """
        sorter = Servo3WaySorter(servo_pin=12, hold_time_seconds=0.1)

        # Test duty cycle math (50Hz: 0 deg = 2.5%, 180 deg = 12.5%)
        self.assertAlmostEqual(sorter._angle_to_duty(0), 2.5, places=2)
        self.assertAlmostEqual(sorter._angle_to_duty(90), 7.5, places=2)
        self.assertAlmostEqual(sorter._angle_to_duty(180), 12.5, places=2)

        # Test Bin 1 (Good Carrots)
        sorter.test_bin_position(1)
        self.assertEqual(sorter.current_angle, sorter.ANGLE_BIN_1_GOOD)
        self.assertEqual(sorter.current_angle, 30)

        # Test Bin 2 (Damaged Carrots)
        sorter.test_bin_position(2)
        self.assertEqual(sorter.current_angle, sorter.ANGLE_BIN_2_DAMAGED)
        self.assertEqual(sorter.current_angle, 90)

        # Test Bin 3 (Rotten Carrots)
        sorter.test_bin_position(3)
        self.assertEqual(sorter.current_angle, sorter.ANGLE_BIN_3_ROTTEN)
        self.assertEqual(sorter.current_angle, 150)

        # Test Neutral / Reject
        sorter.test_bin_position(0)
        self.assertEqual(sorter.current_angle, sorter.ANGLE_REJECT_NEUTRAL)
        self.assertEqual(sorter.current_angle, 0)


if __name__ == "__main__":
    unittest.main()
