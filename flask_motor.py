from flask import Flask, request, jsonify # WORKS FOR CONTROL...
import time
import os
from gpiozero import PWMOutputDevice, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Use LGPIOFactory for GPIO access
Device.pin_factory = LGPIOFactory()

app = Flask(__name__)

# Initialize GPIO pins (BCM numbering)
try:
    ENA = PWMOutputDevice(12)  # GPIO12
    ENB = PWMOutputDevice(13)  # GPIO13
    IN1 = PWMOutputDevice(17)  # GPIO17
    IN2 = PWMOutputDevice(27)  # GPIO27
    IN3 = PWMOutputDevice(22)  # GPIO22
    IN4 = PWMOutputDevice(23)  # GPIO23
except Exception as e:
    with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
        f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] GPIO Init Error: {e}\n")
    raise

# Speed Parameters
DEFAULT_SPEED = 0.5
DEFAULT_TURN_SPEED = 0.4
CURRENT_SPEED = DEFAULT_SPEED
TURN_SPEED = DEFAULT_TURN_SPEED

ENA.value = CURRENT_SPEED
ENB.value = CURRENT_SPEED

def set_motor(lf, lb, rf, rb):
    IN1.value = lf
    IN2.value = lb
    IN3.value = rf
    IN4.value = rb 

def control_motors(command):
    print(f"[ACTION] Executing: {command}")
    with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
        f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Command: {command}\n")
    if command == "left":
        set_motor(0, TURN_SPEED, TURN_SPEED, 0)
    elif command == "right":
        set_motor(TURN_SPEED, 0, 0, TURN_SPEED)
    elif command == "backward":
        set_motor(0, CURRENT_SPEED, 0, CURRENT_SPEED)
    elif command == "forward":
        set_motor(CURRENT_SPEED, 0, CURRENT_SPEED, 0)
    elif command == "stop":
        set_motor(0, 0, 0, 0)
    else:
        print("[WARNING] Unknown command.")
        set_motor(0, 0, 0, 0)

@app.route("/", methods=["GET"])
def index():
    return HTML

@app.route("/control", methods=["POST"])
def control():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"error": "Missing command"}), 400
    try:
        control_motors(data['command'])
        return jsonify({"status": f"Command '{data['command']}' executed."})
    except Exception as e:
        with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
            f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Control Error: {e}\n")
        return jsonify({"error": str(e)}), 500

@app.route("/speed", methods=["POST"])
def set_speed():
    global CURRENT_SPEED
    data = request.get_json()
    try:
        new_speed = float(data.get('speed', 5))
        if not (1 <= new_speed <= 10):
            raise ValueError("Speed must be between 1 and 10")
        CURRENT_SPEED = new_speed / 10.0
        ENA.value = CURRENT_SPEED
        ENB.value = CURRENT_SPEED
        with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
            f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Linear speed set to {CURRENT_SPEED:.1f}\n")
        return jsonify({"status": f"Linear speed set to {CURRENT_SPEED:.1f}"})
    except Exception as e:
        with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
            f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Speed Error: {e}\n")
        return jsonify({"error": str(e)}), 400

@app.route("/turn_speed", methods=["POST"])
def set_turn_speed():
    global TURN_SPEED
    data = request.get_json()
    try:
        new_turn_speed = float(data.get('speed', 4))
        if not (1 <= new_turn_speed <= 10):
            raise ValueError("Turn speed must be between 1 and 10")
        TURN_SPEED = new_turn_speed / 10.0
        with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
            f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Turn speed set to {TURN_SPEED:.1f}\n")
        return jsonify({"status": f"Turn speed set to {TURN_SPEED:.1f}"})
    except Exception as e:
        with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
            f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Turn Speed Error: {e}\n")
        return jsonify({"error": str(e)}), 400

@app.route("/shutdown", methods=["POST"])
def shutdown():
    try:
        with open("/tmp/kill_slam", "w") as f:
            f.write("exit")
        set_motor(0, 0, 0, 0)  # Stop motors
        return jsonify({"status": "Kill signal written"})
    except Exception as e:
        with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
            f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Shutdown Error: {e}\n")
        return jsonify({"error": str(e)}), 500

@app.route("/log", methods=["POST"])
def log_location():
    data = request.get_json()
    label = data.get("label", "").strip()
    if not label:
        return jsonify({"error": "Label is required"}), 400
    pose_path = "/tmp/latest_pose.txt"
    log_path = "/home/jay/dev/ORB_SLAM3/Maps/manual_log.txt"
    try:
        with open(pose_path, "r") as f:
            pose = f.read().strip()
        timestamp = time.strftime("%m%d%Y%H%M%S")
        with open(log_path, "a") as log:
            log.write(f"== [{timestamp}] ==\n")
            log.write(f"Manual Label: {label}\n")
            log.write(f"Pose: {pose}\n\n")
        return jsonify({"status": f"Pose logged with label '{label}'"})
    except Exception as e:
        return jsonify({"error": f"Logging failed: {e}"}), 500

