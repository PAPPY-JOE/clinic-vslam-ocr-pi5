#!/bin/bash

# Check for mode argument --- Works, but lacking terminal separation
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 [map|localize] [debug]"
    exit 1
fi

MODE=$1
DEBUG=${2:-no}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define paths
YAML_FILE="/home/jay/dev/code/my_camera.yaml"
VOCAB_PATH="/home/jay/dev/ORB_SLAM3/Vocabulary/ORBvoc.txt"
MAP_PATH="/home/jay/dev/ORB_SLAM3/Maps/clinic_map_atlas.bag"
EXE_PATH="/home/jay/dev/ORB_SLAM3/build/Examples/Monocular/mono_webcam"
PIPE_PATH="/tmp/frames.pipe"
LOG_DIR="/home/jay/dev/ORB_SLAM3/Logs"
LOG_FILE="$LOG_DIR/run_slam_$(date +%Y%m%d_%H%M%S).log"

# Create Logs directory
mkdir -p "$LOG_DIR" || { echo "ERROR: Failed to create $LOG_DIR"; exit 1; }

# Redirect all output to log file
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Starting SLAM run at $(date)"

# Clean up existing processes
echo "Terminating existing processes..."
pkill -f mono_webcam 2>/dev/null
pkill -f ocr_monitor.py 2>/dev/null
pkill -f flask_motor.py 2>/dev/null
sleep 1

# Free port 5000
if lsof -i :5000 >/dev/null 2>&1; then
    echo "Freeing port 5000..."
    fuser -k 5000/tcp
    sleep 1
fi

# Free GPIO pins safely
echo "Resetting GPIO pins..."
python3 -c "import lgpio; h=lgpio.gpiochip_open(0); pins=[12,13,17,27,22,23]; [lgpio.gpio_free(h,p) for p in pins if lgpio.gpio_get_mode(h,p) != lgpio.FREE]; lgpio.gpiochip_close(h)" 2>/dev/null || echo "WARNING: GPIO cleanup failed, continuing..."

# Remove old pipe if exists
if [[ -p "$PIPE_PATH" ]]; then
    echo "Removing existing pipe..."
    rm -f "$PIPE_PATH"
fi

# Create new named pipe
echo "Creating named pipe at $PIPE_PATH"
mkfifo "$PIPE_PATH" || { echo "ERROR: Failed to create pipe"; exit 1; }
chmod 666 "$PIPE_PATH" || { echo "ERROR: Failed to set pipe permissions"; exit 1; }

# Release camera resources
echo "Releasing camera..."
if fuser /dev/video0 >/dev/null 2>&1; then
    echo "Killing processes using /dev/video0"
    sudo fuser -k /dev/video0
    sleep 2
fi

# Reload uvcvideo module
echo "Optimizing camera module..."
sudo modprobe -r uvcvideo 2>/dev/null || true
sudo modprobe uvcvideo nodrop=1 timeout=5000 quirks=0x80
sleep 2

# Verify camera access with retries
echo "Verifying camera..."
for i in {1..3}; do
    python3 -c "import cv2; exit(0) if cv2.VideoCapture(0).isOpened() else exit(1)" && break
    echo "Retrying camera access ($i/3)..."
    sleep 2
done
if [[ $? -ne 0 ]]; then
    echo "ERROR: Camera not accessible"
    rm -f "$PIPE_PATH"
    exit 1
fi

# Configure camera settings (only supported controls)
echo "Configuring camera settings..."
v4l2-ctl -d /dev/video0 --set-ctrl=focus_automatic_continuous=0 2>/dev/null || echo "WARNING: focus_automatic_continuous not supported"
v4l2-ctl -d /dev/video0 --set-ctrl=focus_absolute=10 2>/dev/null || echo "WARNING: focus_absolute not supported"
v4l2-ctl -d /dev/video0 --set-ctrl=power_line_frequency=1 2>/dev/null || echo "WARNING: power_line_frequency not supported"
# v4l2-ctl -d /dev/video0 --set-ctrl=brightness=128 2>/dev/null || echo "WARNING: brightness not supported"
# v4l2-ctl -d /dev/video0 --set-ctrl=contrast=128 2>/dev/null || echo "WARNING: contrast not supported"

