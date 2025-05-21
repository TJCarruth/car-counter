import cv2

class VideoProcessor:
    def __init__(self, video_path):
        self.video_capture = cv2.VideoCapture(video_path)
        if not self.video_capture.isOpened():
            raise ValueError(f"Unable to open video file: {video_path}")

    def get_frame(self):
        ret, frame = self.video_capture.read()
        if not ret:
            return None
        return frame

    def display_frame(self, frame):
        cv2.imshow("Video", frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):  # Add a 10ms delay
            return False
        return True

    def release(self):
        self.video_capture.release()
        cv2.destroyAllWindows()