import os
import cv2
import threading
from tkinter import Tk, Button, Label, filedialog, StringVar, Frame, Text, Scrollbar, RIGHT, Y, LEFT, BOTH, simpledialog, messagebox, Toplevel
from video_processor import VideoProcessor
from csv_logger import CSVLogger
from datetime import timedelta
from PIL import Image, ImageTk

class CarCounterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Car Counter")
        # Playback and state variables
        self.paused = True
        self.speed = 1
        self.frame_pos = 0
        self.start_offset = timedelta()
        self.video = None
        self.logger = None
        self.video_path = ""
        self.undo_stack = []  # Stack of (entry, index) for undo
        self.redo_stack = []  # Stack of (entry, index) for redo

        # --- GUI Layout ---
        # Main frame contains video and log
        main_frame = Frame(root)
        main_frame.pack(fill=BOTH, expand=True)

        # Log display (right side)
        log_frame = Frame(main_frame)
        log_frame.pack(side=RIGHT, fill=Y, padx=10, pady=10)
        self.log_text = Text(log_frame, width=20, height=25, state='disabled')  # Shows event log
        self.log_text.pack(side=LEFT, fill=Y)
        scrollbar = Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text['yscrollcommand'] = scrollbar.set

        # Video display (left side)
        self.frame_width = 640  # Default video frame width
        self.frame_height = 480  # Default video frame height
        black_img = Image.new('RGB', (self.frame_width, self.frame_height), color='black')
        self.blank_imgtk = ImageTk.PhotoImage(image=black_img)
        self.frame_label = Label(main_frame, image=self.blank_imgtk, bg='black')  # Where video frames are shown
        self.frame_label.imgtk = self.blank_imgtk  # Keep reference to avoid garbage collection
        self.frame_label.pack(side=LEFT, padx=10, pady=10)

        # Controls container (vertical stack of buttons and controls)
        controls_container = Frame(main_frame)
        controls_container.pack(side=LEFT, fill=Y, padx=5, pady=10)
        controls_container.pack(fill='y', expand=True)

        # --- Control Buttons ---
        # Instructions button opens README in a new window
        self.instructions_btn = Button(controls_container, text="Instructions", command=self.show_instructions)
        self.instructions_btn.pack(side='top', pady=(0, 8), fill='x')

        # Open Video button lets user select a video file
        self.open_btn = Button(controls_container, text="Open Video", command=self.open_video)
        self.open_btn.pack(side='top', pady=(0, 16), fill='x')

        # Video playback controls (play, pause, speed, frame navigation, skip)
        kb_btn_frame = Frame(controls_container)
        kb_btn_frame.pack(side='top', pady=(16, 16), fill='x')
        Button(kb_btn_frame, text="Play/Pause", command=lambda: VideoProcessor.toggle_play(self)).pack(side='top', pady=1, fill='x')
        speed_frame = Frame(kb_btn_frame)
        speed_frame.pack(fill='x', pady=1)
        Button(speed_frame, text="Speed -", command=lambda: VideoProcessor.slow_down(self)).pack(side='left', expand=True, fill='x')
        self.status_label = Label(speed_frame, anchor='center', width=5)  # Shows current speed
        self.status_label.pack(side='left', padx=4, fill='x', expand=True)
        Button(speed_frame, text="Speed +", command=lambda: VideoProcessor.speed_up(self)).pack(side='left', expand=True, fill='x')
        # Frame navigation
        frame_frame = Frame(kb_btn_frame)
        frame_frame.pack(fill='x', pady=1)
        Button(frame_frame, text="Prev Frame", command=lambda: VideoProcessor.prev_frame(self)).pack(side='left', expand=True, fill='x')
        Button(frame_frame, text="Next Frame", command=lambda: VideoProcessor.next_frame(self)).pack(side='left', expand=True, fill='x')
        # Skip 5s
        skip5s_frame = Frame(kb_btn_frame)
        skip5s_frame.pack(fill='x', pady=1)
        Button(skip5s_frame, text="Skip -5s", command=lambda: VideoProcessor.skip_back_5s(self)).pack(side='left', expand=True, fill='x')
        Button(skip5s_frame, text="Skip +5s", command=lambda: VideoProcessor.skip_forward_5s(self)).pack(side='left', expand=True, fill='x')
        # Skip 5min
        skip5min_frame = Frame(kb_btn_frame)
        skip5min_frame.pack(fill='x', pady=1)
        Button(skip5min_frame, text="Skip -5min", command=lambda: VideoProcessor.skip_back_5min(self)).pack(side='left', expand=True, fill='x')
        Button(skip5min_frame, text="Skip +5min", command=lambda: VideoProcessor.skip_forward_5min(self)).pack(side='left', expand=True, fill='x')
        # Skip 1hr
        skip1hr_frame = Frame(kb_btn_frame)
        skip1hr_frame.pack(fill='x', pady=1)
        Button(skip1hr_frame, text="Skip -1hr", command=lambda: VideoProcessor.skip_back_1hr(self)).pack(side='left', expand=True, fill='x')
        Button(skip1hr_frame, text="Skip +1hr", command=lambda: VideoProcessor.skip_forward_1hr(self)).pack(side='left', expand=True, fill='x')

        # Log-related controls (export, clear, undo/redo, search, delete)
        log_btn_frame = Frame(controls_container)
        log_btn_frame.pack(side='top', pady=(40, 16), fill='x')
        self.export_btn = Button(log_btn_frame, text="Export Log", command=lambda: self.logger.export_log(self))  # Export log to CSV
        self.export_btn.pack(side='top', pady=2, fill='x')
        self.clear_btn = Button(log_btn_frame, text="Clear Log", command=lambda: self.logger.clear_log(self))    # Clear log
        self.clear_btn.pack(side='top', pady=2, fill='x')
        undo_frame = Frame(log_btn_frame)
        undo_frame.pack(fill='x', pady=1)
        Button(undo_frame, text="Undo", command=lambda: self.logger.restore_last_undo(self)).pack(side='left', expand=True, fill='x')
        Button(undo_frame, text="Redo", command=lambda: self.logger.redo(self)).pack(side='left', expand=True, fill='x')
        Button(log_btn_frame, text="Search Log", command=self.prompt_search_log).pack(side='top', pady=2, fill='x')  # Search log entries
        Button(log_btn_frame, text="Delete Entry", command=lambda: self.logger.undo(self)).pack(side='bottom', pady=2, fill='x')  # Delete last entry

        # Quit button at the very bottom
        Button(controls_container, text="Save and Quit", command=self.root.quit).pack(side='bottom', pady=16, fill='x')

        # Prevent window from resizing automatically to fit widgets
        # Had issues with the window continuously resizing
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.maxsize(self.root.winfo_width(), self.root.winfo_height())
        self.root.resizable(False, False)

        # --- Keyboard Shortcuts ---
        # Video controls
        self.root.bind('<space>', lambda e: VideoProcessor.toggle_play(self))           # Space: play/pause
        self.root.bind('<KeyPress-equal>', lambda e: VideoProcessor.speed_up(self))     # =: speed up
        self.root.bind('<KeyPress-minus>', lambda e: VideoProcessor.slow_down(self))    # -: slow down
        self.root.bind('<comma>', lambda e: VideoProcessor.prev_frame(self))            # ,: previous frame
        self.root.bind('<period>', lambda e: VideoProcessor.next_frame(self))           # .: next frame
        self.root.bind('<semicolon>', lambda e: VideoProcessor.skip_back_5s(self))      # ;: skip back 5s
        self.root.bind("'", lambda e: VideoProcessor.skip_forward_5s(self))            # ': skip forward 5s
        self.root.bind('[', lambda e: VideoProcessor.skip_back_5min(self))              # [: skip back 5min
        self.root.bind(']', lambda e: VideoProcessor.skip_forward_5min(self))           # ]: skip forward 5min
        self.root.bind('{', lambda e: VideoProcessor.skip_back_1hr(self))               # {: skip back 1hr
        self.root.bind('}', lambda e: VideoProcessor.skip_forward_1hr(self))            # }: skip forward 1hr
        # Log controls
        self.root.bind('<BackSpace>', lambda e: self.logger.undo(self))                 # Backspace: delete last entry
        self.root.bind('<Control-z>', lambda e: self.logger.restore_last_undo(self))    # Ctrl+Z: undo
        self.root.bind('<Control-y>', lambda e: self.logger.redo(self))                 # Ctrl+Y: redo
        self.log_text.bind('<Button-1>', self.on_log_click)                             # Click log: highlight entry
        self.root.bind('<Escape>', lambda e: self.root.quit())                          # Escape: quit
        # Bind all alphabet keys to log_key_event (for event logging)
        for char in 'abcdefghijklmnopqrstuvwxyz':
            self.root.bind(f'<KeyPress-{char}>', self.log_key_event)
            self.root.bind(f'<KeyPress-{char.upper()}>', self.log_key_event)