# Minimal HTML Interface
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Robot Control</title>
    <style>
        body { text-align: center; font-family: Arial; }
        button { width: 80px; height: 80px; margin: 10px; font-size: 20px; }
        input[type=range] { width: 300px; }
    </style>
</head>
<body>
    <h2>🕹️ Robot Control Panel</h2>
    <div>
        <button onclick="send('forward')">↑</button><br>
        <button onclick="send('left')">←</button>
        <button onclick="send('stop')">⛔</button>
        <button onclick="send('right')">→</button><br>
        <button onclick="send('backward')">↓</button>
    </div>
    <div style="margin: 20px;">
        <h3>Linear Speed: <span id="speedVal">5</span></h3>
        <input type="range" min="1" max="10" value="5" id="speedSlider" oninput="updateSpeed(this.value)">
    </div>
    <div style="margin: 20px;">
        <h3>Turn Speed: <span id="turnSpeedVal">4</span></h3>
        <input type="range" min="1" max="10" value="4" id="turnSpeedSlider" oninput="updateTurnSpeed(this.value)">
    </div>
    <hr>
    <div style="margin: 20px;">
        <h3>📍 Manual Location Label</h3>
        <input type="text" id="manualLabel" placeholder="e.g., Room 3A" style="padding:8px; width: 250px;">
        <button onclick="logLabel()">Log Location</button>
    </div>
    <button onclick="shutdownSLAM()">🛑 Quit SLAM</button>
    <script>
        function logLabel() {
            const label = document.getElementById("manualLabel").value.trim();
            if (!label) {
                alert("Please enter a label.");
                return;
            }
            fetch("/log", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ label: label })
            })
            .then(res => res.json())
            .then(data => alert(data.status || data.error))
            .catch(err => alert("Log failed: " + err));
        }
        function shutdownSLAM() {
            fetch("/shutdown", { method: "POST" })
            .then(res => res.json())
            .then(data => alert(data.status || data.error))
            .catch(err => alert("Shutdown failed: " + err));
        }
        function send(cmd) {
            fetch("/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: cmd })
            }).then(res => res.json())
            .then(data => console.log("[CONTROL]", cmd))
            .catch(err => alert("Command failed: " + err));
        }
        function updateSpeed(val) {
            document.getElementById("speedVal").innerText = val;
            fetch("/speed", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ speed: val })
            });
        }
        function updateTurnSpeed(val) {
            document.getElementById("turnSpeedVal").innerText = val;
            fetch("/turn_speed", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ speed: val })
            });
        }
        document.addEventListener("keydown", function(event) {
            switch (event.key) {
                case "ArrowUp": case "w": case "W": send("forward"); break;
                case "ArrowDown": case "x": case "X": send("backward"); break;
                case "ArrowLeft": case "a": case "A": send("left"); break;
                case "ArrowRight": case "d": case "D": send("right"); break;
                case "s": case "S": case " ": send("stop"); break;
            }
        });
        document.addEventListener("keyup", function(event) {
            switch (event.key) {
                case "ArrowUp": case "ArrowDown": case "ArrowLeft": case "ArrowRight":
                case "w": case "W": case "x": case "X": case "a": case "A": case "d": case "D":
                    send("stop"); break;
            }
        });
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


# from flask import Flask, request, jsonify
# import time
# import os
# from gpiozero import PWMOutputDevice, Device
# from gpiozero.pins.lgpio import LGPIOFactory

# # Use LGPIOFactory for GPIO access
# Device.pin_factory = LGPIOFactory()

# app = Flask(__name__)

# # Initialize GPIO pins (BCM numbering)
# try:
#     # Define motor pins
#     ENA = PWMOutputDevice(12)  # GPIO12
#     ENB = PWMOutputDevice(13)  # GPIO13
#     IN1 = PWMOutputDevice(17)  # GPIO17
#     IN2 = PWMOutputDevice(27)  # GPIO27
#     IN3 = PWMOutputDevice(22)  # GPIO22
#     IN4 = PWMOutputDevice(23)  # GPIO23
# except Exception as e:
#     with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
#         f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] GPIO Init Error: {e}\n")
#     raise

# # Speed Parameters
# DEFAULT_SPEED = 0.5
# DEFAULT_TURN_SPEED = 0.4
# CURRENT_SPEED = DEFAULT_SPEED
# TURN_SPEED = DEFAULT_TURN_SPEED

# ENA.value = CURRENT_SPEED
# ENB.value = CURRENT_SPEED

# def set_motor(lf, lb, rf, rb):
#     IN1.value = lf
#     IN2.value = lb
#     IN3.value = rf
#     IN4.value = rb 

# def control_motors(command):
#     print(f"[ACTION] Executing: {command}")
#     with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
#         f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Command: {command}\n")
#     if command == "left":
#         set_motor(0, TURN_SPEED, TURN_SPEED, 0)
#     elif command == "right":
#         set_motor(TURN_SPEED, 0, 0, TURN_SPEED)
#     elif command == "backward":
#         set_motor(0, CURRENT_SPEED, 0, CURRENT_SPEED)
#     elif command == "forward":
#         set_motor(CURRENT_SPEED, 0, CURRENT_SPEED, 0)
#     elif command == "stop":
#         set_motor(0, 0, 0, 0)
#     else:
#         print("[WARNING] Unknown command.")
#         set_motor(0, 0, 0, 0)

