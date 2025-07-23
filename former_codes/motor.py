from gpiozero import PWMOutputDevice
import requests
import time
import lgpio as GPIO

# === Motor GPIO setup ===
ENA = PWMOutputDevice(12)
ENB = PWMOutputDevice(13)
IN1 = PWMOutputDevice(17)
IN2 = PWMOutputDevice(27)
IN3 = PWMOutputDevice(22)
IN4 = PWMOutputDevice(23)

DEFAULT_SPEED = 0.5
TURN_SPEED = 0.7

ENA.value = DEFAULT_SPEED
ENB.value = DEFAULT_SPEED

def set_motor(lf, lb, rf, rb):
    IN1.value = lf
    IN2.value = lb
    IN3.value = rf
    IN4.value = rb

def control_motors(command):
    command = command.lower()
    print(f"[ACTION] Executing: {command}")
    if command == "forward":
        set_motor(0, DEFAULT_SPEED, DEFAULT_SPEED, 0)
    elif command == "backward":
        set_motor(DEFAULT_SPEED, 0, 0, DEFAULT_SPEED)
    elif command == "left":
        set_motor(0, TURN_SPEED, 0, 0)
        time.sleep(0.91)
        set_motor(0, 0, 0, 0)
    elif command == "reverse-left":
        set_motor(TURN_SPEED, 0, 0, 0)
        time.sleep(0.91)
        set_motor(0, 0, 0, 0)
    elif command == "right":
        set_motor(0, 0, TURN_SPEED, 0)
        time.sleep(0.91)
        set_motor(0, 0, 0, 0)
    elif command == "reverse-right":
        set_motor(0, 0, 0, TURN_SPEED)
        time.sleep(0.91)
        set_motor(0, 0, 0, 0)
    elif command == "u-turn":
        set_motor(TURN_SPEED, 0, TURN_SPEED, 0)
        time.sleep(1.8)
        set_motor(0, 0, 0, 0)
    elif command == "stop":
        set_motor(0, 0, 0, 0)
    else:
        print(f"[WARNING] Unknown command: {command}")
        set_motor(0, 0, 0, 0)

# === Firebase functions ===
FIREBASE_URL = "https://jil-3000-default-rtdb.firebaseio.com/control.json"

def get_command():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Unexpected status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Firebase error: {e}")
        return None

def send_stop_to_firebase():
    try:
        requests.put(FIREBASE_URL, json="stop")
        print("[SYNC] Sent 'stop' to Firebase")
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Could not send stop: {e}")

# === Ultrasonic sensor setup ===
TRIG = 5
ECHO = 6
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

def get_distance():
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(0.05)
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    GPIO.gpio_write(h, TRIG, 0)

    timeout = time.time() + 1
    while GPIO.gpio_read(h, ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None

    timeout = time.time() + 1
    while GPIO.gpio_read(h, ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None

    pulse_duration = pulse_end - pulse_start
    return round(pulse_duration * 17150, 2)

# === Main loop ===
last_command = None
last_active_command = None
obstacle_mode = False

try:
    print("🚀 Robot started with obstacle auto-stop/resume. Press Ctrl+C to exit.")
    while True:
        distance = get_distance()
        if distance and distance < 20.0:
            if not obstacle_mode:
                print(f"🧱 Obstacle at {distance:.2f} cm. Stopping.")
                if last_command != "stop":
                    last_active_command = last_command
                    control_motors("stop")
                    send_stop_to_firebase()
                    last_command = "stop"
                obstacle_mode = True
            time.sleep(0.2)
            continue
        elif obstacle_mode:
            # Obstacle just cleared
            if last_active_command and last_active_command != "stop":
                print(f"✅ Obstacle cleared. Resuming: {last_active_command}")
                control_motors(last_active_command)
                last_command = last_active_command
            obstacle_mode = False

        command = get_command()
        if command and command != last_command and not obstacle_mode:
            print(f"[COMMAND] {command}")
            control_motors(command)
            last_command = command
            if command != "stop":
                last_active_command = command

        time.sleep(0.1)

except KeyboardInterrupt:
    print("🛑 Exiting...")
finally:
    set_motor(0, 0, 0, 0)
    GPIO.gpiochip_close(h)
