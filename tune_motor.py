from machine import Pin, PWM
from time import sleep

linMot = 25
vibeMot = 26

# Initialize PWM on GPIO 5
pwm_pin = PWM(Pin(vibeMot))
pwm_pin_off = PWM(Pin(linMot))
pwm_pin_off.freq(100)
pwm_pin_off.duty(0)

# List of 10 different PWM frequencies to test
#frequencies = [100, 150, 200, 250, 300, 350, 400, 450, 500]
frequencies = [1750, 2000, 2250, 2500]

try:
    for freq in frequencies:
        pwm_pin.freq(freq)  # Set new PWM frequency
        print(f"\nTesting PWM Frequency: {freq} Hz")

        # Ramp up speed
        for duty in range(0, 250, 10):
            pwm_pin.duty(duty)
            print(f"Frequency: {freq} Hz, Duty Cycle: {duty}")
            sleep(0.1)

        # Hold max speed
        sleep(1)

        # Ramp down speed
        for duty in range(249, -1, -10):
            pwm_pin.duty(duty)
            print(f"Frequency: {freq} Hz, Duty Cycle: {duty}")
            sleep(0.1)

        # Hold at stop before changing frequency
        sleep(1)

    print("PWM Frequency Test Complete")

except KeyboardInterrupt:
    pwm_pin.duty(0)  # Stop the motor
    pwm_pin.deinit()  # Release PWM resources
    pwm_pin_off.deinit()
    print("PWM stopped")
