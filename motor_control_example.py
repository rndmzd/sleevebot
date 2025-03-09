# main.py or your script name
from motor_control import MotorController
import time

# Create a motor controller
controller = MotorController()

# Add motors with their optimal frequencies
# Motor 1 on pin 1 with 5000Hz
controller.add_motor("motor1", 1, 5000)

# Motor 2 on pin 2 with 500Hz
controller.add_motor("motor2", 2, 500)

try:
    print("Setting both motors to 25% speed")
    controller.set_speed("motor1", 25)
    controller.set_speed("motor2", 25)
    
    # Run for 5 seconds
    time.sleep(5)
    
    print("Speeding up to 50%")
    controller.set_speed("motor1", 50)
    controller.set_speed("motor2", 50)
    
    # Run for 5 seconds
    time.sleep(5)
    
    print("Stopping motors")
    controller.stop_all()
    
except Exception as e:
    print("Error:", e)
    controller.stop_all()