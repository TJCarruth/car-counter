# Car Counter

A Python application for playing back camera footage and logging car counts via key presses. The app outputs a CSV file that logs each key press and its corresponding timestamp, making it easy to analyze traffic or vehicle flow from recorded video.

## Features
- Plays back camera/video footage
- Logs key presses with timestamps
- Outputs results to a CSV file for easy analysis
- both a terminal-based and a GUI version available

## Installation
1. Clone this repository:
   ```sh
   git clone <repo-url>
   ```
2. Navigate to the project directory:
   ```sh
   cd car-counter
   ```
3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage ########################################

### Terminal Usage
1. Place your video footage in the video folder.
2. Make sure the output folder is empty and any previous CSV files have been saved elsewhere. 
3. Run the main application:
   ```sh
   python main.py
   ```
4. Use the following to control the video: 
      Space = Play/Pause 
      -/= = Speed up / slow down
      left/right Arrows = skip 5 seconds
      [ / ] = skip 5 minutes
      { / } = skip 1 hour
      , . = one frame forward or back
      Backspace = Undo & Pause
      q = Quit 
5. Press any other key to log an event and it's timestamp in the video.
6. After the session, check the generated CSV file in the output folder for your log data.
7. Use the data analysis language of your choice to interpret the recorded key presses.

### GUI Usage
1. run the main application:
   ```sh
   python main_gui.py
   ```
2. Click the "Open Video" button to select your video file.
3. Use the playback controls to play, pause, and navigate through the video.
4. Press any letter key to log an event and its timestamp.
5. The logged events will be automatically saved to a CSV file located in the same folder as the video file. 
6. clicking on any timestamp in the log will seek to that point in the video. 
7. You can also export the log to a CSV file by clicking the "Export" button.

Note: Since the CSV is saved automatically, you can close the GUI at any time and the log will be saved. Opening the video again will load the previous log data. You can click the last timestamp to seek to the last logged event.

## Files
- `main.py`: Main entry point for the application.
- `csv_logger.py`: Handles logging of key presses to CSV.
- `video_processor.py`: Handles video playback and processing.
- `requirements.txt`: Python dependencies.

## License
MIT License

## Author
Tyler Carruth
