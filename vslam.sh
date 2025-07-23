#!/bin/bash

# Usage check
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 [map|localize] [tmux]"
    exit 1
fi

MODE=$1
DEBUG=${2:-no}
SESSION="slam_session"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$HOME/dev/venv"
ACTIVATE_VENV="source \"$VENV_PATH/bin/activate\""

# Paths
YAML_FILE="$HOME/dev/code/my_camera.yaml"
VOCAB_PATH="$HOME/dev/ORB_SLAM3/Vocabulary/ORBvoc.txt"
MAP_PATH="$HOME/dev/ORB_SLAM3/Maps/clinic_map_atlas.bag"
EXE_PATH="$HOME/dev/ORB_SLAM3/build/Examples/Monocular/mono_webcam"
PIPE_PATH="/tmp/frames.pipe"
LOG_DIR="$HOME/dev/ORB_SLAM3/Logs"
mkdir -p "$LOG_DIR"

# Timestamp
TS=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="$LOG_DIR/main_$TS.log"

# Logging
exec > >(tee -a "$MAIN_LOG") 2>&1

echo "=== Starting SLAM session ($MODE mode) at $(date) ==="

# Kill previous session and processes
tmux has-session -t $SESSION 2>/dev/null && tmux kill-session -t $SESSION
pkill -f mono_webcam 2>/dev/null
pkill -f ocr_monitor.py 2>/dev/null
pkill -f flask_motor.py 2>/dev/null
fuser -k 5000/tcp 2>/dev/null

# Free GPIO
# python3 -c "import lgpio; h=lgpio.gpiochip_open(0); pins=[12,13,17,27,22,23]; [lgpio.gpio_free(h,p) for p in pins if lgpio.gpio_get_mode(h,p) != lgpio.FREE]; lgpio.gpiochip_close(h)" || echo "WARNING: GPIO cleanup failed"

# Camera setup
rm -f "$PIPE_PATH"
mkfifo "$PIPE_PATH"
chmod 666 "$PIPE_PATH"

sudo fuser -k /dev/video0 2>/dev/null
sleep 2
sudo modprobe -r uvcvideo || true
sudo modprobe uvcvideo nodrop=1 timeout=5000 quirks=0x80
sleep 2

for i in {1..3}; do
    python3 -c "import cv2; exit(0) if cv2.VideoCapture(0).isOpened() else exit(1)" && break
    echo "Retrying camera access ($i/3)..."
    sleep 2
done

if [[ $? -ne 0 ]]; then
    echo "ERROR: Camera not accessible"
    exit 1
fi

# Camera settings
v4l2-ctl -d /dev/video0 --set-ctrl=focus_automatic_continuous=0
v4l2-ctl -d /dev/video0 --set-ctrl=focus_absolute=10
v4l2-ctl -d /dev/video0 --set-ctrl=power_line_frequency=1

# YAML config
if [[ ! -f "$YAML_FILE" ]]; then
    echo "ERROR: Configuration file $YAML_FILE not found"
    exit 1
fi

sed -i '/System.SaveAtlasToFile:/d' "$YAML_FILE"
sed -i '/System.LoadAtlasFromFile:/d' "$YAML_FILE"

if [[ "$MODE" == "map" ]]; then
    echo "MAP BUILDING mode"
    echo "System.SaveAtlasToFile: \"$MAP_PATH\"" >> "$YAML_FILE"
elif [[ "$MODE" == "localize" ]]; then
    echo "LOCALIZATION mode"
    [[ ! -f "$MAP_PATH" ]] && { echo "ERROR: Map file not found at $MAP_PATH"; exit 1; }
    echo "System.LoadAtlasFromFile: \"$MAP_PATH\"" >> "$YAML_FILE"
    echo "System.SaveAtlasToFile: \"$MAP_PATH\"" >> "$YAML_FILE"
else
    echo "ERROR: Unknown mode: $MODE"
    exit 1
fi

# Log files
SLAM_LOG="$LOG_DIR/slam_$TS.log"
OCR_LOG="$LOG_DIR/ocr_$TS.log"
FLASK_LOG="$LOG_DIR/flask_$TS.log"

# Helper function
run_tmux_pane() {
    local target=$1
    local cmd=$2
    tmux send-keys -t "$target" "$ACTIVATE_VENV && cd \"$SCRIPT_DIR\" && $cmd" C-m
}

# Start tmux session
tmux new-session -d -s $SESSION -n ORB_SLAM3

# Pane 0: ORB_SLAM3
run_tmux_pane "$SESSION:0.0" "echo 'Running ORB_SLAM3'; \"$EXE_PATH\" \"$VOCAB_PATH\" \"$YAML_FILE\" | tee \"$SLAM_LOG\""

# Pane 1: OCR
tmux split-window -v -t $SESSION:0
run_tmux_pane "$SESSION:0.1" "echo 'Running ocr_monitor.py'; python ocr_monitor.py | tee \"$OCR_LOG\""

# Pane 2: Flask
tmux split-window -h -t $SESSION:0.1
run_tmux_pane "$SESSION:0.2" "echo 'Running flask_motor.py'; python flask_motor.py | tee \"$FLASK_LOG\""

tmux select-pane -t $SESSION:0.0

# Attach or finish
if [[ "$DEBUG" == "tmux" ]]; then
    tmux attach -t $SESSION
else
    echo "?? All processes launched in tmux session '$SESSION'"
    echo "Run 'tmux attach -t $SESSION' to view"
fi

