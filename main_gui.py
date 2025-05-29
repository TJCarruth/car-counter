import os
import cv2
import threading
from tkinter import Tk, Button, Label, filedialog, StringVar, Frame, Text, Scrollbar, RIGHT, Y, LEFT, BOTH, simpledialog, messagebox
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

        # Layout frame for video and log
        main_frame = Frame(root)
        main_frame.pack(fill=BOTH, expand=True)

        # Log display
        log_frame = Frame(main_frame)
        log_frame.pack(side=RIGHT, fill=Y, padx=10, pady=10)
        self.log_text = Text(log_frame, width=25, height=25, state='disabled')
        self.log_text.pack(side=LEFT, fill=Y)
        scrollbar = Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text['yscrollcommand'] = scrollbar.set

        # Video frame display
        self.frame_width = 640  # Default width
        self.frame_height = 480  # Default height
        black_img = Image.new('RGB', (self.frame_width, self.frame_height), color='black')
        self.blank_imgtk = ImageTk.PhotoImage(image=black_img)
        self.frame_label = Label(main_frame, image=self.blank_imgtk, bg='black')
        self.frame_label.imgtk = self.blank_imgtk  # Keep reference!
        self.frame_label.pack(side=LEFT, padx=10, pady=10)
        # Remove dynamic resizing
        # self.frame_label.bind('<Configure>', self.on_frame_resize)

        # Button row under video and log
        button_row = Frame(root)
        button_row.pack(fill='x', pady=(0, 10))
        # Open video button
        self.open_btn = Button(button_row, text="Open Video", command=self.open_video)
        self.open_btn.pack(side='left', padx=10)
        # Export Log button
        self.export_btn = Button(button_row, text="Export Log", command=self.export_log)
        self.export_btn.pack(side='right', padx=20)
        # Clear Log button
        self.clear_btn = Button(button_row, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side='right', padx=10)

        # Controls label inbtween the buttons
        self.controls_label = Label(button_row, text="", anchor='center')
        controls_text = (
            "Space=Play/Pause | +/-=Playbck Speed | , .=Frame Shift | ; '=Skip 5s | [ ]=Skip 5min | { }=Skip 1hr | "
            "Any letter=Log | Backspace=Undo | q=Quit"
        )
        self.controls_label = Label(button_row, text=controls_text, anchor='center')
        self.controls_label.pack(side='left', expand=True, fill='x')

        # Status label at the bottom
        self.status_label = Label(root)
        self.status_label.pack()
        self.update_status()

        # Prevent window from resizing automatically to fit widgets
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.maxsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.resizable(False, False)

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
        self.log_text.bind('<Button-1>', self.on_log_click)
        # Bind all alphabet keys to log_key_event
        for char in 'abcdefghijklmnopqrstuvwxyz':
            self.root.bind(f'<KeyPress-{char}>', self.log_key_event)
            self.root.bind(f'<KeyPress-{char.upper()}>', self.log_key_event)

    def open_video(self, event=None):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            self.video = cv2.VideoCapture(path)
            csv_path = os.path.splitext(path)[0] + ".csv"
            self.logger = CSVLogger(csv_path)
            self.paused = True
            self.frame_pos = 0
            # Do NOT call self.root.geometry or change window size here
            self.show_frame()
            self.update_log_display()
            # --- Start time logic (from main.py) ---
            video_basename = os.path.splitext(os.path.basename(path))[0]
            default_start_time = VideoProcessor.extract_default_start_time(video_basename)
            prompt = "Enter the video start time (HH:MM:SS)"
            if default_start_time:
                prompt += f" [default: {default_start_time}]"
            prompt += ":"
            # Use simpledialog to prompt user
            start_time_str = simpledialog.askstring("Start Time", prompt, initialvalue=default_start_time or "00:00:00", parent=self.root)
            if not start_time_str and default_start_time:
                start_time_str = default_start_time
            offset = VideoProcessor.parse_start_time(start_time_str) if start_time_str else None
            self.start_offset = offset if offset is not None else timedelta()
            # --- End start time logic ---
            self.show_frame()  # Show first frame
            self.update_log_display()

    def toggle_play(self, event=None):
        if not self.video:
            return
        self.paused = not self.paused
        if not self.paused:
            self.play_video()

    def play_video(self):
        if not self.paused and self.video and self.video.isOpened():
            ret, frame = self.video.read()
            if not ret:
                return
            self.show_frame(frame)
            delay = int(30 / self.speed)
            self.root.after(delay, self.play_video)

    def log_event(self, event=None):
        if not self.logger or not self.video:
            return
        frame_idx = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
        fps = self.video.get(cv2.CAP_PROP_FPS)
        seconds = frame_idx / fps if fps > 0 else 0
        ms = seconds * 1000
        timestamp_str = VideoProcessor.format_timestamp(ms, self.start_offset)
        self.logger.log_entry("event", timestamp_str)
        self.sort_log_file()
        self.update_log_display()

    def undo(self, event=None):
        if self.logger:
            # Get the currently highlighted line
            try:
                ranges = self.log_text.tag_ranges('highlight')
                if ranges:
                    start = ranges[0]
                    line_number = int(str(start).split('.')[0])
                    # Read all lines
                    with open(self.logger.filename, 'r') as f:
                        lines = [line for line in f if line.strip()]
                    if 1 <= line_number <= len(lines):
                        # Remove the highlighted line
                        del lines[line_number - 1]
                        with open(self.logger.filename, 'w') as f:
                            f.writelines(lines)
                        self.sort_log_file()
                else:
                    # Fallback: undo last entry
                    self.logger.undo_last_entry()
                    self.sort_log_file()
            except Exception:
                pass
            self.paused = True
            self.update_log_display()

    def show_frame(self, frame=None):
        if self.video and frame is None:
            ret, frame = self.video.read()
            if not ret:
                self.frame_label.config(image=self.blank_imgtk)
                self.frame_label.imgtk = self.blank_imgtk
                return
        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((self.frame_width, self.frame_height), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.frame_label.imgtk = imgtk
            self.frame_label.config(image=imgtk)
        else:
            self.frame_label.config(image=self.blank_imgtk)
            self.frame_label.imgtk = self.blank_imgtk

    def speed_up(self, event=None):
        self.speed = min(self.speed + 0.25, 10)

    def slow_down(self, event=None):
        self.speed = max(self.speed - 0.25, 0.25)

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

    def export_log(self):
        if not self.logger:
            return
        # Suggest a default name based on the video title
        if self.video_path:
            base = os.path.splitext(os.path.basename(self.video_path))[0]
            suggested_name = base + ".csv"
        else:
            suggested_name = "log.csv"
        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=suggested_name
        )
        if export_path:
            try:
                with open(self.logger.filename, 'r') as src, open(export_path, 'w') as dst:
                    dst.write(src.read())
            except Exception as e:
                pass

    def clear_log(self):
        if not self.logger:
            return
        confirm = messagebox.askyesno("Clear Log", "Are you sure you want to clear the log? This cannot be undone.")
        if confirm:
            # Overwrite the log file with nothing
            try:
                with open(self.logger.filename, 'w') as f:
                    f.write("")
                self.update_log_display()
            except Exception as e:
                pass

    def update_log_display(self, highlight_line=None):
        if self.logger:
            try:
                with open(self.logger.filename, 'r') as f:
                    log_content = f.read()
            except Exception:
                log_content = "No log file found."
        else:
            log_content = "No log file found."
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.insert('end', log_content)
        lines = log_content.splitlines()
        if lines:
            if highlight_line is None:
                highlight_line = len(lines)
            # Remove previous highlight
            self.log_text.tag_remove('highlight', '1.0', 'end')
            # Highlight the specified entry
            self.log_text.tag_add('highlight', f'{highlight_line}.0', f'{highlight_line}.end')
            self.log_text.tag_configure('highlight', background='yellow')
            # Center the display around the highlighted entry
            self.log_text.see(f'{highlight_line}.0')
        self.log_text.config(state='disabled')

    def update_status(self):
        speed_str = f"Speed: {self.speed}x"
        self.status_label.config(text=speed_str)
        self.root.after(200, self.update_status)

    def on_log_click(self, event):
        # Remove previous highlight
        self.log_text.tag_remove('highlight', '1.0', 'end')
        # Get the line number clicked
        index = self.log_text.index(f'@{event.x},{event.y}')
        line_number = int(index.split('.')[0])
        # Highlight the clicked line
        self.log_text.tag_add('highlight', f'{line_number}.0', f'{line_number}.end')
        self.log_text.tag_configure('highlight', background='yellow')
        # Get the line content
        line_content = self.log_text.get(f'{line_number}.0', f'{line_number}.end').strip()
        # Try to extract the timestamp (assumes format: timestamp, key)
        if ',' in line_content:
            timestamp_str = line_content.split(',')[0].strip()
        elif ':' in line_content:
            # If format is key, timestamp
            timestamp_str = line_content.split(':', 1)[1].strip()
        else:
            return
        # Parse the timestamp (expects HH:MM:SS:ms or HH:MM:SS)
        try:
            parts = timestamp_str.split(':')
            if len(parts) >= 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                ms = int(parts[3]) if len(parts) > 3 else 0
                total_seconds = hours * 3600 + minutes * 60 + seconds + ms / 1000.0
                # Subtract offset
                offset_seconds = self.start_offset.total_seconds() if self.start_offset else 0
                video_seconds = max(0, total_seconds - offset_seconds)
                if self.video:
                    fps = self.video.get(cv2.CAP_PROP_FPS)
                    frame = int(video_seconds * fps)
                    self.video.set(cv2.CAP_PROP_POS_FRAMES, frame)
                    self.paused = True
                    self.show_frame()
        except Exception:
            pass

    def sort_log_file(self):
        if not self.logger:
            return
        import re
        try:
            with open(self.logger.filename, 'r') as f:
                lines = [line for line in f if line.strip()]
            def parse_ts(line):
                if ',' in line:
                    ts = line.split(',')[0].strip()
                elif ':' in line:
                    ts = line.split(':', 1)[1].strip()
                else:
                    return float('inf')
                parts = re.split(r'[:]', ts)
                try:
                    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                    ms = int(parts[3]) if len(parts) > 3 else 0
                    return h * 3600 + m * 60 + s + ms / 1000.0
                except Exception:
                    return float('inf')
            lines.sort(key=parse_ts)
            with open(self.logger.filename, 'w') as f:
                f.writelines(lines)
        except Exception:
            pass

    def log_key_event(self, event):
        key = event.char
        if not key.isalpha():
            return
        frame_idx = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
        fps = self.video.get(cv2.CAP_PROP_FPS)
        seconds = frame_idx / fps if fps > 0 else 0
        ms = seconds * 1000
        timestamp_str = VideoProcessor.format_timestamp(ms, self.start_offset)
        self.logger.log_entry(key, timestamp_str)
        self.sort_log_file()
        # Find the line number of the just-logged event (match both timestamp and key)
        highlight_line = None
        try:
            with open(self.logger.filename, 'r') as f:
                lines = [line for line in f if line.strip()]
            for idx, line in enumerate(lines, 1):
                parts = line.strip().split(',')
                if len(parts) >= 2 and parts[0].strip() == timestamp_str and parts[1].strip() == key:
                    highlight_line = idx
                    break
        except Exception:
            highlight_line = None
        self.update_log_display(highlight_line=highlight_line)

if __name__ == "__main__":
    root = Tk()
    app = CarCounterGUI(root)
    root.mainloop()