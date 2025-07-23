import imageio
import os

video_path = '/home/jay/my_video-3.mp4'
output_dir = '/home/jay/dev/datasets/map_frames'
os.makedirs(output_dir, exist_ok=True)

reader = imageio.get_reader(video_path)
fps = reader.get_meta_data()['fps']
timestamps = []

frame_idx = 0

while True:
    try:
        frame = reader.get_data(frame_idx)
        
        if frame_idx % 7 == 0:
            filename = f"{frame_idx:06d}.jpg"
            timestamp = frame_idx / fps
            imageio.imwrite(os.path.join(output_dir, filename), frame)
            timestamps.append(f"{timestamp:.6f} {filename}")
            print(f"✅ Extracted {len(timestamps)} frames (every 7th frame, JPG format).")

        frame_idx += 1

    except IndexError:
        # End of video
        break
    except Exception as e:
        print(f"❌ Error at frame {frame_idx}: {e}")
        break

with open(os.path.join(output_dir, "timestamps.txt"), "w") as f:
    f.write("\n".join(timestamps))

print(f"✅ Complete: Extracted {len(timestamps)} frames (every 7th frame, JPG format).")
