import os

class CSVLogger:
    def __init__(self, filename):
        self.filename = filename

    def log_entry(self, key, timestamp):
        with open(self.filename, 'a') as file:
            file.write(f"{timestamp}, {key}\n")

    def display_entries(self, num_entries=5):
        if not os.path.exists(self.filename):
            print("No observations yet.")
            return
        with open(self.filename, 'r') as f:
            lines = f.readlines()
            print("\nLatest Observations:")
            for line in lines[-num_entries:]:
                print(line.strip())

    def undo_last_entry(self):
        if not os.path.exists(self.filename):
            raise Exception("Log file does not exist.")
        with open(self.filename, 'r') as f:
            lines = f.readlines()
        if len(lines) <= 1:
            raise Exception("No entries to undo.")
        with open(self.filename, 'w') as f:
            f.writelines(lines[:-1])