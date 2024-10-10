import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
    QPushButton, QLabel, QFileDialog, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import screens

class ImageViewer(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)

        # Display image
        label = QLabel(self)
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        #label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main layout
        self.setWindowTitle("F9 RasterMakker")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Horizontal layout for the buttons (placed at the top)
        button_layout = QHBoxLayout()

        # CSV file selection button
        self.csv_button = QPushButton("Select CSV File")
        self.csv_button.clicked.connect(self.select_csv_file)
        button_layout.addWidget(self.csv_button)

        # Folder selection button
        self.folder_button = QPushButton("Select Output Folder")
        self.folder_button.clicked.connect(self.select_output_folder)
        button_layout.addWidget(self.folder_button)

        # Run button (disabled by default)
        self.run_button = QPushButton("Run")
        self.run_button.setEnabled(False)  # Disabled initially
        self.run_button.clicked.connect(self.run_image_creation)
        button_layout.addWidget(self.run_button)

        # Add the button layout to the main layout at the top
        main_layout.addLayout(button_layout)

        # Tab widget for viewing images
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Initialize paths for validation
        self.csv_file_path = Path
        self.output_folder_path = Path

    def select_csv_file(self):
        # Open a file dialog to select a CSV file
        csv_file, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if csv_file:
            self.csv_file_path = Path(csv_file)  # Store as Path object
            print(f"Selected CSV file: {self.csv_file_path}")
            self.check_run_button_enabled()

    def select_output_folder(self):
        # Open a dialog to select an output folder
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_path = Path(folder)  # Store as Path object
            print(f"Selected output folder: {self.output_folder_path}")
            self.check_run_button_enabled()

    def check_run_button_enabled(self):
        # Enable the Run button only if both a CSV file and output folder are selected
        if self.csv_file_path and self.output_folder_path:
            self.run_button.setEnabled(True)
        else:
            self.run_button.setEnabled(False)

    def run_image_creation(self):
        # This is where the main logic for creating images will go
        print("Running the main loop to create images...")
        
        # Ensure output folder exists
        if not self.output_folder_path.exists():
            print(f"Output folder does not exist: {self.output_folder_path}")
            return
        
        # Prepare output directories
        csv_path = self.csv_file_path
        filename = csv_path.stem  # Get the CSV filename without extension
        base_output_path = self.output_folder_path / filename

        # List of screens
        screen_list = screens.ScreenList(csv_path)
        print(screen_list.screens)

        # Create necessary directories
        (base_output_path / '01_Content_Blocks').mkdir(parents=True, exist_ok=True)
        (base_output_path / '02_Eng_Blocks').mkdir(parents=True, exist_ok=True)
        (base_output_path / '03_Stealth_Blocks').mkdir(parents=True, exist_ok=True)

        # Process each screen
        for screen in screen_list.screens:
            print(screen.name)

            # Assuming ScreenDrawer creates images for each screen
            drawer = screens.ScreenDrawer(screen, base_output_path)
            drawer.draw_content()
            drawer.draw_eng()
            drawer.draw_stealth()

            # Assuming the `ScreenDrawer` has a method that gives us the output image paths
            # Add each image as a tab (update with actual image path after drawing)
            content_image = base_output_path / '01_Content_Blocks' / f"{screen.name}.png"
            eng_image = base_output_path / '02_Eng_Blocks' / f"{screen.name}.png"
            stealth_image = base_output_path / '03_Stealth_Blocks' / f"{screen.name}.png"

            # Add the images to the tab viewer (assuming they exist after generation)
            self.add_image_tab(str(content_image))
            self.add_image_tab(str(eng_image))
            self.add_image_tab(str(stealth_image))

    def add_image_tab(self, image_path):
        # Add a new tab for displaying an image
        if not Path(image_path).exists():
            print(f"Image not found: {image_path}")
            return
        image_viewer = ImageViewer(image_path)
        tab_name = Path(image_path).name  # Use the file name as the tab title
        self.tab_widget.addTab(image_viewer, tab_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow()

    window.show()
    sys.exit(app.exec())
