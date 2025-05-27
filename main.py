import os
import cv2
from video_processor import VideoProcessor
from csv_logger import CSVLogger
from datetime import timedelta, datetime

def select_video(videos_dir):
    video_files = [f for f in os.listdir(videos_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not video_files:
        print("No video files found in the 'videos' folder.")
        return None
    print("Available videos:")
    for idx, video in enumerate(video_files, start=1):
        print(f"{idx}. {video}")
    while True:
        try:
            choice = int(input("Enter the number of the video you want to use: "))
            if 1 <= choice <= len(video_files):
                return video_files[choice - 1]
            else:
                print("Invalid choice. Please select a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def display_csv_entries(csv_path, num_entries=5):
    if not os.path.exists(csv_path):
        print("No observations yet.")
        return
    with open(csv_path, 'r') as f:
        lines = f.readlines()
        print("\nLatest Observations:")
        for line in lines[-num_entries:]:
            print(line.strip())

def parse_start_time(start_time_str):
    try:
        dt = datetime.strptime(start_time_str, "%H:%M:%S")
        return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second)
    except ValueError:
        print("Invalid time format. Please use HH:MM:SS.")
        return None

def format_timestamp(ms, start_offset):
    video_td = timedelta(milliseconds=ms)
    total_td = start_offset + video_td
    hours, remainder = divmod(total_td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = total_td.microseconds // 1000
    hours += total_td.days * 24
    return f"{hours:02}:{minutes:02}:{seconds:02}:{milliseconds:03}"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    videos_dir = os.path.join(script_dir, "videos")
    selected_video = select_video(videos_dir)
    if not selected_video:
        return

    video_path = os.path.join(videos_dir, selected_video)
    csv_path = os.path.join(script_dir, "output", f"{os.path.splitext(selected_video)[0]}.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    video = cv2.VideoCapture(video_path)
    logger = CSVLogger(csv_path)
    paused = True  # Start paused
    speed = 1  # 1x speed
    frame_pos = 0
    start_offset = timedelta()  # Default to zero

    print("\nControls: Space=Play/Pause | +/-=Speed | Arrows=Skip | , .=Frame | Any key=Log | Backspace=Undo & Pause | q=Quit\n")
    print("The video will start paused. When ready, press 's' to enter the start time (HH:MM:SS).")

    start_time_set = False

    while True:
        if not paused:
            ret, frame = video.read()
            if not ret:
                print("End of video.")
                break
            frame_pos = int(video.get(cv2.CAP_PROP_POS_FRAMES))
            cv2.imshow("Video", frame)
        else:
            # If paused, still show the current frame
            if int(video.get(cv2.CAP_PROP_POS_FRAMES)) != frame_pos:
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = video.read()
            if ret:
                cv2.imshow("Video", frame)
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)  # Stay on the same frame

        key = cv2.waitKey(0 if paused else int(30 / speed)) & 0xFF

        if key == ord(' '):  # Space: Play/Pause
            paused = not paused
        elif key == ord('='):  # Speed up
            speed = min(speed + 0.25, 4)
            print(f"Speed: {speed}x")
        elif key == ord('-'):  # Slow down
            speed = max(speed - 0.25, 0.25)
            print(f"Speed: {speed}x")
        elif key == 81:  # Left arrow: skip back 5s
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = max(0, frame_pos - int(fps * 5))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        elif key == 83:  # Right arrow: skip forward 5s
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, frame_pos + int(fps * 5))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        elif key == ord(','):  # Previous frame
            frame_pos = max(0, frame_pos - 1)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            paused = True
        elif key == ord('.'):  # Next frame
            frame_pos = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, frame_pos + 1)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            paused = True
        elif key == ord('s') and not start_time_set:  # Set start time
            paused = True
            while True:
                start_time_str = input("Enter the video start time (HH:MM:SS): ")
                offset = parse_start_time(start_time_str)
                if offset is not None:
                    start_offset = offset
                    start_time_set = True
                    print(f"Start time set to {start_time_str}.")
                    break
            paused = False
        elif key == 8:  # Backspace: Undo last observation and pause
            logger.undo_last_entry()
            print("Last observation removed.")
            paused = True
            display_csv_entries(csv_path)
        elif key == ord('q'):  # Quit
            break
        elif key != 255 and start_time_set:  # Any other key: log observation (only if start time set)
            ms = video.get(cv2.CAP_PROP_POS_MSEC)
            timestamp_str = format_timestamp(ms, start_offset)
            logger.log_entry(chr(key), timestamp_str)
            print(f"Logged: {chr(key)} at {timestamp_str}")
            display_csv_entries(csv_path)
        elif key != 255 and not start_time_set:
            print("Please set the start time first by pressing 's'.")

    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()