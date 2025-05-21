class TimestampReader:
    def __init__(self, tesseract_cmd=None):
        # Optionally set the Tesseract executable path
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def process_frame(self, frame):
        # Preprocess the frame for OCR
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary_frame = cv2.threshold(gray_frame, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # Use pytesseract to extract text
        timestamp = pytesseract.image_to_string(binary_frame, config='--psm 7')  # PSM 7 assumes a single line of text
        return timestamp.strip()

    def read_timestamps(self, video_path):
        video_capture = cv2.VideoCapture(video_path)
        timestamps = []

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            timestamp = self.process_frame(frame)
            if timestamp not in timestamps:
                timestamps.append(timestamp)
                if len(timestamps) >= 10:
                    break

        video_capture.release()
        return timestamps