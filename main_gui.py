import os
import cv2
import threading
from tkinter import Tk, Button, Label, filedialog, StringVar
from video_processor import VideoProcessor
from csv_logger import CSVLogger
from datetime import timedelta

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

        # Controls
        Button(root, text="Open Video", command=self.open_video).pack()
        Button(root, text="Play/Pause", command=self.toggle_play).pack()
        Button(root, text="Log Event", command=self.log_event).pack()
        Button(root, text="Undo", command=self.undo).pack()
        Label(root, textvariable=self.status).pack()

    def open_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            self.video = cv2.VideoCapture(path)
            csv_path = os.path.splitext(path)[0] + ".csv"
            self.logger = CSVLogger(csv_path)
            self.status.set(f"Loaded: {os.path.basename(path)}")
            self.paused = True
            self.frame_pos = 0

    def toggle_play(self):
        if not self.video:
            self.status.set("No video loaded.")
            return
        self.paused = not self.paused
        if not self.paused:
            threading.Thread(target=self.play_video, daemon=True).start()

    def play_video(self):
        while not self.paused and self.video.isOpened():
            ret, frame = self.video.read()
            if not ret:
                self.status.set("End of video.")
                break
            cv2.imshow("Video", frame)
            if cv2.waitKey(int(30 / self.speed)) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    def log_event(self):
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

    def undo(self):
        if self.logger:
            try:
                self.logger.undo_last_entry()
                self.status.set("Last event undone.")
            except Exception as e:
                self.status.set(str(e))

if __name__ == "__main__":
    root = Tk()
    app = CarCounterGUI(root)
    root.mainloop()