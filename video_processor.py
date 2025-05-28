import cv2
import os

class VideoProcessor:
    def __init__(self, video_path):
        self.video_capture = cv2.VideoCapture(video_path)
        if not self.video_capture.isOpened():
            raise ValueError(f"Unable to open video file: {video_path}")

    @staticmethod
    def select_video(videos_dir):
        video_files = [f for f in os.listdir(videos_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
        if not video_files:
            print("No video files found in the 'videos' folder.")
            return None
        print("Available videos:")
        for idx, video in enumerate(video_files, start=1):
            print(f"{idx}. {video}")
        while True:
            try:
                choice = int(input("Enter the number of the video you want to use: "))
                if 1 <= choice <= len(video_files):
                    return video_files[choice - 1]
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

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