## GUI Functions ##########################################################

    def open_video(self, event=None):
        """
        Opens a file dialog for the user to select a video file. Initializes the video processor and logger,
        prompts for the video start time, and displays the first frame and log.
        """
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

    def update_log_display(self, highlight_line=None, highlight_lines=None):
        """
        Updates the log display area with the contents of the log file. Optionally highlights a specific line or lines.
        """
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
        self.log_text.tag_remove('highlight', '1.0', 'end')
        # If highlight_lines is provided, highlight all those lines
        if highlight_lines:
            for line_num in highlight_lines:
                self.log_text.tag_add('highlight', f'{line_num}.0', f'{line_num}.end')
            self.log_text.tag_configure('highlight', background='yellow')
            self.log_text.see(f'{highlight_lines[0]}.0')
        # Otherwise, if highlight_line is provided, highlight that single line
        elif highlight_line is not None:
            self.log_text.tag_add('highlight', f'{highlight_line}.0', f'{highlight_line}.end')
            self.log_text.tag_configure('highlight', background='yellow')
            self.log_text.see(f'{highlight_line}.0')
        self.log_text.config(state='disabled')

    def on_log_click(self, event):
        """
        Handles clicks on the log display. Highlights the clicked line and seeks the video to the corresponding timestamp.
        """
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
        """
        Handles key press events for logging. Logs the key and current timestamp to the CSV, updates the log display,
        and highlights the new entry.
        """
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

    def prompt_search_log(self):
        """
        Prompts the user for a search term and highlights all matching entries in the log display.
        This, and the .search_entries method in CSVLogger, are very basic. Use excel or similar for more advanced searching.
        """
        search_term = simpledialog.askstring("Search Log", "Enter search term:", parent=self.root)
        if search_term and self.logger:
            self.logger.search_entries(search_term, self)

    def show_instructions(self):
        """
        Opens a new window and displays the contents of README.md as instructions for the user.
        """
        instructions_win = Toplevel(self.root)
        instructions_win.title("Instructions")
        instructions_win.geometry("700x600")
        text_widget = Text(instructions_win, wrap='word')
        text_widget.pack(fill='both', expand=True)
        scrollbar = Scrollbar(text_widget, command=text_widget.yview)
        text_widget['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side=RIGHT, fill=Y)
        try:
            with open("README.md", "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"Could not load instructions: {e}"
        text_widget.insert('1.0', content)
        text_widget.config(state='disabled')

if __name__ == "__main__":
    root = Tk()
    app = CarCounterGUI(root)
    root.mainloop()