# motor_control.py
from machine import Pin, PWM

class DCMotor:
    """
    Class to control DC motors via L298D driver with PWM speed control
    """
    def __init__(self, enable_pin, frequency=5000, duty_min=0, duty_max=1023):
        """
        Initialize a DC motor controller
        
        Parameters:
        - enable_pin: The ESP32 GPIO pin connected to the enable pin (EN) on L298D
        - frequency: PWM frequency in Hz (default: 5000)
        """
        self.pwm = PWM(Pin(enable_pin))
        self.pwm.freq(frequency)
        self.duty_min = duty_min
        self.duty_max = duty_max
        self.speed = 0
        # Explicitly set duty to 0 to ensure motor is stopped
        self.pwm.duty(0)
    
    def set_frequency(self, frequency):
        """
        Set the PWM frequency for this motor
        
        Parameters:
        - frequency: PWM frequency in Hz
        """
        self.pwm.freq(frequency)
    
    def set_speed(self, speed):
        """
        Set the motor speed
        
        Parameters:
        - speed: Speed as percentage (0-100)
        """
        if speed == 0:
            duty_constrained = 0
        else:
            self.speed = max(0, min(100, speed))  # Constrain between 0-100
            #duty = int(self.speed * 10.23)  # Convert to 0-1023 range
            #duty_constrained = max(self.duty_min, min(self.duty_max, duty))
            duty_constrained = int(self.duty_min + ((self.speed / 100) * (self.duty_max - self.duty_min)))
        print(f"speed    -> {speed}")
        print(f"pwm.duty -> {duty_constrained}")
        self.pwm.duty(duty_constrained)
    
    def stop(self):
        """Stop the motor"""
        self.speed = 0
        self.pwm.duty(0)

class MotorController:
    """
    Control multiple DC motors with different optimal settings
    """
    def __init__(self):
        self.motors = {}
    
    def add_motor(self, name, enable_pin, frequency, duty_min=0, duty_max=1023):
        """
        Add a motor to the controller
        
        Parameters:
        - name: Identifier for the motor
        - enable_pin: The ESP32 GPIO pin connected to the enable pin (EN)
        - frequency: Optimal PWM frequency for this motor in Hz
        """
        motor = DCMotor(enable_pin, frequency, duty_min=duty_min, duty_max=duty_max)
        self.motors[name] = motor
        motor.stop()  # Ensure motor starts in stopped state
        return motor
    
    def get_motor(self, name):
        """Get a motor by name"""
        return self.motors.get(name)
    
    def set_speed(self, name, speed):
        """
        Set a motor's speed by name
        
        Parameters:
        - name: Motor identifier
        - speed: Speed as percentage (0-100)
        """
        motor = self.get_motor(name)
        if motor:
            print(f"{name} speed -> {speed}")
            motor.set_speed(speed)
    
    def stop_all(self):
        """Stop all motors"""
        for motor in self.motors.values():
            motor.stop()