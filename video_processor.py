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