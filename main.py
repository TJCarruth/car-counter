import os
import cv2
from video_processor import VideoProcessor
from csv_logger import CSVLogger
from datetime import timedelta, datetime

def main():

    ## Background Initializations ##########################################################

    # Ensure the script is run from the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    videos_dir = os.path.join(script_dir, "videos")
    selected_video = VideoProcessor.select_video(videos_dir)
    if not selected_video:
        return

    # Construct full paths for video and CSV output
    video_path = os.path.join(videos_dir, selected_video)
    csv_path = os.path.join(script_dir, "output", f"{os.path.splitext(selected_video)[0]}.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Initialize video capture and logger
    video = cv2.VideoCapture(video_path)
    logger = CSVLogger(csv_path)
    paused = True  # Start paused
    speed = 1  # 1x speed
    frame_pos = 0
    start_offset = timedelta()  # Default to zero

    ## Print the controls to terminal ##########################################
    controls_text = """
                    Controls: Space=Play/Pause | +/-=Speed | Arrows, [, ], {{, }} =Skip | , .=Frame | Any key=Log | Backspace=Undo & Pause | q=Quit
                    The video will start paused. When ready, press 's' to enter the start time (HH:MM:SS).
                    """
    print(controls_text)
    start_time_set = False

    slider_max = int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    slider_pos = 0
    user_slider_drag = [False]
    slider_target_frame = [0]

    def on_trackbar(val):
        user_slider_drag[0] = True
        slider_target_frame[0] = val

    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Position", "Video", 0, slider_max, on_trackbar)

    while True:
        # If user dragged the slider, show the frame at that position and pause
        if user_slider_drag[0]:
            frame_pos = slider_target_frame[0]
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = video.read()
            if ret:
                cv2.setWindowProperty("Video", cv2.WND_PROP_TOPMOST, 1)
                cv2.setTrackbarPos("Position", "Video", frame_pos)
                cv2.imshow("Video", frame)
            paused = True
            user_slider_drag[0] = False
            continue

        if not paused:
            ret, frame = video.read()
            if not ret:
                print("End of video.") # If we reach the end of the video, we stop playback
                break
            frame_pos = int(video.get(cv2.CAP_PROP_POS_FRAMES))
            cv2.setWindowProperty("Video", cv2.WND_PROP_TOPMOST, 1)
            cv2.setTrackbarPos("Position", "Video", frame_pos)
            cv2.imshow("Video", frame)
        else:
            if int(video.get(cv2.CAP_PROP_POS_FRAMES)) != frame_pos:
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = video.read()
            if ret:
                cv2.setWindowProperty("Video", cv2.WND_PROP_TOPMOST, 1)
                cv2.setTrackbarPos("Position", "Video", frame_pos)
                cv2.imshow("Video", frame)
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        # Check if slider was moved
        new_slider_pos = cv2.getTrackbarPos("Position", "Video")
        if new_slider_pos != frame_pos:
            frame_pos = new_slider_pos
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            paused = True

        key = cv2.waitKey(0 if paused else int(30 / speed)) & 0xFF

        ## General Controls ##########################################################
        if key == ord('q'):  # q: Quit
            break

        if key == ord(' '):  # Space: Play/Pause
            paused = not paused
        
        ## Speed Controls ############################################################

        elif key == ord('='):  # Speed up: =
            speed = min(speed + 0.25, 10) # Max speed is 10x
            print(f"Speed: {speed}x")

        elif key == ord('-'):  # Slow down: -
            speed = max(speed - 0.25, 0.25) # Min speed is 0.25x
            print(f"Speed: {speed}x")

        ## Navigation Controls #########################################################

        elif key == ord(','):  # ,: Previous frame
            frame_pos = max(0, frame_pos - 1)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            paused = True

        elif key == ord('.'):  # .: Next frame
            frame_pos = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, frame_pos + 1)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            paused = True
        
        elif key == ord(';'):  # ;: skip back 5s
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = max(0, frame_pos - int(fps * 5))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        elif key == ord("'"):  # ': skip forward 5s
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, frame_pos + int(fps * 5))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        elif key == ord('['):  # [: Skip back 5 minutes
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = max(0, frame_pos - int(fps * 60 * 5))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        elif key == ord(']'):  # ]: Skip forward 5 minutes
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, frame_pos + int(fps * 60 * 5))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        elif key == ord('{'):  # {: Skip back 1 hour
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = max(0, frame_pos - int(fps * 60 * 60))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        elif key == ord('}'):  # }: Skip forward 1 hour
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_pos = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, frame_pos + int(fps * 60 * 60))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        ## Logging Controls ##########################################################        

        elif key == 8:  # Backspace: Undo last observation and pause
            try:
                logger.undo_last_entry()
                print("Last observation removed.")
            except Exception as e:
                print(f"Nothing to undo: {e}")
            paused = True
            logger.display_entries()
        
        elif key != 255:  # Any other key not used as a control gets logged
            # Use frame position and FPS to compute timestamp
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_idx = int(video.get(cv2.CAP_PROP_POS_FRAMES))
            seconds = frame_idx / fps if fps > 0 else 0
            ms = seconds * 1000
            timestamp_str = VideoProcessor.format_timestamp(ms, start_offset)
            # Log the key press with the timestamp
            logger.log_entry(chr(key), timestamp_str)
            print(f"Logged: {chr(key)} at {timestamp_str}")
            logger.display_entries()

        

    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()