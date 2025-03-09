# boot.py
# This file runs when the ESP32 boots
import webrepl
import time
import gc

# Short pause to let system stabilize
time.sleep(1)

# Enable garbage collection
gc.enable()

# Start WebREPL
print("Starting WebREPL...")
webrepl.start()
print("WebREPL started")

print("System booted, starting motor_server...")