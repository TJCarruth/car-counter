# Car Counter

A Python application for playing back camera footage and logging car counts via key presses. The app outputs a CSV file that logs each key press and its corresponding timestamp, making it easy to analyze traffic or vehicle flow from recorded video.

## Features
- Plays back camera/video footage
- Logs key presses with timestamps
- Outputs results to a CSV file for easy analysis
- GUI version only

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/TJCarruth/car-counter.git
   ```
2. Navigate to the project directory:
   ```sh
   cd car-counter
   ```
3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

### (Optional) Compile to Standalone Executable
You can use [PyInstaller](https://pyinstaller.org/) to create a standalone executable:

1. Install PyInstaller:
   ```sh
   pip install pyinstaller
   ```
2. Run PyInstaller on the GUI script:
   ```sh
   pyinstaller --onefile --windowed --clean main_gui.py
   ```
3. The standalone executable will be found in the `dist` folder.

## Usage
1. Run the main application:
   ```sh
   python main_gui.py
   ```
   Or, if you compiled an executable, run the generated file in the `dist` folder.
2. Click the "Open Video" button to select your video file.
3. Use the playback control buttons or keyboard shortcuts to play, pause, and navigate through the video:
   - Play/Pause
   - Speed + / -
   - Prev/Next Frame
   - Skip +/-5s
   - Skip +/-5min
   - Skip +/-1hr
   - Undo / Redo
   - Quit
   - Or use the corresponding keyboard shortcuts:
     - Space = Play/Pause
     - + / - = Playback Speed
     - , / . = Frame Shift
     - ; / ' = Skip 5s
     - [ / ] = Skip 5min
     - { / } = Skip 1hr
     - Backspace = Undo
     - Ctrl+Z = Undo
     - Ctrl+Y = Redo
     - q = Quit
4. Press any letter key to log an event and its timestamp.
5. The logged events will be automatically saved to a CSV file located in the same folder as the video file.
6. Clicking on any timestamp in the log will seek to that point in the video.
7. You can also export the log to a CSV file by clicking the "Export Log" button.

Note: Since the CSV is saved automatically, you can close the GUI at any time and the log will be saved. Opening the video again will load the previous log data. You can click the last timestamp to seek to the last logged event.

## Files
- `main_gui.py`: Main entry point for the GUI application.
- `csv_logger.py`: Handles logging of key presses to CSV.
- `video_processor.py`: Handles video playback and processing.
- `requirements.txt`: Python dependencies.

Note: The GUI version requires `tkinter` for the graphical interface, which is included in the standard Python library for most installations.

## License
MIT License

## Author
Tyler Carruth
