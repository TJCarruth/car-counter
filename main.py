import os
import cv2
from video_processor import VideoProcessor
from csv_logger import CSVLogger
from datetime import timedelta, datetime

def main():
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

    # Print the controls to terminal
    controls_text = """
                    Controls: Space=Play/Pause | +/-=Speed | Arrows, [, ], {{, }} =Skip | , .=Frame | Any key=Log | Backspace=Undo & Pause | q=Quit
                    The video will start paused. When ready, press 's' to enter the start time (HH:MM:SS).
                    """
    print(controls_text)

    
    # Extract last 6 digits from video name (before extension) to use as default start time if available.
    # If the video name is something like "video_000003.mp4", it will use "00:00:03" as the default start time.
    video_basename = os.path.splitext(selected_video)[0]
    default_start_time = VideoProcessor.extract_default_start_time(video_basename)

    # Prompts the user for the start time, but offers a default based on the video name.
    while True:
        prompt = f"Enter the video start time (HH:MM:SS)"
        if default_start_time:
            prompt += f" [default: {default_start_time}]: "
        else:
            prompt += ": "
        start_time_str = input(prompt)

        if not start_time_str and default_start_time:
            start_time_str = default_start_time
        offset = VideoProcessor.parse_start_time(start_time_str)
        
        if offset is not None:
            start_offset = offset
            print(f"Start time set to {start_time_str}.")
            break

    # Plays the video in a loop, allowing for controls to be used.
    while True:

        # controls the playing and pausing of the video
        if not paused:
            ret, frame = video.read()
            if not ret:
                print("End of video.") # If we reach the end of the video, we stop playback
                break
            frame_pos = int(video.get(cv2.CAP_PROP_POS_FRAMES))
        else:
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = video.read()
        # Keep the video window on top so we can interact with the terminal at the same time.
        if ret:
            cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Video", cv2.WND_PROP_TOPMOST, 1)
            cv2.imshow("Video", frame)
        else:
            print("Error: Couldn't retrieve frame.")
            break

        

        # Video Controls #############################################################################

        # watches for key presses. The delay controls the speed of the video playback.
        # If paused, waits indefinitely for a key press; otherwise, adjust delay based on speed.
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