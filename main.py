# main.py
# This file runs automatically after boot.py
import motor_server
import time
from machine import Pin

# Blink LED to indicate startup
status_led = Pin(2, Pin.OUT)
for _ in range(3):
    status_led.value(1)
    time.sleep(0.2)
    status_led.value(0)
    time.sleep(0.2)

print("Starting motor server with motors STOPPED...")

# Start the motor server
motor_server.main()