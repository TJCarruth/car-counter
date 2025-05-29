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
        self.last_removed_entry = None
        self.last_removed_index = None
        self.undo_stack = []  # Stack of (entry, index)
        self.redo_stack = []  # Stack of (entry, index)

        # Layout frame for video and log
        main_frame = Frame(root)
        main_frame.pack(fill=BOTH, expand=True)

        # Log display
        log_frame = Frame(main_frame)
        log_frame.pack(side=RIGHT, fill=Y, padx=10, pady=10)
        self.log_text = Text(log_frame, width=20, height=25, state='disabled')
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

        # --- Side panel between video and log ---
        side_panel = Frame(main_frame)
        side_panel.pack(side=LEFT, fill=Y, padx=5, pady=10)

        # --- Keybinding buttons regrouped and evenly spaced ---
        # Use a vertical container for all control groups
        controls_container = Frame(side_panel)
        controls_container.pack(fill='y', expand=True)

        # Open Video at the very top
        self.open_btn = Button(controls_container, text="Open Video", command=self.open_video)
        self.open_btn.pack(side='top', pady=(0, 16), fill='x')

        # Video playback controls (grouped)
        kb_btn_frame = Frame(controls_container)
        kb_btn_frame.pack(side='top', pady=(16, 16), fill='x')
        Button(kb_btn_frame, text="Play/Pause", command=lambda: VideoProcessor.toggle_play(self)).pack(side='top', pady=1, fill='x')
        speed_frame = Frame(kb_btn_frame)
        speed_frame.pack(fill='x', pady=1)
        Button(speed_frame, text="Speed -", command=lambda: VideoProcessor.slow_down(self)).pack(side='left', expand=True, fill='x')
        self.status_label = Label(speed_frame, anchor='center', width=5)
        self.status_label.pack(side='left', padx=4, fill='x', expand=True)
        Button(speed_frame, text="Speed +", command=lambda: VideoProcessor.speed_up(self)).pack(side='left', expand=True, fill='x')
        # Frame shift side by side
        frame_frame = Frame(kb_btn_frame)
        frame_frame.pack(fill='x', pady=1)
        Button(frame_frame, text="Prev Frame", command=lambda: VideoProcessor.prev_frame(self)).pack(side='left', expand=True, fill='x')
        Button(frame_frame, text="Next Frame", command=lambda: VideoProcessor.next_frame(self)).pack(side='left', expand=True, fill='x')
        # Skip 5s side by side
        skip5s_frame = Frame(kb_btn_frame)
        skip5s_frame.pack(fill='x', pady=1)
        Button(skip5s_frame, text="Skip -5s", command=lambda: VideoProcessor.skip_back_5s(self)).pack(side='left', expand=True, fill='x')
        Button(skip5s_frame, text="Skip +5s", command=lambda: VideoProcessor.skip_forward_5s(self)).pack(side='left', expand=True, fill='x')
        # Skip 5min side by side
        skip5min_frame = Frame(kb_btn_frame)
        skip5min_frame.pack(fill='x', pady=1)
        Button(skip5min_frame, text="Skip -5min", command=lambda: VideoProcessor.skip_back_5min(self)).pack(side='left', expand=True, fill='x')
        Button(skip5min_frame, text="Skip +5min", command=lambda: VideoProcessor.skip_forward_5min(self)).pack(side='left', expand=True, fill='x')
        # Skip 1hr side by side
        skip1hr_frame = Frame(kb_btn_frame)
        skip1hr_frame.pack(fill='x', pady=1)
        Button(skip1hr_frame, text="Skip -1hr", command=lambda: VideoProcessor.skip_back_1hr(self)).pack(side='left', expand=True, fill='x')
        Button(skip1hr_frame, text="Skip +1hr", command=lambda: VideoProcessor.skip_forward_1hr(self)).pack(side='left', expand=True, fill='x')

        # Log-related buttons (grouped)
        log_btn_frame = Frame(controls_container)
        log_btn_frame.pack(side='bottom', pady=(16, 16), fill='x')
        self.export_btn = Button(log_btn_frame, text="Export Log", command=lambda: self.logger.export_log(self))
        self.export_btn.pack(side='top', pady=2, fill='x')
        self.clear_btn = Button(log_btn_frame, text="Clear Log", command=lambda: self.logger.clear_log(self))
        self.clear_btn.pack(side='top', pady=2, fill='x')
        undo_frame = Frame(log_btn_frame)
        undo_frame.pack(fill='x', pady=1)
        Button(undo_frame, text="Undo", command=lambda: self.logger.restore_last_undo(self)).pack(side='left', expand=True, fill='x')
        Button(undo_frame, text="Redo", command=lambda: self.logger.redo(self)).pack(side='left', expand=True, fill='x')
        Button(log_btn_frame, text="Delete Entry", command=lambda: self.logger.undo(self)).pack(side='top', pady=2, fill='x')

        # Quit button at the very bottom, spaced from above
        Button(side_panel, text="Save and Quit", command=self.root.quit).pack(side='bottom', pady=16, fill='x')

        # Prevent window from resizing automatically to fit widgets
        # Had issues with the window continuously resizing
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.maxsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.resizable(False, False)

        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: VideoProcessor.toggle_play(self))
        self.root.bind('<KeyPress-equal>', lambda e: VideoProcessor.speed_up(self))
        self.root.bind('<KeyPress-minus>', lambda e: VideoProcessor.slow_down(self))
        self.root.bind('<comma>', lambda e: VideoProcessor.prev_frame(self))
        self.root.bind('<period>', lambda e: VideoProcessor.next_frame(self))
        self.root.bind('<semicolon>', lambda e: VideoProcessor.skip_back_5s(self))
        self.root.bind("'", lambda e: VideoProcessor.skip_forward_5s(self))
        self.root.bind('[', lambda e: VideoProcessor.skip_back_5min(self))
        self.root.bind(']', lambda e: VideoProcessor.skip_forward_5min(self))
        self.root.bind('{', lambda e: VideoProcessor.skip_back_1hr(self))
        self.root.bind('}', lambda e: VideoProcessor.skip_forward_1hr(self))
        self.root.bind('<BackSpace>', lambda e: self.logger.undo(self))
        self.root.bind('<Control-z>', lambda e: self.logger.restore_last_undo(self))  # Ctrl+Z for undo
        self.root.bind('<Control-y>', lambda e: self.logger.redo(self))  # Ctrl+Y for redo
        self.log_text.bind('<Button-1>', self.on_log_click)
        self.root.bind('<Escape>', lambda e: self.root.quit())  # Escape key to quit
        # Bind all alphabet keys to log_key_event
        for char in 'abcdefghijklmnopqrstuvwxyz':
            self.root.bind(f'<KeyPress-{char}>', self.log_key_event)
            self.root.bind(f'<KeyPress-{char.upper()}>', self.log_key_event)

## GUI Functions ##########################################################

    def open_video(self, event=None):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            self.video = VideoProcessor.open_video(path)
            csv_path = os.path.splitext(path)[0] + ".csv"
            self.logger = CSVLogger(csv_path)
            self.paused = True
            self.frame_pos = 0
            VideoProcessor.show_frame(self)
            self.update_log_display()
            # --- Start time logic (from main.py) ---
            video_basename = os.path.splitext(os.path.basename(path))[0]
            default_start_time = VideoProcessor.extract_default_start_time(video_basename)
            prompt = "Enter the video start time (HH:MM:SS)"
            if default_start_time:
                prompt += f" [default: {default_start_time}]"
            prompt += ":"
            start_time_str = simpledialog.askstring("Start Time", prompt, initialvalue=default_start_time or "00:00:00", parent=self.root)
            if not start_time_str and default_start_time:
                start_time_str = default_start_time
            offset = VideoProcessor.parse_start_time(start_time_str) if start_time_str else None
            self.start_offset = offset if offset is not None else timedelta()
            VideoProcessor.show_frame(self)  # Show first frame
            self.update_log_display()

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
                    VideoProcessor.show_frame(self)
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
        self.logger.sort_log_file()
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