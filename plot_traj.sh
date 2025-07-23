#!/bin/bash

# === Input Trajectories ===
TRAJ_PATH="/home/jay/dev/monocular_gt.txt"
TRAJ_PATH_2="/home/jay/dev/monocular_reading.txt"

# === Output Directory Setup ===
PLOT_DIR="/home/jay/dev/Plots"
mkdir -p "$PLOT_DIR"
LOG_FILE="$PLOT_DIR/plots.log"

# Start fresh log
echo "Plotting started at $(date)" > "$LOG_FILE"

# === Output Paths ===
PLOT_PATH_A="$PLOT_DIR/$(basename "$TRAJ_PATH")_a.pdf"
PLOT_PATH_B="$PLOT_DIR/$(basename "$TRAJ_PATH_2")_b.pdf"
PLOT_PATH_C="$PLOT_DIR/compare_ab.pdf"
ZIP_PATH="$PLOT_DIR/$(basename "$TRAJ_PATH")_vs_$(basename "$TRAJ_PATH_2").zip"
TABLE_PATH="$PLOT_DIR/metrics_table.csv"

# Step 1: Plot test trajectory
echo "Plotting: $TRAJ_PATH" | tee -a "$LOG_FILE"
evo_traj tum "$TRAJ_PATH" -p --plot_mode xz --save_plot "$PLOT_PATH_A" --no_warnings >> "$LOG_FILE" 2>&1

# Step 2: Plot control trajectory
echo "Plotting: $TRAJ_PATH_2" | tee -a "$LOG_FILE"
evo_traj tum "$TRAJ_PATH_2" -p --plot_mode xz --save_plot "$PLOT_PATH_B" --no_warnings >> "$LOG_FILE" 2>&1

# Step 3: Plot comparison
echo "Comparing trajectories..." | tee -a "$LOG_FILE"
evo_traj tum "$TRAJ_PATH" --ref="$TRAJ_PATH_2" -va -p --plot_mode xz --save_plot "$PLOT_PATH_C" --no_warnings >> "$LOG_FILE" 2>&1

# Step 4: Run APE
echo "Calculating APE..." | tee -a "$LOG_FILE"
evo_ape tum "$TRAJ_PATH_2" "$TRAJ_PATH" \
  -va --plot --plot_mode xz \
  --save_results "$ZIP_PATH" \
  --no_warnings >> "$LOG_FILE" 2>&1

# Step 5: Export table
echo "Exporting results table..." | tee -a "$LOG_FILE"
evo_res "$ZIP_PATH" -p --save_table "$TABLE_PATH" --no_warnings >> "$LOG_FILE" 2>&1

# Step 6: Move APE plots
RAW_PNG="ape_plot_raw.png"
MAP_PNG="ape_plot_map.png"

if [ -f "$RAW_PNG" ]; then
    mv "$RAW_PNG" "$PLOT_DIR/APE_raw_plot.png"
    echo "Moved: APE_raw_plot.png" | tee -a "$LOG_FILE"
fi

if [ -f "$MAP_PNG" ]; then
    mv "$MAP_PNG" "$PLOT_DIR/APE_map_plot.png"
    echo "Moved: APE_map_plot.png" | tee -a "$LOG_FILE"
fi

echo "All plots and metrics saved to: $PLOT_DIR" | tee -a "$LOG_FILE"
