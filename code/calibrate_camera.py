import imageio
import numpy as np
import cv2
import argparse
import os

parser = argparse.ArgumentParser(description="Camera calibration using a checkerboard video.")
parser.add_argument('--video', type=str, required=True, help='Path to checkerboard video')
parser.add_argument('--rows', type=int, default=6, help='Number of inner corners per column')
parser.add_argument('--cols', type=int, default=9, help='Number of inner corners per row')
parser.add_argument('--square_size', type=float, default=0.025, help='Checkerboard square size in meters')
parser.add_argument('--start_time', type=float, default=5.0, help='Start time in seconds')
parser.add_argument('--end_time', type=float, default=29.0, help='End time in seconds')

args = parser.parse_args()

CHECKERBOARD = (args.cols, args.rows)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= args.square_size

objpoints = []  # 3D points
imgpoints = []  # 2D points

video_path = os.path.expanduser(args.video)
reader = imageio.get_reader(video_path)

# fps = reader.get_meta_data().get('fps', 30)
# start_frame = int(args.start_time * fps)
# end_frame = int(args.end_time * fps)
# total_frames = reader.count_frames()

meta = reader.get_meta_data()
fps = meta.get('fps', 30)
duration = meta.get('duration', 0)
total_frames = int(duration * fps)

start_frame = int(args.start_time * fps)
end_frame = int(args.end_time * fps)


if start_frame >= total_frames or end_frame > total_frames:
    print(f"❌ Video too short. Total frames: {total_frames}, Requested end frame: {end_frame}")
    exit()

success_count = 0
gray = None  # Needed later for calibration size

for frame_idx, frame in enumerate(reader):
    if frame_idx < start_frame:
        print("continue...")
        continue
    if frame_idx > end_frame:
        break

    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    ret_corners, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if ret_corners:
        objpoints.append(objp)
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners_refined)
        success_count += 1
        cv2.drawChessboardCorners(frame_bgr, CHECKERBOARD, corners_refined, ret_corners)

    cv2.imshow('Checkerboard Detection', frame_bgr)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

if success_count < 5:
    print("❌ Not enough valid frames for calibration. Found:", success_count)
    exit()

ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print("\n✅ Calibration successful!\n")
print("Camera Matrix (K):")
print(K)
print("\nDistortion Coefficients:")
print(dist.ravel())


# import cv2
# import numpy as np
# import argparse
# import imageio

# parser = argparse.ArgumentParser(description="Camera calibration using a checkerboard video.")
# parser.add_argument('--video', type=str, required=True, help='Path to checkerboard video')
# parser.add_argument('--rows', type=int, default=6, help='Number of inner corners per column')
# parser.add_argument('--cols', type=int, default=9, help='Number of inner corners per row')
# parser.add_argument('--square_size', type=float, default=0.025, help='Checkerboard square size in meters')
# parser.add_argument('--start_time', type=float, default=5.0, help='Start time in seconds')
# parser.add_argument('--end_time', type=float, default=29.0, help='End time in seconds')

# args = parser.parse_args()

# CHECKERBOARD = (args.cols, args.rows)
# criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
# objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
# objp *= args.square_size

# objpoints = []  # 3D points
# imgpoints = []  # 2D points

# cap = cv2.VideoCapture(args.video)
# fps = cap.get(cv2.CAP_PROP_FPS)
# start_frame = int(args.start_time * fps)
# end_frame = int(args.end_time * fps)
# total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# if start_frame >= total_frames or end_frame > total_frames:
#     print(f"❌ Video too short. Total frames: {total_frames}, Requested end frame: {end_frame}")
#     cap.release()
#     exit()

# cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

# frame_idx = start_frame
# success_count = 0

# while frame_idx <= end_frame:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     ret_corners, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

#     if ret_corners:
#         objpoints.append(objp)
#         corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
#         imgpoints.append(corners_refined)
#         success_count += 1
#         cv2.drawChessboardCorners(frame, CHECKERBOARD, corners_refined, ret_corners)
    
#     cv2.imshow('Checkerboard Detection', frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

#     frame_idx += 1

# cap.release()
# cv2.destroyAllWindows()

# if success_count < 5:
#     print("❌ Not enough valid frames for calibration. Found:", success_count)
#     exit()

# ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# print("\n✅ Calibration successful!\n")
# print("Camera Matrix (K):")
# print(K)
# print("\nDistortion Coefficients:")
# print(dist.ravel())


# # # import cv2
# # # import numpy as np
# # # import argparse

# # # parser = argparse.ArgumentParser(description="Camera calibration using a checkerboard video.")
# # # parser.add_argument('--video', type=str, required=True, help='Path to checkerboard video')
# # # parser.add_argument('--rows', type=int, default=6, help='Number of inner corners per column')
# # # parser.add_argument('--cols', type=int, default=9, help='Number of inner corners per row')
# # # parser.add_argument('--square_size', type=float, default=0.025, help='Checkerboard square size in meters')

# # # args = parser.parse_args()

# # # CHECKERBOARD = (args.cols, args.rows)
# # # criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# # # objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
# # # objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
# # # objp *= args.square_size

# # # objpoints = []  # 3D points
# # # imgpoints = []  # 2D points

# # # cap = cv2.VideoCapture(args.video)
# # # frame_count = 0
# # # success = 0

# # # while True:
# # #     ret, frame = cap.read()
# # #     if not ret:
# # #         break
# # #     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# # #     ret_corners, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
# # #     frame_count += 1

# # #     if ret_corners:
# # #         objpoints.append(objp)
# # #         corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
# # #         imgpoints.append(corners_refined)
# # #         success += 1
# # #         cv2.drawChessboardCorners(frame, CHECKERBOARD, corners_refined, ret_corners)
# # #         cv2.imshow('Checkerboard', frame)
# # #         if cv2.waitKey(1) & 0xFF == ord('q'):
# # #             break

# # # cap.release()
# # # cv2.destroyAllWindows()

# # # if success < 5:
# # #     print("❌ Not enough valid frames for calibration. Found:", success)
# # #     exit()

# # # ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# # # print("\n✅ Calibration successful!\n")
# # # print("Camera Matrix (K):")
# # # print(K)
# # # print("\nDistortion Coefficients:")
# # # print(dist.ravel())
