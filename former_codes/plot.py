import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path

def load_tum_trajectory(path):
    poses = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                tokens = line.strip().split()
                if len(tokens) == 8:
                    tx, ty, tz = float(tokens[4]), float(tokens[5]), float(tokens[6])
                    poses.append((tx, ty, tz))
    return np.array(poses)

def parse_manual_labels(path):
    labels = []
    with open(path, 'r') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("== ["):
            label_line = lines[i + 1].strip()
            label = label_line.split(":")[-1].strip()
            matrix_lines = lines[i + 2:i + 6]
            try:
                pose_matrix = np.array([[float(num) for num in line.strip().split()] for line in matrix_lines])
                x, y, z = pose_matrix[0][3], pose_matrix[1][3], pose_matrix[2][3]
                labels.append(('manual', label, x, y, z, 1.0))
            except:
                pass
            i += 6
        else:
            i += 1
    return labels

def parse_auto_labels(path):
    labels = []
    with open(path, 'r') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("== "):
            label, conf = None, 1.0
            pose_matrix = None
            try:
                matrix_lines = lines[i + 1:i + 5]
                pose_matrix = np.array([[float(num) for num in line.strip().split()] for line in matrix_lines])
            except:
                i += 1
                continue
            for j in range(i + 5, i + 12):
                if j >= len(lines): break
                if "Detected:" in lines[j]:
                    label = lines[j].split("Detected:")[1].strip()
                if "Confidence:" in lines[j]:
                    try:
                        conf = float(lines[j].split("Confidence:")[1].strip())
                    except:
                        conf = 1.0
            if label and pose_matrix is not None:
                x, y, z = pose_matrix[0][3], pose_matrix[1][3], pose_matrix[2][3]
                labels.append(('auto', label, x, y, z, conf))
            i += 12
        else:
            i += 1
    return labels

def plot_3d_trajectory(control_path, test_path, manual_log, auto_log):
    control_traj = load_tum_trajectory(control_path)
    test_traj = load_tum_trajectory(test_path)
    manual_labels = parse_manual_labels(manual_log)
    auto_labels = parse_auto_labels(auto_log)

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    # Trajectories
    ax.plot(control_traj[:, 0], control_traj[:, 1], control_traj[:, 2], label='Control Trajectory', color='black', linewidth=2)
    ax.plot(test_traj[:, 0], test_traj[:, 1], test_traj[:, 2], label='Test Trajectory', color='orange', linestyle='--')

    # Manual labels
    for _, label, x, y, z, _ in manual_labels:
        ax.scatter(x, y, z, color='blue', s=60, label='Manual' if label not in ax.get_legend_handles_labels()[1] else "")
        ax.text(x, y, z + 0.05, label, fontsize=9, color='blue')

    # Auto labels
    for _, label, x, y, z, conf in auto_labels:
        ax.scatter(x, y, z, color='green', alpha=conf, marker='x', s=80, label='Auto (OCR)' if label not in ax.get_legend_handles_labels()[1] else "")
        ax.text(x, y, z + 0.05, label, fontsize=9, color='green', alpha=conf)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title("3D Trajectories with OCR Labels")
    ax.legend()
    plt.tight_layout()
    plt.savefig("trajectory_with_labels_3d.png")
    print("✅ 3D Plot saved to: trajectory_with_labels_3d.png")
    plt.show()

if __name__ == "__main__":
    control_file = str(Path("~/dev/ORB_SLAM3/Maps/control.txt").expanduser())
    # test_file = str(Path("~/dev/ORB_SLAM3/Maps/test.txt").expanduser())
    test_file = str(Path("~/dev/ORB_SLAM3/Maps/control.txt").expanduser())
    manual_log = str(Path("~/dev/ORB_SLAM3/Maps/manual_log.txt").expanduser())
    auto_log = str(Path("~/dev/ORB_SLAM3/Maps/OCR_Logs/ocr_detections_20250715.txt").expanduser())

    plot_3d_trajectory(control_file, test_file, manual_log, auto_log)
