# Re-import required libraries after kernel reset
import matplotlib.pyplot as plt
import numpy as np
import re

# Re-define parser functions
# def parse_ocr_log(file_path):
#     ocr_data = []
#     with open(file_path, 'r') as f:
#         lines = f.readlines()

#     i = 0
#     while i < len(lines):
#         line = lines[i]

#         if line.startswith("== "):
#             timestamp = line.strip("=\n ").strip()
#             i += 1

#             while i < len(lines) and not lines[i].startswith("Pose:"):
#                 i += 1
#             if i + 4 >= len(lines): break

#             pose_lines = lines[i+1:i+5]
#             try:
#                 pose_matrix = [[float(num) for num in row.strip().split()] for row in pose_lines]
#                 tx = pose_matrix[0][3]
#                 ty = pose_matrix[1][3]
#                 tz = pose_matrix[2][3]
#             except:
#                 tx, ty, tz = None, None, None

#             i += 5
#             while i < len(lines) and not lines[i].strip().startswith("Detected:"):
#                 i += 1
#             if i >= len(lines): break

#             label_match = re.search(r"Detected:\s*(\w+)", lines[i])
#             label = label_match.group(1) if label_match else "UNKNOWN"

#             confidence = 1.0
#             while i < len(lines):
#                 conf_match = re.search(r"Confidence:\s*([0-9.]+)", lines[i])
#                 if conf_match:
#                     confidence = float(conf_match.group(1))
#                     break
#                 i += 1

#             if tx is not None:
#                 ocr_data.append({
#                     "timestamp": timestamp,
#                     "label": label,
#                     "x": tx,
#                     "y": ty,
#                     "z": tz,
#                     "confidence": confidence
#                 })

#         i += 1

#     return ocr_data

def parse_ocr_log(file_path):
    ocr_data = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("== "):
            timestamp = line.strip("=\n ").strip()
            i += 1

            # Skip until Detected Text(s)
            while i < len(lines) and not lines[i].strip().startswith("Detected Text"):
                i += 1
            i += 1  # Move to first detection line

            labels_conf = []
            while i < len(lines) and lines[i].strip().startswith("-"):
                match = re.search(r"-\s+(\w+)\s+\(Confidence:\s*([0-9.]+)\)", lines[i])
                if match:
                    label = match.group(1)
                    confidence = float(match.group(2))
                    labels_conf.append((label, confidence))
                i += 1

            # Look for Pose
            while i < len(lines) and not lines[i].startswith("Pose:"):
                i += 1
            if i + 4 >= len(lines):
                break

            pose_lines = lines[i+1:i+5]
            try:
                pose_matrix = [[float(num) for num in row.strip().split()] for row in pose_lines]
                tx = pose_matrix[0][3]
                ty = pose_matrix[1][3]
                tz = pose_matrix[2][3]
            except:
                tx, ty, tz = None, None, None

            for label, conf in labels_conf:
                if tx is not None:
                    ocr_data.append({
                        "timestamp": timestamp,
                        "label": label,
                        "x": tx,
                        "y": ty,
                        "z": tz,
                        "confidence": conf
                    })

        i += 1

    return ocr_data


def parse_keyframes(file_path):
    traj = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip() == "":
                continue
            parts = line.strip().split()
            if len(parts) >= 8:
                x, y = float(parts[1]), float(parts[2])
                traj.append((x, y))
    return traj

# Load example files
ocr_file_path = "/home/jay/dev/ORB_SLAM3/Maps/OCR_Logs/ocr_detections_20250716.txt"
keyframe_file_path = "/home/jay/dev/ORB_SLAM3/Maps/KeyFrameTrajectory.txt"
ocr_data = parse_ocr_log(ocr_file_path)
keyframes = parse_keyframes(keyframe_file_path)

# Prepare OCR points for plotting
ocr_x = [d['x'] for d in ocr_data]
ocr_y = [d['y'] for d in ocr_data]
labels = [d['label'] for d in ocr_data]
confidences = [d['confidence'] for d in ocr_data]

# Normalize confidences to 0-1 for colormap
conf_norm = (np.array(confidences) - min(confidences)) / (max(confidences) - min(confidences))

# Plot
plt.figure(figsize=(10, 8))
if keyframes:
    kx, ky = zip(*keyframes)
    plt.plot(kx, ky, label="Keyframe Trajectory", color='blue')

sc = plt.scatter(ocr_x, ocr_y, c=conf_norm, cmap='Reds', s=80, edgecolors='k', label="OCR Detections")
for x, y, label in zip(ocr_x, ocr_y, labels):
    plt.text(x, y, label, fontsize=9, color='black', ha='center', va='bottom')

plt.colorbar(sc, label="OCR Confidence")
plt.xlabel("X")
plt.ylabel("Y")
plt.title("Keyframe Trajectory with OCR Detections")
plt.legend()
plt.grid(True)
plt.axis("equal")
plt.tight_layout()
plt.show()
