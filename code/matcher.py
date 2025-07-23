import numpy as np
import argparse
import subprocess
import matplotlib.pyplot as plt
from pathlib import Path

def load_tum(file_path):
    data = []
    with open(file_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                tokens = line.strip().split()
                if len(tokens) == 8:
                    t = float(tokens[0])
                    pose = list(map(float, tokens[1:]))
                    data.append((t, pose))
    return sorted(data)

def save_tum(data, path):
    with open(path, "w") as f:
        for t, pose in data:
            f.write(f"{t:.6f} " + " ".join(f"{x:.6f}" for x in pose) + "\n")

def interpolate_pose(t, t1, p1, t2, p2):
    alpha = (t - t1) / (t2 - t1)
    interp = [p1[i] * (1 - alpha) + p2[i] * alpha for i in range(7)]
    return interp

def interpolate_trajectory(target_data, new_timestamps):
    times, poses = zip(*target_data)
    interpolated = []

    for t in new_timestamps:
        if t < times[0] or t > times[-1]:
            continue
        for i in range(len(times) - 1):
            if times[i] <= t <= times[i+1]:
                interp_pose = interpolate_pose(t, times[i], poses[i], times[i+1], poses[i+1])
                interpolated.append((t, interp_pose))
                break
    return interpolated

def align(ref_data, tgt_data, max_time_diff):
    aligned_ref = []
    aligned_tgt = []
    tgt_times = [t for t, _ in tgt_data]

    for ref_t, ref_pose in ref_data:
        diffs = np.abs(np.array(tgt_times) - ref_t)
        idx = np.argmin(diffs)
        if diffs[idx] <= max_time_diff:
            aligned_ref.append((ref_t, ref_pose))
            aligned_tgt.append((tgt_data[idx][0], tgt_data[idx][1]))
    return aligned_ref, aligned_tgt

def search_offset(ref_data, target_data, max_diff, offset_range, step):
    best_count = 0
    best_offset = 0
    best_ref = []
    best_tgt = []
    offsets = []
    counts = []

    ref_times = [t for t, _ in ref_data]

    for offset in np.arange(offset_range[0], offset_range[1] + step, step):
        shifted_target = [(t + offset, pose) for t, pose in target_data]
        interpolated = interpolate_trajectory(shifted_target, ref_times)

        if not interpolated:
            offsets.append(offset)
            counts.append(0)
            continue  # 🔒 Skip invalid offsets

        aligned_ref, aligned_tgt = align(ref_data, interpolated, max_diff)

        count = len(aligned_ref)
        offsets.append(offset)
        counts.append(count)

        if count > best_count:
            best_count = count
            best_offset = offset
            best_ref = aligned_ref
            best_tgt = aligned_tgt

    return best_offset, best_count, best_ref, best_tgt, offsets, counts

def plot_matches(offsets, counts, best_offset):
    plt.figure(figsize=(10, 4))
    plt.bar(offsets, counts, width=0.9 * (offsets[1] - offsets[0]), color='lightblue')
    plt.axvline(best_offset, color='red', linestyle='--', label=f"Best Offset: {best_offset:.2f}s")
    plt.xlabel("Offset (s)")
    plt.ylabel("Matches")
    plt.title("Match count vs. Time Offset")
    plt.legend()
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def run_evo(ref_path, tgt_path):
    print("📈 Running evo_ape and evo_traj ...")
    subprocess.run([
        "evo_ape", "tum", ref_path, tgt_path,
        "-va", "--plot_mode", "xz", "--save_plot", "ape_plot.png"
    ]) 
    subprocess.run([
        "evo_traj", "tum", str(ref_path), str(tgt_path),
        "--ref", str(ref_path),
        "--plot", "--plot_mode", "xyz", "--save_plot", "evo_traj_plot.png"

    ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ref", help="Reference trajectory (TUM format)")
    parser.add_argument("target", help="Target trajectory (TUM format)")
    parser.add_argument("output_dir", help="Where to save aligned files")
    parser.add_argument("--max-time-diff", type=float, default=0.5)
    parser.add_argument("--offset-range", nargs=2, type=float, default=[-3000, 3000])
    parser.add_argument("--step", type=float, default=1.0)

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ref_data = load_tum(args.ref)
    target_data = load_tum(args.target)

    best_offset, count, best_ref, best_tgt, offsets, counts = search_offset(
        ref_data, target_data, args.max_time_diff, args.offset_range, args.step
    )

    print(f"\n✅ Best Offset: {best_offset:.2f} s")
    print(f"✅ Matches: {count}\n")

    aligned_ref_path = output_dir / "aligned_ref.txt"
    aligned_tgt_path = output_dir / "aligned_target.txt"

    save_tum(best_ref, aligned_ref_path)
    save_tum(best_tgt, aligned_tgt_path)

    print(f"📁 Saved: {aligned_ref_path}")
    print(f"📁 Saved: {aligned_tgt_path}")

    plot_matches(offsets, counts, best_offset)
    run_evo(str(aligned_ref_path), str(aligned_tgt_path))


# import numpy as np # scans for best offset
# import matplotlib.pyplot as plt
# from pathlib import Path
# import argparse

# def load_tum_trajectory(file_path):
#     data = []
#     with open(file_path, 'r') as f:
#         for line in f:
#             if line.strip() and not line.startswith("#"):
#                 tokens = line.strip().split()
#                 if len(tokens) == 8:
#                     t = float(tokens[0])
#                     pose = list(map(float, tokens[1:]))
#                     data.append((t, pose))
#     return data

# def save_tum_trajectory(data, out_path):
#     with open(out_path, "w") as f:
#         for t, pose in data:
#             f.write(f"{t:.6f} " + " ".join(f"{x:.6f}" for x in pose) + "\n")

# def align_trajectories(ref_data, target_data, max_time_diff):
#     aligned_ref = []
#     aligned_target = []
#     target_timestamps = np.array([t for t, _ in target_data])
#     used_indices = set()

#     for ref_t, ref_pose in ref_data:
#         diffs = np.abs(target_timestamps - ref_t)
#         idx = np.argmin(diffs)
#         if idx in used_indices:
#             continue
#         if diffs[idx] <= max_time_diff:
#             aligned_ref.append((ref_t, ref_pose))
#             aligned_target.append((target_data[idx][0], target_data[idx][1]))
#             used_indices.add(idx)
#     return aligned_ref, aligned_target

# def search_best_offset(ref_data, target_data, max_time_diff, offset_range, step):
#     best_offset = None
#     best_matches = 0
#     best_aligned_ref = []
#     best_aligned_target = []

#     offsets = []
#     match_counts = []

#     print("🔍 Scanning for best time offset...")
#     for offset in np.arange(offset_range[0], offset_range[1] + step, step):
#         shifted_target = [(t + offset, pose) for t, pose in target_data]
#         aligned_ref, aligned_target = align_trajectories(ref_data, shifted_target, max_time_diff)
#         num_matches = len(aligned_ref)

#         offsets.append(offset)
#         match_counts.append(num_matches)

#         if num_matches > best_matches:
#             best_matches = num_matches
#             best_offset = offset
#             best_aligned_ref = aligned_ref
#             best_aligned_target = aligned_target

#     return best_offset, best_matches, best_aligned_ref, best_aligned_target, offsets, match_counts

# def plot_offset_matches(offsets, match_counts, best_offset):
#     plt.figure(figsize=(12, 5))
#     plt.bar(offsets, match_counts, width=0.8 * (offsets[1] - offsets[0]), color='skyblue', edgecolor='black')
#     plt.axvline(best_offset, color='red', linestyle='--', label=f'Best Offset: {best_offset:.2f}s')
#     plt.title("Number of Matches vs. Time Offset")
#     plt.xlabel("Time Offset (s)")
#     plt.ylabel("Number of Matches")
#     plt.legend()
#     plt.grid(True)
#     plt.tight_layout()
#     plt.show()

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("ref", help="Reference trajectory (TUM format)")
#     parser.add_argument("target", help="Target trajectory (TUM format)")
#     parser.add_argument("output_dir", help="Directory to save aligned results")
#     parser.add_argument("--max-time-diff", type=float, default=0.5)
#     parser.add_argument("--offset-range", nargs=2, type=float, default=[-3000, 3000],
#                         help="Offset range to search (e.g. -3000 3000)")
#     parser.add_argument("--step", type=float, default=0.5, help="Step size for offset search")
#     args = parser.parse_args()

#     ref_data = load_tum_trajectory(args.ref)
#     tgt_data = load_tum_trajectory(args.target)
#     output_dir = Path(args.output_dir)
#     output_dir.mkdir(parents=True, exist_ok=True)

#     best_offset, match_count, aligned_ref, aligned_target, offsets, match_counts = search_best_offset(
#         ref_data, tgt_data, args.max_time_diff, args.offset_range, args.step
#     )

#     if match_count == 0:
#         print("❌ No matches found in the given offset range.")
#     else:
#         save_tum_trajectory(aligned_ref, output_dir / "aligned_ref.txt")
#         save_tum_trajectory(aligned_target, output_dir / "aligned_target.txt")
#         print(f"✅ Best offset: {best_offset:.2f} s")
#         print(f"✅ Matches: {match_count}")
#         print(f"📄 Saved to: {output_dir/'aligned_ref.txt'} and {output_dir/'aligned_target.txt'}")

#         # 📊 Show match histogram
#         plot_offset_matches(offsets, match_counts, best_offset)

# # import numpy as np
# # import argparse
# # from pathlib import Path
# # import matplotlib.pyplot as plt

# # def load_tum_trajectory(file_path):
# #     data = []
# #     with open(file_path, 'r') as f:
# #         for line in f:
# #             if line.strip() and not line.startswith('#'):
# #                 tokens = line.strip().split()
# #                 if len(tokens) == 8:
# #                     timestamp = float(tokens[0])
# #                     pose = list(map(float, tokens[1:]))
# #                     data.append((timestamp, pose))
# #     return data

# # def normalize_timestamps(data):
# #     base_time = data[0][0]
# #     return [(t - base_time, pose) for t, pose in data]

# # def save_tum_trajectory(data, out_path):
# #     with open(out_path, 'w') as f:
# #         for t, pose in data:
# #             f.write(f"{t:.6f} {' '.join(f'{x:.6f}' for x in pose)}\n")

# # def align_trajectories(ref_data, target_data, max_time_diff):
# #     aligned_ref = []
# #     aligned_target = []

# #     target_timestamps = np.array([t for t, _ in target_data])
# #     used_indices = set()

# #     for ref_t, ref_pose in ref_data:
# #         diffs = np.abs(target_timestamps - ref_t)
# #         idx = np.argmin(diffs)
# #         if idx in used_indices:
# #             continue
# #         if diffs[idx] <= max_time_diff:
# #             aligned_ref.append((ref_t, ref_pose))
# #             aligned_target.append((target_data[idx][0], target_data[idx][1]))
# #             used_indices.add(idx)

# #     return aligned_ref, aligned_target

# # def plot_timestamps(ref_data, target_data, ref_label="Reference", tgt_label="Target"):
# #     ref_ts = [t for t, _ in ref_data]
# #     tgt_ts = [t for t, _ in target_data]

# #     plt.figure(figsize=(10, 4))
# #     plt.plot(ref_ts, label=ref_label)
# #     plt.plot(tgt_ts, label=tgt_label)
# #     plt.xlabel("Index")
# #     plt.ylabel("Timestamp (s)")
# #     plt.title("Timestamp Comparison (Before Alignment)")
# #     plt.legend()
# #     plt.grid(True)
# #     plt.tight_layout()
# #     plt.show()

# # if __name__ == "__main__":
# #     parser = argparse.ArgumentParser(description="Align two TUM trajectories based on timestamp.")
# #     parser.add_argument("ref", help="Reference trajectory (e.g., ground truth)")
# #     parser.add_argument("target", help="Target trajectory (e.g., SLAM estimate)")
# #     parser.add_argument("output_dir", help="Directory to save aligned output files")
# #     parser.add_argument("--ref-offset", type=float, default=0.0, help="Time offset to add to reference timestamps")
# #     parser.add_argument("--target-offset", type=float, default=0.0, help="Time offset to add to target timestamps")
# #     parser.add_argument("--max-time-diff", type=float, default=0.05, help="Maximum allowed timestamp difference for matching (in seconds)")
# #     parser.add_argument("--normalize", action="store_true", help="Normalize timestamps to start at 0")

# #     args = parser.parse_args()

# #     output_dir = Path(args.output_dir)
# #     output_dir.mkdir(parents=True, exist_ok=True)

# #     ref_data = load_tum_trajectory(args.ref)
# #     tgt_data = load_tum_trajectory(args.target)

# #     # ✅ Optional time offsets
# #     if args.ref_offset != 0.0:
# #         ref_data = [(t + args.ref_offset, pose) for t, pose in ref_data]
# #     if args.target_offset != 0.0:
# #         tgt_data = [(t + args.target_offset, pose) for t, pose in tgt_data]

# #     # ✅ Optional normalization
# #     if args.normalize:
# #         ref_data = normalize_timestamps(ref_data)
# #         tgt_data = normalize_timestamps(tgt_data)

# #     # ✅ Plot for inspection
# #     plot_timestamps(ref_data, tgt_data)

# #     # ✅ Align
# #     aligned_ref, aligned_tgt = align_trajectories(ref_data, tgt_data, max_time_diff=args.max_time_diff)

# #     if len(aligned_ref) == 0:
# #         print("❌ No matching timestamps found within the time window.")
# #     else:
# #         save_tum_trajectory(aligned_ref, output_dir / "aligned_ref.txt")
# #         save_tum_trajectory(aligned_tgt, output_dir / "aligned_target.txt")
# #         print(f"✅ {len(aligned_ref)} matched pairs saved.")
# #         print(f"📄 Aligned reference: {output_dir / 'aligned_ref.txt'}")
# #         print(f"📄 Aligned target:    {output_dir / 'aligned_target.txt'}")


# # import numpy as np
# # import argparse
# # from pathlib import Path
# # import matplotlib.pyplot as plt

# # def load_tum_trajectory(file_path):
# #     data = []
# #     with open(file_path, 'r') as f:
# #         for line in f:
# #             if line.strip() and not line.startswith('#'):
# #                 tokens = line.strip().split()
# #                 if len(tokens) == 8:
# #                     timestamp = float(tokens[0])
# #                     pose = list(map(float, tokens[1:]))
# #                     data.append((timestamp, pose))
# #     return data

# # def save_tum_trajectory(data, out_path):
# #     with open(out_path, 'w') as f:
# #         for t, pose in data:
# #             f.write(f"{t:.6f} {' '.join(f'{x:.6f}' for x in pose)}\n")

# # def align_trajectories(ref_data, target_data, max_time_diff):
# #     aligned_ref = []
# #     aligned_target = []

# #     target_timestamps = np.array([t for t, _ in target_data])
# #     used_indices = set()

# #     for ref_t, ref_pose in ref_data:
# #         diffs = np.abs(target_timestamps - ref_t)
# #         idx = np.argmin(diffs)
# #         if idx in used_indices:
# #             continue
# #         if diffs[idx] <= max_time_diff:
# #             aligned_ref.append((ref_t, ref_pose))
# #             aligned_target.append((target_data[idx][0], target_data[idx][1]))
# #             used_indices.add(idx)

# #     return aligned_ref, aligned_target

# # def plot_timestamps(ref_data, target_data, ref_label="Reference", tgt_label="Target"):
# #     ref_ts = [t for t, _ in ref_data]
# #     tgt_ts = [t for t, _ in target_data]

# #     plt.figure(figsize=(10, 4))
# #     plt.plot(ref_ts, label=ref_label)
# #     plt.plot(tgt_ts, label=tgt_label)
# #     plt.xlabel("Index")
# #     plt.ylabel("Timestamp (s)")
# #     plt.title("Timestamp Comparison (Before Alignment)")
# #     plt.legend()
# #     plt.grid(True)
# #     plt.tight_layout()
# #     plt.show()

# # if __name__ == "__main__":
# #     parser = argparse.ArgumentParser(description="Align two TUM trajectories based on timestamp.")
# #     parser.add_argument("ref", help="Reference trajectory file (e.g., ground truth)")
# #     parser.add_argument("target", help="Target trajectory file (e.g., SLAM estimate)")
# #     parser.add_argument("output_dir", help="Directory to save aligned output files")
# #     parser.add_argument("--ref-offset", type=float, default=0.0, help="Time offset to add to reference timestamps")
# #     parser.add_argument("--target-offset", type=float, default=0.0, help="Time offset to add to target timestamps")
# #     parser.add_argument("--max-time-diff", type=float, default=0.05, help="Max allowed timestamp difference for matching (in seconds)")

# #     args = parser.parse_args()

# #     output_dir = Path(args.output_dir)
# #     output_dir.mkdir(parents=True, exist_ok=True)

# #     ref_data = load_tum_trajectory(args.ref)
# #     tgt_data = load_tum_trajectory(args.target)

# #     # ✅ Apply time offsets if needed
# #     ref_data = [(t + args.ref_offset, pose) for t, pose in ref_data]
# #     tgt_data = [(t + args.target_offset, pose) for t, pose in tgt_data]

# #     # ✅ Visual check
# #     plot_timestamps(ref_data, tgt_data)

# #     # ✅ Match and align trajectories
# #     aligned_ref, aligned_tgt = align_trajectories(ref_data, tgt_data, args.max_time_diff)

# #     if not aligned_ref:
# #         print("❌ No matches found within time difference threshold.")
# #     else:
# #         save_tum_trajectory(aligned_ref, output_dir / "aligned_ref.txt")
# #         save_tum_trajectory(aligned_tgt, output_dir / "aligned_target.txt")
# #         print(f"✅ {len(aligned_ref)} matched pairs saved.")
# #         print(f"📄 Aligned reference: {output_dir / 'aligned_ref.txt'}")
# #         print(f"📄 Aligned target:    {output_dir / 'aligned_target.txt'}")


# # # # import numpy as np
# # # # import argparse
# # # # import os

# # # # def load_trajectory(file_path):
# # # #     traj = []
# # # #     with open(file_path, 'r') as f:
# # # #         for line in f:
# # # #             if line.strip() == "" or line.startswith("#"):
# # # #                 continue
# # # #             parts = line.strip().split()
# # # #             t = float(parts[0])
# # # #             pose = list(map(float, parts[1:]))
# # # #             traj.append((t, pose))
# # # #     return traj

# # # # def save_trajectory(path, traj):
# # # #     with open(path, 'w') as f:
# # # #         for t, pose in traj:
# # # #             f.write(f"{t:.6f} " + " ".join(f"{x:.7f}" for x in pose) + "\n")

# # # # def match_trajectories(ref_traj, tgt_traj, max_diff=None):
# # # #     matched_ref = []
# # # #     matched_tgt = []

# # # #     tgt_times = np.array([t for t, _ in tgt_traj])
# # # #     used_indices = set()

# # # #     for ref_time, ref_pose in ref_traj:
# # # #         diffs = np.abs(tgt_times - ref_time)
# # # #         tgt_idx = np.argmin(diffs)
# # # #         if tgt_idx in used_indices:
# # # #             continue  # avoid duplicates

# # # #         if max_diff is None or diffs[tgt_idx] <= max_diff:
# # # #             matched_ref.append((ref_time, ref_pose))
# # # #             matched_tgt.append((tgt_traj[tgt_idx][0], tgt_traj[tgt_idx][1]))
# # # #             used_indices.add(tgt_idx)

# # # #     return matched_ref, matched_tgt

# # # # if __name__ == "__main__":
# # # #     parser = argparse.ArgumentParser()
# # # #     parser.add_argument("ref", help="Reference trajectory (e.g. ground truth)")
# # # #     parser.add_argument("target", help="Target trajectory (e.g. SLAM estimate)")
# # # #     parser.add_argument("output_dir", help="Directory to save aligned files")
# # # #     parser.add_argument("--max-diff", type=float, default=None, help="Max timestamp diff (in seconds)")

# # # #     args = parser.parse_args()

# # # #     ref_traj = load_trajectory(args.ref)
# # # #     tgt_traj = load_trajectory(args.target)

# # # #     aligned_ref, aligned_tgt = match_trajectories(ref_traj, tgt_traj, args.max_diff)

# # # #     os.makedirs(args.output_dir, exist_ok=True)
# # # #     ref_path = os.path.join(args.output_dir, "aligned_ref.txt")
# # # #     tgt_path = os.path.join(args.output_dir, "aligned_target.txt")

# # # #     save_trajectory(ref_path, aligned_ref)
# # # #     save_trajectory(tgt_path, aligned_tgt)

# # # #     print(f"? Saved {len(aligned_ref)} aligned pairs.")
# # # #     print(f"?? Reference: {ref_path}")
# # # #     print(f"?? Target:    {tgt_path}")


# # # import numpy as np
# # # from pathlib import Path
# # # import matplotlib.pyplot as plt

# # # def load_tum_trajectory(file_path):
# # #     data = []
# # #     with open(file_path, 'r') as f:
# # #         for line in f:
# # #             if line.strip() and not line.startswith('#'):
# # #                 tokens = line.strip().split()
# # #                 if len(tokens) == 8:
# # #                     timestamp = float(tokens[0])
# # #                     pose = list(map(float, tokens[1:]))
# # #                     data.append((timestamp, pose))
# # #     return data

# # # # def align_trajectories(ref_data, target_data, max_time_diff=0.05):
# # # # def align_trajectories(ref_data, target_data, max_time_diff=1):
# # # def align_trajectories(ref_data, target_data, max_time_diff=50):
# # #     aligned_ref = []
# # #     aligned_target = []

# # #     target_timestamps = np.array([t for t, _ in target_data])

# # #     for ref_t, ref_pose in ref_data:
# # #         idx = np.argmin(np.abs(target_timestamps - ref_t))
# # #         closest_t = target_timestamps[idx]
# # #         time_diff = abs(closest_t - ref_t)

# # #         if time_diff <= max_time_diff:
# # #             aligned_ref.append((ref_t, ref_pose))
# # #             aligned_target.append((closest_t, target_data[idx][1]))

# # #     return aligned_ref, aligned_target

# # # def save_tum_trajectory(data, out_path):
# # #     with open(out_path, 'w') as f:
# # #         for t, pose in data:
# # #             f.write(f"{t:.6f} {' '.join(f'{x:.6f}' for x in pose)}\n")

# # # if __name__ == "__main__":
# # #     import argparse
# # #     parser = argparse.ArgumentParser()
# # #     parser.add_argument("ref", help="Reference trajectory (e.g. ground truth)")
# # #     parser.add_argument("target", help="Trajectory to align (e.g. SLAM output)")
# # #     parser.add_argument("output_dir", help="Directory to save aligned results")
# # #     parser.add_argument("--max_time_diff", type=float, default=0.05, help="Maximum timestamp difference")
# # #     args = parser.parse_args()

# # #     output_dir = Path(args.output_dir)
# # #     output_dir.mkdir(parents=True, exist_ok=True)

# # #     # ✅ Load trajectories
# # #     ref_data = load_tum_trajectory(args.ref)
# # #     target_data = load_tum_trajectory(args.target)

# # #     # ✅ Apply manual time offset (negative means shifting earlier)
# # #     time_offset = 2746.624  # Try -600, adjust further if needed
# # #     ref_data = [(t + time_offset, pose) for t, pose in ref_data]


# # #     # ✅ Plot timestamp comparison
# # #     ref_ts = [t for t, _ in ref_data]
# # #     target_ts = [t for t, _ in target_data]

# # #     plt.plot(ref_ts, label='Reference')
# # #     plt.plot(target_ts, label='Target')
# # #     plt.legend()
# # #     plt.title("Timestamp Comparison")
# # #     plt.xlabel("Index")
# # #     plt.ylabel("Time (s)")
# # #     plt.show()

# # #     # ✅ Try to align
# # #     aligned_ref, aligned_target = align_trajectories(ref_data, target_data, max_time_diff=args.max_time_diff)

# # #     if not aligned_ref:
# # #         print("? No matching timestamps found within the time window.")
# # #     else:
# # #         ref_out = output_dir / "aligned_ref.txt"
# # #         target_out = output_dir / "aligned_target.txt"

# # #         save_tum_trajectory(aligned_ref, ref_out)
# # #         save_tum_trajectory(aligned_target, target_out)

# # #         print(f"? Saved {len(aligned_ref)} aligned pairs.")
# # #         print(f"?? Reference: {ref_out}")
# # #         print(f"?? Target:    {target_out}")