# Prepare ORB-SLAM3 config
echo "Preparing ORB_SLAM3 config for '$MODE' mode..."
# Verify YAML file exists
if [[ ! -f "$YAML_FILE" ]]; then
    echo "ERROR: Configuration file $YAML_FILE not found"
    rm -f "$PIPE_PATH"
    exit 1
fi
# Clear existing atlas settings
sed -i '/System.SaveAtlasToFile:/d' "$YAML_FILE"
sed -i '/System.LoadAtlasFromFile:/d' "$YAML_FILE"
if [[ "$MODE" == "map" ]]; then
    echo "MAP BUILDING mode"
    echo "System.SaveAtlasToFile: \"$MAP_PATH\"" >> "$YAML_FILE"
elif [[ "$MODE" == "localize" ]]; then
    echo "LOCALIZATION mode"
    [[ ! -f "$MAP_PATH" ]] && { echo "ERROR: Map file not found at $MAP_PATH"; rm -f "$PIPE_PATH"; exit 1; }
    echo "System.LoadAtlasFromFile: \"$MAP_PATH\"" >> "$YAML_FILE"
    echo "System.SaveAtlasToFile: \"$MAP_PATH\"" >> "$YAML_FILE"
fi

# Start OCR monitor in background
echo "Starting OCR monitor..."
nice -n 10 python3 "$SCRIPT_DIR/ocr_monitor.py" &
OCR_PID=$!
echo $OCR_PID > /tmp/ocr_pid.txt
sleep 2

# Verify pipe is open
echo "Checking pipe readiness..."
for i in {1..5}; do
    if [[ -p "$PIPE_PATH" && $(lsof "$PIPE_PATH" 2>/dev/null) ]]; then
        echo "Pipe is ready"
        break
    fi
    echo "Waiting for pipe to be ready ($i/5)..."
    sleep 1
done
if [[ $i -eq 5 ]]; then
    echo "ERROR: Pipe not ready"
    pkill -P $OCR_PID
    rm -f "$PIPE_PATH" /tmp/ocr_pid.txt
    exit 1
fi

# Start Flask server
echo "Launching Flask server..."
python3 "$SCRIPT_DIR/flask_motor.py" &
FLASK_PID=$!
echo $FLASK_PID > /tmp/flask_pid.txt
sleep 2

# Start SLAM
echo "Launching ORB_SLAM3..."
if [[ "$DEBUG" == "debug" ]]; then
    gdb -ex run --args "$EXE_PATH" "$VOCAB_PATH" "$YAML_FILE"
else
    "$EXE_PATH" "$VOCAB_PATH" "$YAML_FILE" > "$LOG_DIR/mono_webcam_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    SLAM_PID=$!
    echo $SLAM_PID > /tmp/slam_pid.txt
    wait $SLAM_PID
fi

# Check for crash
if [[ $? -eq 139 ]]; then
    echo "ERROR: ORB_SLAM3 crashed with segmentation fault"
    echo "Check /var/log/syslog or enable core dumps for debugging"
fi

# === Post-Processing: Plot trajectory ===
TIMESTAMP=$(date +%Y%m%d_%H%M%S) # Generate timestamp for output naming
TRAJ_PATH="/home/jay/dev/ORB_SLAM3/Maps/KeyFrameTrajectory_${TIMESTAMP}.txt"
PLOT_PATH="/home/jay/dev/ORB_SLAM3/Maps/evo_plot_${TIMESTAMP}.pdf"

if [[ -f "$TRAJ_PATH" ]]; then
    echo "📈 Plotting trajectory with evo_traj..."
    evo_traj tum "$TRAJ_PATH" -p --plot_mode=xz --save_plot "$PLOT_PATH"
    if [[ -f "$PLOT_PATH" ]]; then
        echo "✅ Plot saved to $PLOT_PATH"
    else
        echo "⚠️ Failed to save trajectory plot"
    fi
else
    echo "❌ No trajectory file found at $TRAJ_PATH"
fi

# Cleanup
echo "Cleaning up..."
rm -f "$PIPE_PATH" /tmp/slam_pid.txt /tmp/ocr_pid.txt /tmp/flask_pid.txt
echo "SLAM run completed at $(date)"
