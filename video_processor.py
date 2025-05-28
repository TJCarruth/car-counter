import cv2
import os
from datetime import timedelta, datetime

class VideoProcessor:
    def __init__(self, video_path):
        self.video_capture = cv2.VideoCapture(video_path)
        if not self.video_capture.isOpened():
            raise ValueError(f"Unable to open video file: {video_path}")

    @staticmethod
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

    @staticmethod
    def parse_start_time(start_time_str):
        # Accepts a string in HH:MM:SS or an integer/str with 6 digits (e.g. 000003 for 00:00:03)
        try:
            if start_time_str.isdigit() and len(start_time_str) == 6:
                # Parse as HHMMSS
                hours = int(start_time_str[:2])
                minutes = int(start_time_str[2:4])
                seconds = int(start_time_str[4:6])
                return timedelta(hours=hours, minutes=minutes, seconds=seconds)
            else:
                dt = datetime.strptime(start_time_str, "%H:%M:%S")
                return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second)
        except ValueError:
            print("Invalid time format. Please use HH:MM:SS or a 6-digit timestamp (HHMMSS).")
            return None

    @staticmethod
    def format_timestamp(ms, start_offset):
        video_td = timedelta(milliseconds=ms)
        total_td = start_offset + video_td
        hours, remainder = divmod(total_td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = total_td.microseconds // 1000
        hours += total_td.days * 24
        return f"{hours:02}:{minutes:02}:{seconds:02}:{milliseconds:03}"

    @staticmethod
    def extract_default_start_time(video_basename):
        # Extract last 6 digits from video name (before extension) to use as default start time
        last_six = video_basename[-6:]
        return last_six if last_six.isdigit() else None

    def get_frame(self):
        ret, frame = self.video_capture.read()
        if not ret:
            return None
        return frame

    def display_frame(self, frame):
        cv2.imshow("Video", frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):  # Add a 10ms delay
            return False
        return True

    def release(self):
        self.video_capture.release()
        cv2.destroyAllWindows()

    def skip_frames(self, num_frames):
        # Move forward or backward by num_frames (can be negative)
        current_pos = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES))
        frame_count = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        new_pos = min(max(0, current_pos + num_frames), frame_count - 1)
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
        return new_pos

    def skip_seconds(self, seconds):
        # Move forward or backward by a number of seconds (can be negative)
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        frames_to_skip = int(fps * seconds)
        return self.skip_frames(frames_to_skip)

    def skip_minutes(self, minutes):
        return self.skip_seconds(minutes * 60)

    def skip_hours(self, hours):
        return self.skip_seconds(hours * 3600)

    def get_frame_pos(self):
        return int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES))

    def set_frame_pos(self, pos):
        frame_count = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        pos = min(max(0, pos), frame_count - 1)
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, pos)
        return pos

    def get_fps(self):
        return self.video_capture.get(cv2.CAP_PROP_FPS)

    def get_frame_count(self):
        return int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))