# # HTML Frontend
# HTML = '''
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Robot Control</title>
#     <style>
#         body { text-align: center; font-family: Arial; }
#         button { width: 80px; height: 80px; margin: 10px; font-size: 20px; }
#         input[type=range] { width: 300px; }
#     </style>
# </head>
# <body>
#     <h2>🕹️ Robot Control Panel</h2>
#     <div>
#         <button onclick="send('forward')">↑</button><br>
#         <button onclick="send('left')">←</button>
#         <button onclick="send('stop')">⛔</button>
#         <button onclick="send('right')">→</button><br>
#         <button onclick="send('backward')">↓</button>
#     </div>
#     <div style="margin: 20px;">
#         <h3>Linear Speed: <span id="speedVal">5</span></h3>
#         <input type="range" min="1" max="10" value="5" id="speedSlider" oninput="updateSpeed(this.value)">
#     </div>
#     <div style="margin: 20px;">
#         <h3>Turn Speed: <span id="turnSpeedVal">4</span></h3>
#         <input type="range" min="1" max="10" value="4" id="turnSpeedSlider" oninput="updateTurnSpeed(this.value)">
#     </div>
#     <hr>
#     <div style="margin: 20px;">
#         <h3>📍 Manual Location Label</h3>
#         <input type="text" id="manualLabel" placeholder="e.g., Room 3A" style="padding:8px; width: 250px;">
#         <button onclick="logLabel()">Log Location</button>
#     </div>
#     <button onclick="shutdownSLAM()">🛑 Quit SLAM</button>
#     <script>
#         function logLabel() {
#             const label = document.getElementById("manualLabel").value.trim();
#             if (!label) {
#                 alert("Please enter a label.");
#                 return;
#             }
#             fetch("/log", {
#                 method: "POST",
#                 headers: { "Content-Type": "application/json" },
#                 body: JSON.stringify({ label: label })
#             })
#             .then(res => res.json())
#             .then(data => alert(data.status || data.error))
#             .catch(err => alert("Log failed: " + err));
#         }
#         function shutdownSLAM() {
#             fetch("/shutdown", { method: "POST" })
#             .then(res => res.json())
#             .then(data => alert(data.status || data.error))
#             .catch(err => alert("Shutdown failed: " + err));
#         }
#         function send(cmd) {
#             fetch("/control", {
#                 method: "POST",
#                 headers: { "Content-Type": "application/json" },
#                 body: JSON.stringify({ command: cmd })
#             }).then(res => res.json())
#             .then(data => console.log("[CONTROL]", cmd))
#             .catch(err => alert("Command failed: " + err));
#         }
#         function updateSpeed(val) {
#             document.getElementById("speedVal").innerText = val;
#             fetch("/speed", {
#                 method: "POST",
#                 headers: { "Content-Type": "application/json" },
#                 body: JSON.stringify({ speed: val })
#             }).then(res => res.json())
#             .then(data => console.log(data))
#             .catch(err => alert("Speed update failed: " + err));
#         }
#         function updateTurnSpeed(val) {
#             document.getElementById("turnSpeedVal").innerText = val;
#             fetch("/turn_speed", {
#                 method: "POST",
#                 headers: { "Content-Type": "application/json" },
#                 body: JSON.stringify({ speed: val })
#             }).then(res => res.json())
#             .then(data => console.log(data))
#             .catch(err => alert("Turn speed update failed: " + err));
#         }
#         document.addEventListener("keydown", function(event) {
#             switch (event.key) {
#                 case "ArrowUp": case "w": case "W": send("forward"); break;
#                 case "ArrowDown": case "x": case "X": send("backward"); break;
#                 case "ArrowLeft": case "a": case "A": send("left"); break;
#                 case "ArrowRight": case "d": case "D": send("right"); break;
#                 case "s": case "S": case " ": send("stop"); break;
#             }
#         });
#         document.addEventListener("keyup", function(event) {
#             switch (event.key) {
#                 case "ArrowUp": case "ArrowDown": case "ArrowLeft": case "ArrowRight":
#                 case "w": case "W": case "x": case "X": case "a": case "A": case "d": case "D":
#                     send("stop"); break;
#             }
#         });
#     </script>
# </body>
# </html>
# '''

# # Flask Routes
# @app.route("/", methods=["GET"])
# def index():
#     return HTML

# @app.route("/control", methods=["POST"])
# def control():
#     data = request.get_json()
#     if not data or 'command' not in data:
#         return jsonify({"error": "Missing command"}), 400
#     try:
#         control_motors(data['command'])
#         return jsonify({"status": f"Command '{data['command']}' executed."})
#     except Exception as e:
#         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
#             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Control Error: {e}\n")
#         return jsonify({"error": str(e)}), 500

