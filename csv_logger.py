class CSVLogger:
    def __init__(self, filename):
        self.filename = filename

    def log_entry(self, key, timestamp):
        with open(self.filename, 'a') as file:
            file.write(f"{key},{timestamp}\n")

    def clear_log(self):
        with open(self.filename, 'w') as file:
            file.write("key,timestamp\n")  # Write header for CSV file