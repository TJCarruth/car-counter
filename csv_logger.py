class CSVLogger:
    def __init__(self, filename):
        self.filename = filename

    def log_entry(self, key, timestamp):
        with open(self.filename, 'a') as file:
            file.write(f"{key},{timestamp}\n")

    def clear_log(self):
        with open(self.filename, 'w') as file:
            file.write("key,timestamp\n")  # Write header for CSV file

    def display_entries(self, num_entries=5):
        import os
        if not os.path.exists(self.filename):
            print("No observations yet.")
            return
        with open(self.filename, 'r') as f:
            lines = f.readlines()
            print("\nLatest Observations:")
            for line in lines[-num_entries:]:
                print(line.strip())