# @app.route("/speed", methods=["POST"])
# def set_speed():
#     global CURRENT_SPEED
#     data = request.get_json()
#     try:
#         new_speed = float(data.get('speed', 5))
#         if not (1 <= new_speed <= 10):
#             raise ValueError("Speed must be between 1 and 10")
#         CURRENT_SPEED = new_speed / 10.0
#         ENA.value = CURRENT_SPEED
#         ENB.value = CURRENT_SPEED
#         with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
#             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Linear speed set to {CURRENT_SPEED:.1f}\n")
#         return jsonify({"status": f"Linear speed set to {CURRENT_SPEED:.1f}"})
#     except Exception as e:
#         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
#             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Speed Error: {e}\n")
#         return jsonify({"error": str(e)}), 400

# @app.route("/turn_speed", methods=["POST"])
# def set_turn_speed():
#     global TURN_SPEED
#     data = request.get_json()
#     try:
#         new_turn_speed = float(data.get('speed', 4))
#         if not (1 <= new_turn_speed <= 10):
#             raise ValueError("Turn speed must be between 1 and 10")
#         TURN_SPEED = new_turn_speed / 10.0
#         with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
#             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Turn speed set to {TURN_SPEED:.1f}\n")
#         return jsonify({"status": f"Turn speed set to {TURN_SPEED:.1f}"})
#     except Exception as e:
#         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
#             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Turn Speed Error: {e}\n")
#         return jsonify({"error": str(e)}), 400

# @app.route("/shutdown", methods=["POST"])
# def shutdown():
#     try:
#         with open("/tmp/kill_slam", "w") as f:
#             f.write("exit")
#         set_motor(0, 0, 0, 0)  # Stop motors
#         return jsonify({"status": "Kill signal written"})
#     except Exception as e:
#         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
#             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Shutdown Error: {e}\n")
#         return jsonify({"error": str(e)}), 500

# @app.route("/log", methods=["POST"])
# def log_location():
#     data = request.get_json()
#     label = data.get("label", "").strip()
#     if not label:
#         return jsonify({"error": "Label is required"}), 400
#     pose_path = "/tmp/latest_pose.txt"
#     log_path = "/home/jay/dev/ORB_SLAM3/Maps/manual_log.txt"
#     try:
#         with open(pose_path, "r") as f:
#             pose = f.read().strip()
#         timestamp = time.strftime("%m%d%Y%H%M%S")
#         with open(log_path, "a") as log:
#             log.write(f"== [{timestamp}] ==\n")
#             log.write(f"Manual Label: {label}\n")
#             log.write(f"Pose: {pose}\n\n")
#         return jsonify({"status": f"Label '{label}' logged with pose"})
#     except Exception as e:
#         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
#             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Log Error: {e}\n")
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

# # from flask import Flask, request, jsonify
# # import time
# # import os
# # import lgpio
# # from gpiozero import PWMOutputDevice, Device
# # from gpiozero.pins.lgpio import LGPIOFactory

# # # Use LGPIOFactory for GPIO access
# # Device.pin_factory = LGPIOFactory()

# # app = Flask(__name__)

# # # Initialize GPIO pins (BOARD numbering)
# # try:
# #     # Free GPIO pins
# #     h = lgpio.gpiochip_open(0)
# #     for pin in [32, 33, 11, 13, 15, 16]:  # BOARD: 32=GPIO12, 33=GPIO13, 11=GPIO17, 13=GPIO27, 15=GPIO22, 16=GPIO23
# #         lgpio.gpio_free(h, pin)
# #     lgpio.gpiochip_close(h)
# #     ENA = PWMOutputDevice(32)  # BOARD32 = GPIO12
# #     ENB = PWMOutputDevice(33)  # BOARD33 = GPIO13
# #     IN1 = PWMOutputDevice(11)  # BOARD11 = GPIO17
# #     IN2 = PWMOutputDevice(13)  # BOARD13 = GPIO27
# #     IN3 = PWMOutputDevice(15)  # BOARD15 = GPIO22
# #     IN4 = PWMOutputDevice(16)  # BOARD16 = GPIO23
# # except Exception as e:
# #     with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
# #         f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] GPIO Init Error: {e}\n")
# #     raise

# # # Speed Parameters
# # DEFAULT_SPEED = 0.5
# # DEFAULT_TURN_SPEED = 0.4
# # CURRENT_SPEED = DEFAULT_SPEED
# # TURN_SPEED = DEFAULT_TURN_SPEED

# # ENA.value = CURRENT_SPEED
# # ENB.value = CURRENT_SPEED

# # def set_motor(lf, lb, rf, rb):
# #     IN1.value = lf
# #     IN2.value = lb
# #     IN3.value = rf
# #     IN4.value = rb 

