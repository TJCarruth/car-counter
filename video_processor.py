import cv2
import os
from datetime import timedelta, datetime
from PIL import Image, ImageTk

class VideoProcessor:
    @staticmethod
    def open_video(path):
        """
        Open a video file and return a cv2.VideoCapture object.
        """
        return cv2.VideoCapture(path)

    @staticmethod
    def toggle_play(gui, event=None):
        """
        Toggle play/pause state for the video. If unpausing, start playback.
        """
        if not gui.video:
            return
        gui.paused = not gui.paused
        if not gui.paused:
            VideoProcessor.play_video(gui)

    @staticmethod
    def play_video(gui):
        """
        Play the video by reading frames and updating the GUI at the current speed.
        """
        if not gui.paused and gui.video and gui.video.isOpened():
            ret, frame = gui.video.read()
            if not ret:
                return
            VideoProcessor.show_frame(gui, frame)
            delay = int(30 / gui.speed)
            gui.root.after(delay, lambda: VideoProcessor.play_video(gui))

    @staticmethod
    def show_frame(gui, frame=None):
        """
        Display a single video frame in the GUI. If no frame is provided, read the next frame from the video.
        """
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
    def speed_up(gui):
        """
        Increase playback speed, up to a maximum of 10x. Update the status label if present.
        """
        gui.speed = min(gui.speed + 0.25, 10)
        if hasattr(gui, 'status_label'):
            gui.status_label.config(text=f"{gui.speed}x")
        return gui.speed

    @staticmethod
    def slow_down(gui):
        """
        Decrease playback speed, down to a minimum of 0.25x. Update the status label if present.
        """
        gui.speed = max(gui.speed - 0.25, 0.25)
        if hasattr(gui, 'status_label'):
            gui.status_label.config(text=f"{gui.speed}x")
        return gui.speed

    @staticmethod
    def prev_frame(gui):
        """
        Move to the previous frame in the video and pause playback.
        """
        if gui.video:
            #checks the current frame, checks that it is not the first frame, and then sets the video to the previous frame
            gui.video.set(cv2.CAP_PROP_POS_FRAMES, max(0, gui.video.get(cv2.CAP_PROP_POS_FRAMES) - 2))
            gui.paused = True
            VideoProcessor.show_frame(gui)

    @staticmethod
    def next_frame(gui):
        """
        Move to the next frame in the video and pause playback.
        """
        if gui.video: # check if video is opened
            # checks the current frame, checks that it is not the last frame, and then sets the video to the next frame
            frame_count = int(gui.video.get(cv2.CAP_PROP_FRAME_COUNT)) # get total number of frames
            gui.video.set(cv2.CAP_PROP_POS_FRAMES, min(frame_count - 1, gui.video.get(cv2.CAP_PROP_POS_FRAMES) + 1))
            gui.paused = True
            VideoProcessor.show_frame(gui)

    @staticmethod
    def skip_back_5s(gui):
        """
        Skip backward 5 seconds in the video.
        """
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            VideoProcessor.show_frame(gui)

    @staticmethod
    def skip_forward_5s(gui):
        """
        Skip forward 5 seconds in the video.
        """
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            VideoProcessor.show_frame(gui)

    @staticmethod
    def skip_back_5min(gui):
        """
        Skip backward 5 minutes in the video.
        """
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 60 * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            VideoProcessor.show_frame(gui)

    @staticmethod
    def skip_forward_5min(gui):
        """
        Skip forward 5 minutes in the video.
        """
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 60 * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            VideoProcessor.show_frame(gui)

    @staticmethod
    def skip_back_1hr(gui):
        """
        Skip backward 1 hour in the video.
        """
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 60 * 60))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            VideoProcessor.show_frame(gui)

    @staticmethod
    def skip_forward_1hr(gui):
        """
        Skip forward 1 hour in the video.
        """
        if gui.video:
            vp = gui.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 60 * 60))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            VideoProcessor.show_frame(gui)

    @staticmethod
    def parse_start_time(start_time_str):
        """
        Parse a start time string in HH:MM:SS or 6-digit format and return a timedelta.
        """
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
        """
        Format a timestamp in milliseconds plus a start offset as HH:MM:SS:ms string.
        """
        video_td = timedelta(milliseconds=ms)
        total_td = start_offset + video_td
        hours, remainder = divmod(total_td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = total_td.microseconds // 1000
        hours += total_td.days * 24
        return f"{hours:02}:{minutes:02}:{seconds:02}:{milliseconds:03}"

    @staticmethod
    def extract_default_start_time(video_basename):
        """
        Extract the last 6 digits from a video filename to use as a default start time.
        """
        last_six = video_basename[-6:]
        return last_six if last_six.isdigit() else None