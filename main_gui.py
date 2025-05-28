import os
import cv2
import threading
from tkinter import Tk, Button, Label, filedialog, StringVar
from video_processor import VideoProcessor
from csv_logger import CSVLogger
from datetime import timedelta
from PIL import Image, ImageTk

class CarCounterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Car Counter")
        self.paused = True
        self.speed = 1
        self.frame_pos = 0
        self.start_offset = timedelta()
        self.video = None
        self.logger = None
        self.video_path = ""
        self.status = StringVar()
        self.status.set("No video loaded.")

        # Video frame display
        self.frame_label = Label(root)
        self.frame_label.pack()

        # GUI Controls
        Button(root, text="Open Video", command=self.open_video).pack()
        Button(root, text="Play/Pause", command=self.toggle_play).pack()
        Button(root, text="Log Event", command=self.log_event).pack()
        Button(root, text="Undo", command=self.undo).pack()
        Label(root, textvariable=self.status).pack()

        # Keyboard shortcuts
        self.root.bind('<space>', self.toggle_play)
        self.root.bind('<KeyPress-equal>', self.speed_up)
        self.root.bind('<KeyPress-minus>', self.slow_down)
        self.root.bind('<comma>', self.prev_frame)
        self.root.bind('<period>', self.next_frame)
        self.root.bind('<semicolon>', self.skip_back_5s)
        self.root.bind("'", self.skip_forward_5s)
        self.root.bind('[', self.skip_back_5min)
        self.root.bind(']', self.skip_forward_5min)
        self.root.bind('{', self.skip_back_1hr)
        self.root.bind('}', self.skip_forward_1hr)
        self.root.bind('<BackSpace>', self.undo)

    def open_video(self, event=None):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            self.video = cv2.VideoCapture(path)
            csv_path = os.path.splitext(path)[0] + ".csv"
            self.logger = CSVLogger(csv_path)
            self.status.set(f"Loaded: {os.path.basename(path)}")
            self.paused = True
            self.frame_pos = 0
            self.show_frame()  # Show first frame

    def toggle_play(self, event=None):
        if not self.video:
            self.status.set("No video loaded.")
            return
        self.paused = not self.paused
        if not self.paused:
            self.play_video()

    def play_video(self):
        if not self.paused and self.video and self.video.isOpened():
            ret, frame = self.video.read()
            if not ret:
                self.status.set("End of video.")
                return
            self.show_frame(frame)
            delay = int(30 / self.speed)
            self.root.after(delay, self.play_video)

    def log_event(self, event=None):
        if not self.logger or not self.video:
            self.status.set("No video loaded.")
            return
        frame_idx = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
        fps = self.video.get(cv2.CAP_PROP_FPS)
        seconds = frame_idx / fps if fps > 0 else 0
        ms = seconds * 1000
        timestamp_str = VideoProcessor.format_timestamp(ms, self.start_offset)
        self.logger.log_entry("event", timestamp_str)
        self.status.set(f"Logged event at {timestamp_str}")

    def undo(self, event=None):
        if self.logger:
            try:
                self.logger.undo_last_entry()
                self.status.set("Last event undone.")
            except Exception as e:
                self.status.set(str(e))

    def show_frame(self, frame=None):
        if self.video:
            if frame is None:
                ret, frame = self.video.read()
                if not ret:
                    return
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.frame_label.imgtk = imgtk  # Keep reference!
            self.frame_label.config(image=imgtk)

    def speed_up(self, event=None):
        self.speed = min(self.speed + 0.25, 10)
        self.status.set(f"Speed: {self.speed}x")

    def slow_down(self, event=None):
        self.speed = max(self.speed - 0.25, 0.25)
        self.status.set(f"Speed: {self.speed}x")

    def prev_frame(self, event=None):
        if self.video:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, max(0, self.video.get(cv2.CAP_PROP_POS_FRAMES) - 1))
            self.paused = True
            self.show_frame()

    def next_frame(self, event=None):
        if self.video:
            frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video.set(cv2.CAP_PROP_POS_FRAMES, min(frame_count - 1, self.video.get(cv2.CAP_PROP_POS_FRAMES) + 1))
            self.paused = True
            self.show_frame()

    def skip_back_5s(self, event=None):
        if self.video:
            vp = self.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            self.show_frame()

    def skip_forward_5s(self, event=None):
        if self.video:
            vp = self.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            self.show_frame()

    def skip_back_5min(self, event=None):
        if self.video:
            vp = self.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 60 * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            self.show_frame()

    def skip_forward_5min(self, event=None):
        if self.video:
            vp = self.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 60 * 5))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            self.show_frame()

    def skip_back_1hr(self, event=None):
        if self.video:
            vp = self.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            new_pos = max(0, vp.get(cv2.CAP_PROP_POS_FRAMES) - int(fps * 60 * 60))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            self.show_frame()

    def skip_forward_1hr(self, event=None):
        if self.video:
            vp = self.video
            fps = vp.get(cv2.CAP_PROP_FPS)
            frame_count = int(vp.get(cv2.CAP_PROP_FRAME_COUNT))
            new_pos = min(frame_count - 1, vp.get(cv2.CAP_PROP_POS_FRAMES) + int(fps * 60 * 60))
            vp.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
            self.show_frame()

if __name__ == "__main__":
    root = Tk()
    app = CarCounterGUI(root)
    root.mainloop()