# # def control_motors(command):
# #     print(f"[ACTION] Executing: {command}")
# #     with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
# #         f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Command: {command}\n")
# #     if command == "left":
# #         set_motor(0, TURN_SPEED, TURN_SPEED, 0)
# #     elif command == "right":
# #         set_motor(TURN_SPEED, 0, 0, TURN_SPEED)
# #     elif command == "backward":
# #         set_motor(0, CURRENT_SPEED, 0, CURRENT_SPEED)
# #     elif command == "forward":
# #         set_motor(CURRENT_SPEED, 0, CURRENT_SPEED, 0)
# #     elif command == "stop":
# #         set_motor(0, 0, 0, 0)
# #     else:
# #         print("[WARNING] Unknown command.")
# #         set_motor(0, 0, 0, 0)

# # # HTML Frontend (unchanged)
# # HTML = '''
# # <!DOCTYPE html>
# # <html>
# # <head>
# #     <title>Robot Control</title>
# #     <style>
# #         body { text-align: center; font-family: Arial; }
# #         button { width: 80px; height: 80px; margin: 10px; font-size: 20px; }
# #         input[type=range] { width: 300px; }
# #     </style>
# # </head>
# # <body>
# #     <h2>🕹️ Robot Control Panel</h2>
# #     <div>
# #         <button onclick="send('forward')">↑</button><br>
# #         <button onclick="send('left')">←</button>
# #         <button onclick="send('stop')">⛔</button>
# #         <button onclick="send('right')">→</button><br>
# #         <button onclick="send('backward')">↓</button>
# #     </div>
# #     <div style="margin: 20px;">
# #         <h3>Linear Speed: <span id="speedVal">5</span></h3>
# #         <input type="range" min="1" max="10" value="5" id="speedSlider" oninput="updateSpeed(this.value)">
# #     </div>
# #     <div style="margin: 20px;">
# #         <h3>Turn Speed: <span id="turnSpeedVal">4</span></h3>
# #         <input type="range" min="1" max="10" value="4" id="turnSpeedSlider" oninput="updateTurnSpeed(this.value)">
# #     </div>
# #     <hr>
# #     <div style="margin: 20px;">
# #         <h3>📍 Manual Location Label</h3>
# #         <input type="text" id="manualLabel" placeholder="e.g., Room 3A" style="padding:8px; width: 250px;">
# #         <button onclick="logLabel()">Log Location</button>
# #     </div>
# #     <button onclick="shutdownSLAM()">🛑 Quit SLAM</button>
# #     <script>
# #         function logLabel() {
# #             const label = document.getElementById("manualLabel").value.trim();
# #             if (!label) {
# #                 alert("Please enter a label.");
# #                 return;
# #             }
# #             fetch("/log", {
# #                 method: "POST",
# #                 headers: { "Content-Type": "application/json" },
# #                 body: JSON.stringify({ label: label })
# #             })
# #             .then(res => res.json())
# #             .then(data => alert(data.status || data.error))
# #             .catch(err => alert("Log failed: " + err));
# #         }
# #         function shutdownSLAM() {
# #             fetch("/shutdown", { method: "POST" })
# #             .then(res => res.json())
# #             .then(data => alert(data.status || data.error))
# #             .catch(err => alert("Shutdown failed: " + err));
# #         }
# #         function send(cmd) {
# #             fetch("/control", {
# #                 method: "POST",
# #                 headers: { "Content-Type": "application/json" },
# #                 body: JSON.stringify({ command: cmd })
# #             }).then(res => res.json())
# #             .then(data => console.log("[CONTROL]", cmd))
# #             .catch(err => alert("Command failed: " + err));
# #         }
# #         function updateSpeed(val) {
# #             document.getElementById("speedVal").innerText = val;
# #             fetch("/speed", {
# #                 method: "POST",
# #                 headers: { "Content-Type": "application/json" },
# #                 body: JSON.stringify({ speed: val })
# #             }).then(res => res.json())
# #             .then(data => console.log(data))
# #             .catch(err => alert("Speed update failed: " + err));
# #         }
# #         function updateTurnSpeed(val) {
# #             document.getElementById("turnSpeedVal").innerText = val;
# #             fetch("/turn_speed", {
# #                 method: "POST",
# #                 headers: { "Content-Type": "application/json" },
# #                 body: JSON.stringify({ speed: val })
# #             }).then(res => res.json())
# #             .then(data => console.log(data))
# #             .catch(err => alert("Turn speed update failed: " + err));
# #         }
# #         document.addEventListener("keydown", function(event) {
# #             switch (event.key) {
# #                 case "ArrowUp": case "w": case "W": send("forward"); break;
# #                 case "ArrowDown": case "x": case "X": send("backward"); break;
# #                 case "ArrowLeft": case "a": case "A": send("left"); break;
# #                 case "ArrowRight": case "d": case "D": send("right"); break;
# #                 case "s": case "S": case " ": send("stop"); break;
# #             }
# #         });
# #         document.addEventListener("keyup", function(event) {
# #             switch (event.key) {
# #                 case "ArrowUp": case "ArrowDown": case "ArrowLeft": case "ArrowRight":
# #                 case "w": case "W": case "x": case "X": case "a": case "A": case "d": case "D":
# #                     send("stop"); break;
# #             }
# #         });
# #     </script>
# # </body>
# # </html>
# # '''

