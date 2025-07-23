import lgpio as GPIO
import time

TRIG = 5   # BCM GPIO 5 (physical pin 29)
ECHO = 6   # BCM GPIO 6 (physical pin 31)

h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

def get_distance():
    pulse_start = None
    pulse_end = None

    # Ensure TRIG is low
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(0.05)

    # Send 10us trigger pulse
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    GPIO.gpio_write(h, TRIG, 0)

    # Wait for ECHO to go high
    timeout = time.time() + 1
    while GPIO.gpio_read(h, ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            print("⚠️ Timeout waiting for ECHO to go high")
            return None

    # Wait for ECHO to go low
    timeout = time.time() + 1
    while GPIO.gpio_read(h, ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            print("⚠️ Timeout waiting for ECHO to go low")
            return None

    pulse_duration = pulse_end - pulse_start
    distance_cm = pulse_duration * 17150  # Speed of sound / 2 in cm/us

    return round(distance_cm, 2)

try:
    while True:
        distance = get_distance()
        if distance is not None:
            print(f"📏 Distance: {distance} cm")
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Measurement stopped.")
    GPIO.gpiochip_close(h)
