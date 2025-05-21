# Car Counter

A Python application for playing back camera footage and logging car counts via key presses. The app outputs a CSV file that logs each key press and its corresponding timestamp, making it easy to analyze traffic or vehicle flow from recorded video.

## Features
- Plays back camera/video footage
- Logs key presses with timestamps
- Outputs results to a CSV file for easy analysis

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

## Usage
1. Place your video footage in the project directory or specify the path as needed.
2. Run the main application:
   ```sh
   python main.py
   ```
3. Use the designated keys to log car counts as you watch the footage. Each key press will be recorded with a timestamp.
4. After the session, check the generated CSV file for your log data.

## Files
- `main.py`: Main entry point for the application.
- `csv_logger.py`: Handles logging of key presses to CSV.
- `video_processor.py`: Handles video playback and processing.
- `timestamp_reader.py`: Reads and processes timestamps.
- `requirements.txt`: Python dependencies.

## License
MIT License (or specify your license here)

## Author
Your Name Here