# # # Flask Routes
# # @app.route("/", methods=["GET"])
# # def index():
# #     return HTML

# # @app.route("/control", methods=["POST"])
# # def control():
# #     data = request.get_json()
# #     if not data or 'command' not in data:
# #         return jsonify({"error": "Missing command"}), 400
# #     try:
# #         control_motors(data['command'])
# #         return jsonify({"status": f"Command '{data['command']}' executed."})
# #     except Exception as e:
# #         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
# #             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Control Error: {e}\n")
# #         return jsonify({"error": str(e)}), 500

# # @app.route("/speed", methods=["POST"])
# # def set_speed():
# #     global CURRENT_SPEED
# #     data = request.get_json()
# #     try:
# #         new_speed = float(data.get('speed', 5))
# #         if not (1 <= new_speed <= 10):
# #             raise ValueError("Speed must be between 1 and 10")
# #         CURRENT_SPEED = new_speed / 10.0
# #         ENA.value = CURRENT_SPEED
# #         ENB.value = CURRENT_SPEED
# #         with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
# #             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Linear speed set to {CURRENT_SPEED:.1f}\n")
# #         return jsonify({"status": f"Linear speed set to {CURRENT_SPEED:.1f}"})
# #     except Exception as e:
# #         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
# #             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Speed Error: {e}\n")
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/turn_speed", methods=["POST"])
# # def set_turn_speed():
# #     global TURN_SPEED
# #     data = request.get_json()
# #     try:
# #         new_turn_speed = float(data.get('speed', 4))
# #         if not (1 <= new_turn_speed <= 10):
# #             raise ValueError("Turn speed must be between 1 and 10")
# #         TURN_SPEED = new_turn_speed / 10.0
# #         with open("/home/jay/dev/ORB_SLAM3/Logs/motor_log.txt", "a") as f:
# #             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Turn speed set to {TURN_SPEED:.1f}\n")
# #         return jsonify({"status": f"Turn speed set to {TURN_SPEED:.1f}"})
# #     except Exception as e:
# #         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
# #             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Turn Speed Error: {e}\n")
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/shutdown", methods=["POST"])
# # def shutdown():
# #     try:
# #         with open("/tmp/kill_slam", "w") as f:
# #             f.write("exit")
# #         set_motor(0, 0, 0, 0)  # Stop motors
# #         return jsonify({"status": "Kill signal written"})
# #     except Exception as e:
# #         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
# #             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Shutdown Error: {e}\n")
# #         return jsonify({"error": str(e)}), 500

# # @app.route("/log", methods=["POST"])
# # def log_location():
# #     data = request.get_json()
# #     label = data.get("label", "").strip()
# #     if not label:
# #         return jsonify({"error": "Label is required"}), 400
# #     pose_path = "/tmp/latest_pose.txt"
# #     log_path = "/home/jay/dev/ORB_SLAM3/Maps/manual_log.txt"
# #     try:
# #         with open(pose_path, "r") as f:
# #             pose = f.read().strip()
# #         timestamp = time.strftime("%m%d%Y%H%M%S")
# #         with open(log_path, "a") as log:
# #             log.write(f"== [{timestamp}] ==\n")
# #             log.write(f"Manual Label: {label}\n")
# #             log.write(f"Pose: {pose}\n\n")
# #         return jsonify({"status": f"Label '{label}' logged with pose"})
# #     except Exception as e:
# #         with open("/home/jay/dev/ORB_SLAM3/Logs/gpio_errors.log", "a") as f:
# #             f.write(f"[{time.strftime('%Y%m%d_%H%M%S')}] Log Error: {e}\n")
# #         return jsonify({"error": str(e)}), 500

# # if __name__ == "__main__":
# #     print("Start Gunicorn separately: gunicorn -w 4 -b 0.0.0.0:5000 flask_motor:app")


# # # from flask import Flask, request, jsonify
# # # import time
# # # import os
# # # import signal
# # # from gpiozero import PWMOutputDevice, Device
# # # from gpiozero.pins.lgpio import LGPIOFactory

# # # # Use LGPIOFactory for GPIO access
# # # Device.pin_factory = LGPIOFactory()

# # # app = Flask(__name__)

# # # # === Motor Setup ===
# # # ENA = PWMOutputDevice(12)
# # # ENB = PWMOutputDevice(13)
# # # IN1 = PWMOutputDevice(17)
# # # IN2 = PWMOutputDevice(27)
# # # IN3 = PWMOutputDevice(22)
# # # IN4 = PWMOutputDevice(23)

# # # # === Speed Parameters ===
# # # DEFAULT_SPEED = 0.5
# # # DEFAULT_TURN_SPEED = 0.4
# # # CURRENT_SPEED = DEFAULT_SPEED
# # # TURN_SPEED = DEFAULT_TURN_SPEED

# # # ENA.value = CURRENT_SPEED
# # # ENB.value = CURRENT_SPEED

# # # def set_motor(lf, lb, rf, rb):
# # #     IN1.value = lf
# # #     IN2.value = lb
# # #     IN3.value = rf
# # #     IN4.value = rb 

