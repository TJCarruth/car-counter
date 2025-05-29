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
        Button(kb_btn_frame, text="Play/Pause", command=self.toggle_play).pack(side='top', pady=1, fill='x')
        speed_frame = Frame(kb_btn_frame)
        speed_frame.pack(fill='x', pady=1)
        Button(speed_frame, text="Speed +", command=self.speed_up).pack(side='left', expand=True, fill='x')
        Button(speed_frame, text="Speed -", command=self.slow_down).pack(side='left', expand=True, fill='x')
        # Status label next to speed buttons
        self.status_label = Label(speed_frame)
        self.status_label.pack(side='left', padx=(8,0), fill='x')
        self.update_status()
        # Frame shift side by side
        frame_frame = Frame(kb_btn_frame)
        frame_frame.pack(fill='x', pady=1)
        Button(frame_frame, text="Prev Frame", command=self.prev_frame).pack(side='left', expand=True, fill='x')
        Button(frame_frame, text="Next Frame", command=self.next_frame).pack(side='left', expand=True, fill='x')
        # Skip 5s side by side
        skip5s_frame = Frame(kb_btn_frame)
        skip5s_frame.pack(fill='x', pady=1)
        Button(skip5s_frame, text="Skip -5s", command=self.skip_back_5s).pack(side='left', expand=True, fill='x')
        Button(skip5s_frame, text="Skip +5s", command=self.skip_forward_5s).pack(side='left', expand=True, fill='x')
        # Skip 5min side by side
        skip5min_frame = Frame(kb_btn_frame)
        skip5min_frame.pack(fill='x', pady=1)
        Button(skip5min_frame, text="Skip -5min", command=self.skip_back_5min).pack(side='left', expand=True, fill='x')
        Button(skip5min_frame, text="Skip +5min", command=self.skip_forward_5min).pack(side='left', expand=True, fill='x')
        # Skip 1hr side by side
        skip1hr_frame = Frame(kb_btn_frame)
        skip1hr_frame.pack(fill='x', pady=1)
        Button(skip1hr_frame, text="Skip -1hr", command=self.skip_back_1hr).pack(side='left', expand=True, fill='x')
        Button(skip1hr_frame, text="Skip +1hr", command=self.skip_forward_1hr).pack(side='left', expand=True, fill='x')

        # Log-related buttons (grouped) - move to bottom of controls_container
        log_btn_frame = Frame(controls_container)
        log_btn_frame.pack(side='bottom', pady=(16, 16), fill='x')
        self.export_btn = Button(log_btn_frame, text="Export Log", command=self.export_log)
        self.export_btn.pack(side='top', pady=2, fill='x')
        self.clear_btn = Button(log_btn_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side='top', pady=2, fill='x')
        undo_frame = Frame(log_btn_frame)
        undo_frame.pack(fill='x', pady=1)
        Button(undo_frame, text="Undo", command=self.restore_last_undo).pack(side='left', expand=True, fill='x')
        Button(undo_frame, text="Redo", command=self.redo).pack(side='left', expand=True, fill='x')
        Button(log_btn_frame, text="Delete Entry", command=self.undo).pack(side='top', pady=2, fill='x')

        # Quit button at the very bottom, spaced from above
        Button(side_panel, text="Save and Quit", command=self.quit_app).pack(side='bottom', pady=16, fill='x')

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
        self.root.bind('<Control-z>', self.restore_last_undo)  # Ctrl+Z for undo
        self.root.bind('<Control-y>', self.redo)  # Ctrl+Y for redo
        self.log_text.bind('<Button-1>', self.on_log_click)
        self.root.bind('q', self.quit_app)  # Quit key binding
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
            highlight_next = None
            try:
                ranges = self.log_text.tag_ranges('highlight')
                if ranges:
                    start = ranges[0]
                    line_number = int(str(start).split('.')[0])
                    with open(self.logger.filename, 'r') as f:
                        lines = [line for line in f if line.strip()]
                    if 1 <= line_number <= len(lines):
                        removed_entry = lines[line_number - 1]
                        removed_index = line_number - 1
                        self.undo_stack.append((removed_entry, removed_index))
                        self.redo_stack.clear()
                        del lines[line_number - 1]
                        with open(self.logger.filename, 'w') as f:
                            f.writelines(lines)
                        self.sort_log_file()
                        if line_number > 1:
                            highlight_next = line_number - 1
                        elif lines:
                            highlight_next = 1
                        else:
                            highlight_next = None
                else:
                    with open(self.logger.filename, 'r') as f:
                        lines = [line for line in f if line.strip()]
                    if lines:
                        removed_entry = lines[-1]
                        removed_index = len(lines) - 1
                        self.undo_stack.append((removed_entry, removed_index))
                        self.redo_stack.clear()
                    self.logger.undo_last_entry()
                    self.sort_log_file()
            except Exception:
                pass
            self.paused = True
            self.update_log_display(highlight_line=highlight_next)

    def restore_last_undo(self):
        if self.logger and self.undo_stack:
            try:
                entry, index = self.undo_stack.pop()
                with open(self.logger.filename, 'r') as f:
                    lines = [line for line in f if line.strip()]
                insert_at = min(index, len(lines))
                lines.insert(insert_at, entry)
                with open(self.logger.filename, 'w') as f:
                    f.writelines(lines)
                self.sort_log_file()
                # Find the new line number of the restored entry
                with open(self.logger.filename, 'r') as f:
                    sorted_lines = [line for line in f if line.strip()]
                highlight_line = None
                for idx, line in enumerate(sorted_lines, 1):
                    if line.strip() == entry.strip():
                        highlight_line = idx
                        break
                self.redo_stack.append((entry, index))
                self.update_log_display(highlight_line=highlight_line)
            except Exception:
                pass

    def redo(self):
        if self.logger and self.redo_stack:
            try:
                entry, index = self.redo_stack.pop()
                with open(self.logger.filename, 'r') as f:
                    lines = [line for line in f if line.strip()]
                # Remove the entry at the same index (if it exists)
                for i, line in enumerate(lines):
                    if line.strip() == entry.strip():
                        del lines[i]
                        break
                with open(self.logger.filename, 'w') as f:
                    f.writelines(lines)
                self.sort_log_file()
                self.undo_stack.append((entry, index))
                # Highlight the next entry above
                highlight_line = index if index > 0 else 1
                self.update_log_display(highlight_line=highlight_line)
            except Exception:
                pass

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

    def quit_app(self, event=None):
        self.root.quit()

if __name__ == "__main__":
    root = Tk()
    app = CarCounterGUI(root)
    root.mainloop()