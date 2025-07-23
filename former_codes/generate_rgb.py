import os

# Point to the actual dataset folder
# data_dir = os.path.expanduser("~/dev/datasets/video_frames")
data_dir = os.path.expanduser("~/dev/datasets/map_frames")
timestamps_file = os.path.join(data_dir, "timestamps.txt")
output_file = os.path.join(data_dir, "rgb.txt")

# Read timestamps
with open(timestamps_file, "r") as f:
    timestamps = [line.strip() for line in f if line.strip()]

# Get sorted image files
# image_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".png")])
image_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".jpg")])

if len(timestamps) != len(image_files):
    print(f"❌ Mismatch: {len(timestamps)} timestamps vs {len(image_files)} images")
    exit()

# Write rgb.txt
with open(output_file, "w") as f:
    f.write("# timestamp filename\n")
    for ts, img in zip(timestamps, image_files):
        f.write(f"{ts} {img}\n")

print("✅ rgb.txt created successfully at", output_file)