# # # def control_motors(command):
# # #     print(f"[ACTION] Executing: {command}")
# # #     if command == "left": #f
# # #         set_motor(0, TURN_SPEED, TURN_SPEED, 0)
# # #     elif command == "right": #b
# # #         set_motor(TURN_SPEED, 0, 0, TURN_SPEED)
# # #     elif command == "backward": #l
# # #         set_motor(0, CURRENT_SPEED, 0, CURRENT_SPEED)
# # #     elif command == "forward": #r
# # #         set_motor(CURRENT_SPEED, 0, CURRENT_SPEED, 0)
# # #     elif command == "stop":
# # #         set_motor(0, 0, 0, 0)
# # #     else:
# # #         print("[WARNING] Unknown command.")
# # #         set_motor(0, 0, 0, 0)

# # # # === HTML Frontend ===
# # # HTML = '''
# # # <!DOCTYPE html>
# # # <html>
# # # <head>
# # #     <title>Robot Control</title>
# # #     <style>
# # #         body { text-align: center; font-family: Arial; }
# # #         button { width: 80px; height: 80px; margin: 10px; font-size: 20px; }
# # #         input[type=range] { width: 300px; }
# # #     </style>
# # # </head>
# # # <body>
# # #     <h2>🕹️ Robot Control Panel</h2>
# # #     <div>
# # #         <button onclick="send('forward')">↑</button><br>
# # #         <button onclick="send('left')">←</button>
# # #         <button onclick="send('stop')">⛔</button>
# # #         <button onclick="send('right')">→</button><br>
# # #         <button onclick="send('backward')">↓</button>
# # #     </div>
# # #     <div style="margin: 20px;">
# # #         <h3>Linear Speed: <span id="speedVal">5</span></h3>
# # #         <input type="range" min="1" max="10" value="5" id="speedSlider" oninput="updateSpeed(this.value)">
# # #     </div>
# # #     <div style="margin: 20px;">
# # #         <h3>Turn Speed: <span id="turnSpeedVal">4</span></h3>
# # #         <input type="range" min="1" max="10" value="4" id="turnSpeedSlider" oninput="updateTurnSpeed(this.value)">
# # #     </div>

# # #     <hr>
# # #     <div style="margin: 20px;">
# # #         <h3>📍 Manual Location Label</h3>
# # #         <input type="text" id="manualLabel" placeholder="e.g., Room 3A" style="padding:8px; width: 250px;">
# # #         <button onclick="logLabel()">Log Location</button>
# # #     </div>


# # #     <button onclick="shutdownSLAM()">🛑 Quit SLAM</button>

# # #     <script>
# # #         function logLabel() {
# # #             const label = document.getElementById("manualLabel").value.trim();
# # #             if (!label) {
# # #                 alert("Please enter a label.");
# # #                 return;
# # #             }

# # #             fetch("/log", {
# # #                 method: "POST",
# # #                 headers: { "Content-Type": "application/json" },
# # #                 body: JSON.stringify({ label: label })
# # #             })
# # #             .then(res => res.json())
# # #             .then(data => alert(data.status || data.error))
# # #             .catch(err => alert("Log failed: " + err));
# # #         }

# # #         function shutdownSLAM() {
# # #             fetch("/shutdown", { method: "POST" })
# # #             .then(res => res.json())
# # #             .then(data => alert(data.status || data.error))
# # #             .catch(err => alert("Shutdown failed: " + err));
# # #         }

# # #         function send(cmd) {
# # #             fetch("/control", {
# # #                 method: "POST",
# # #                 headers: { "Content-Type": "application/json" },
# # #                 body: JSON.stringify({ command: cmd })
# # #             }).then(res => res.json())
# # #             .then(data => console.log("[CONTROL]", cmd))
# # #             .catch(err => alert("Command failed: " + err));
# # #         }

# # #         function updateSpeed(val) {
# # #             document.getElementById("speedVal").innerText = val;
# # #             fetch("/speed", {  // ✅ this was wrong before
# # #                 method: "POST",
# # #                 headers: { "Content-Type": "application/json" },
# # #                 body: JSON.stringify({ speed: val })
# # #             }).then(res => res.json())
# # #             .then(data => console.log(data))
# # #             .catch(err => alert("Speed update failed: " + err));
# # #         }

# # #         function updateTurnSpeed(val) {
# # #             document.getElementById("turnSpeedVal").innerText = val;
# # #             fetch("/turn_speed", {  // ✅ this was wrong before
# # #                 method: "POST",
# # #                 headers: { "Content-Type": "application/json" },
# # #                 body: JSON.stringify({ speed: val })
# # #             }).then(res => res.json())
# # #             .then(data => console.log(data))
# # #             .catch(err => alert("Turn speed update failed: " + err));
# # #         }

# # #         // === Keyboard Events ===
# # #         document.addEventListener("keydown", function(event) {
# # #             switch (event.key) {
# # #                 case "ArrowUp":
# # #                 case "w":
# # #                 case "W":
# # #                     send("forward"); break;

