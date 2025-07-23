import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

trajectory_file = "/home/jay/dev/ORB_SLAM3/Maps/KeyFrameTrajectory.txt"

xs, ys, zs = [], [], []

with open(trajectory_file) as f:
    for line in f:
        if line.startswith('#') or len(line.strip()) == 0:
            continue
        parts = line.strip().split()
        tx, ty, tz = float(parts[1]), float(parts[2]), float(parts[3])
        xs.append(tx)
        ys.append(ty)
        zs.append(tz)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(xs, ys, zs, label='Camera Path', marker='o', markersize=2, linewidth=1)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('ORB-SLAM3 KeyFrame Trajectory')
ax.legend()
plt.tight_layout()
plt.show()
