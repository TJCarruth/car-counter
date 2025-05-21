class CSVLogger:
    def __init__(self, filename):
        self.filename = filename
        self.logged_keys = set()

    def log_entry(self, key, timestamp):
        if key not in self.logged_keys:
            with open(self.filename, 'a') as file:
                file.write(f"{key},{timestamp}\n")
            self.logged_keys.add(key)

    def ensure_unique_keys(self, keys):
        unique_keys = []
        for key in keys:
            if key not in self.logged_keys:
                unique_keys.append(key)
                self.logged_keys.add(key)
        return unique_keys

    def clear_log(self):
        with open(self.filename, 'w') as file:
            file.write("key,timestamp\n")  # Write header for CSV file
        self.logged_keys.clear()