# # #                 case "ArrowDown":
# # #                 case "x":
# # #                 case "X":
# # #                     send("backward"); break;

# # #                 case "ArrowLeft":
# # #                 case "a":
# # #                 case "A":
# # #                     send("left"); break;

# # #                 case "ArrowRight":
# # #                 case "d":
# # #                 case "D":
# # #                     send("right"); break;

# # #                 case "s":
# # #                 case "S":
# # #                 case " ":
# # #                     send("stop"); break;
# # #             }
# # #         });

# # #         document.addEventListener("keyup", function(event) {
# # #             switch (event.key) {
# # #                 case "ArrowUp":
# # #                 case "ArrowDown":
# # #                 case "ArrowLeft":
# # #                 case "ArrowRight":
# # #                 case "w":
# # #                 case "W":
# # #                 case "x":
# # #                 case "X":
# # #                 case "a":
# # #                 case "A":
# # #                 case "d":
# # #                 case "D":
# # #                     send("stop"); break;
# # #             }
# # #         });
# # #     </script>

# # # </body>
# # # </html>
# # # '''

# # # # === Flask Routes ===
# # # @app.route("/", methods=["GET"])
# # # def index():
# # #     return HTML

# # # @app.route("/control", methods=["POST"])
# # # def control():
# # #     data = request.get_json()
# # #     if not data or 'command' not in data:
# # #         return jsonify({"error": "Missing command"}), 400
# # #     control_motors(data['command'])
# # #     return jsonify({"status": f"Command '{data['command']}' executed."})

# # # @app.route("/speed", methods=["POST"])
# # # def set_speed():
# # #     global CURRENT_SPEED
# # #     data = request.get_json()
# # #     try:
# # #         new_speed = float(data.get('speed', 5))
# # #         if not (1 <= new_speed <= 10): raise ValueError
# # #         CURRENT_SPEED = new_speed / 10.0
# # #         ENA.value = CURRENT_SPEED
# # #         ENB.value = CURRENT_SPEED
# # #         return jsonify({"status": f"Linear speed set to {CURRENT_SPEED:.1f}"}), 200
# # #     except (TypeError, ValueError):
# # #         return jsonify({"error": "Speed must be between 1 and 10."}), 400

# # # @app.route("/turn_speed", methods=["POST"])
# # # def set_turn_speed():
# # #     global TURN_SPEED
# # #     data = request.get_json()
# # #     try:
# # #         new_turn_speed = float(data.get('speed', 4))
# # #         if not (1 <= new_turn_speed <= 10): raise ValueError
# # #         TURN_SPEED = new_turn_speed / 10.0
# # #         return jsonify({"status": f"Turn speed set to {TURN_SPEED:.1f}"}), 200
# # #     except (TypeError, ValueError):
# # #         return jsonify({"error": "Turn speed must be between 1 and 10."}), 400

# # # # @app.route("/shutdown", methods=["POST"])
# # # # def shutdown():
# # # #     try:
# # # #         with open("/tmp/slam_pid.txt", "r") as f:
# # # #             pid = int(f.read().strip())
# # # #         os.kill(pid, signal.SIGINT)
# # # #         return jsonify({"status": f"ORB_SLAM3 process {pid} signaled with SIGINT"}), 200
# # # #     except Exception as e:
# # #         # return jsonify({"error": str(e)}), 500
# # # @app.route("/shutdown", methods=["POST"])
# # # def shutdown():
# # #     try:
# # #         with open("/tmp/kill_slam", "w") as f:
# # #             f.write("exit")
# # #         return jsonify({"status": "Kill signal written"})
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)})

# # # @app.route("/log", methods=["POST"])
# # # def log_location():
# # #     data = request.get_json()
# # #     label = data.get("label", "").strip()

# # #     if not label:
# # #         return jsonify({"error": "Label is required"}), 400

# # #     pose_path = "/tmp/latest_pose.txt"
# # #     log_path = "/home/jay/dev/ORB_SLAM3/Maps/manual_log.txt"

# # #     if not os.path.exists(pose_path):
# # #         return jsonify({"error": "Pose data not available yet"}), 500

# # #     try:
# # #         with open(pose_path, "r") as f:
# # #             pose = f.read().strip()
# # #         timestamp = time.strftime("%m%d%Y%H%M%S")
# # #         with open(log_path, "a") as log:
# # #             log.write(f"== [{timestamp}] ==\n")
# # #             log.write(f"Manual Label: {label}\n")
# # #             log.write(f"Pose: {pose}\n\n")
# # #         return jsonify({"status": f"✅ '{label}' logged with current pose."})
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 500


# # # # === Start Flask App ===
# # # # if __name__ == "__main__":
# # # #     print("🚀 Flask robot controller running on http://<pi-ip>:5000")
# # # #     app.run(host="0.0.0.0", port=5000)
# # # if __name__ == "__main__":
# # #     print("Start Gunicorn separately: gunicorn -w 4 -b 0.0.0.0:5000 flask_motor:app")