import cv2
import os
from datetime import timedelta, datetime
from PIL import Image, ImageTk

class VideoProcessor:
    @staticmethod
    def open_video(path):
        return cv2.VideoCapture(path)

    @staticmethod
    def play_video(gui):
        if not gui.paused and gui.video and gui.video.isOpened():
            ret, frame = gui.video.read()
            if not ret:
                return
            gui.show_frame(frame)
            delay = int(30 / gui.speed)
            gui.root.after(delay, lambda: VideoProcessor.play_video(gui))

    @staticmethod
    def show_frame(gui, frame=None):
        if gui.video and frame is None:
            ret, frame = gui.video.read()
            if not ret:
                gui.frame_label.config(image=gui.blank_imgtk)
                gui.frame_label.imgtk = gui.blank_imgtk
                return
        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((gui.frame_width, gui.frame_height), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            gui.frame_label.imgtk = imgtk
            gui.frame_label.config(image=imgtk)
        else:
            gui.frame_label.config(image=gui.blank_imgtk)
            gui.frame_label.imgtk = gui.blank_imgtk

    @staticmethod
    def speed_up(speed):
        return min(speed + 0.25, 10)

    @staticmethod
    def slow_down(speed):
        return max(speed - 0.25, 0.25)

    @staticmethod
    def prev_frame(gui):
        if gui.video:
            #checks the current frame, checks that it is not the first frame, and then sets the video to the previous frame
            gui.video.set(cv2.CAP_PROP_POS_FRAMES, max(0, gui.video.get(cv2.CAP_PROP_POS_FRAMES) - 2))
            gui.paused = True
            gui.show_frame()

    @staticmethod
    def next_frame(gui):
        if gui.video: # check if video is opened
            # checks the current frame, checks that it is not the last frame, and then sets the video to the next frame
            frame_count = int(gui.video.get(cv2.CAP_PROP_FRAME_COUNT)) # get total number of frames
            gui.video.set(cv2.CAP_PROP_POS_FRAMES, min(frame_count - 1, gui.video.get(cv2.CAP_PROP_POS_FRAMES) + 1))
            gui.paused = True
            gui.show_frame()

    @staticmethod
    def skip_back_5s(gui):
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            gui.show_frame()

    @staticmethod
    def skip_forward_5s(gui):
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            gui.show_frame()

    @staticmethod
    def skip_back_5min(gui):
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 60 * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            gui.show_frame()

    @staticmethod
    def skip_forward_5min(gui):
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 60 * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            gui.show_frame()

    @staticmethod
    def skip_back_1hr(gui):
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 60 * 60))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            gui.show_frame()

    @staticmethod
    def skip_forward_1hr(gui):
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 60 * 60))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            gui.show_frame()

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