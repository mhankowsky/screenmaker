import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
    QPushButton, QLabel, QFileDialog, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class ImageViewer(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)

        # Display image
        label = QLabel(self)
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        #label.setAlignment(Qt.AlignmentFlag())
        
        layout.addWidget(label)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main layout
        self.setWindowTitle("Image Viewer and File Selector")
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
        self.csv_file_path = None
        self.output_folder_path = None

    def select_csv_file(self):
        # Open a file dialog to select a CSV file
        csv_file, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if csv_file:
            self.csv_file_path = csv_file
            print(f"Selected CSV file: {csv_file}")
            self.check_run_button_enabled()

    def select_output_folder(self):
        # Open a dialog to select an output folder
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_path = folder
            print(f"Selected output folder: {folder}")
            self.check_run_button_enabled()

    def check_run_button_enabled(self):
        # Enable the Run button only if both a CSV file and output folder are selected
        if self.csv_file_path and self.output_folder_path:
            self.run_button.setEnabled(True)
        else:
            self.run_button.setEnabled(False)

    def run_image_creation(self):
        # This is where the main logic for creating images will go
        # For now, just a placeholder action
        print("Running the main loop to create images...")
        # Example: Add tabs with placeholder images (you can replace with your actual logic)
        self.add_image_tab("/path/to/your/image1.jpg")
        self.add_image_tab("/path/to/your/image2.png")

    def add_image_tab(self, image_path):
        # Add a new tab for displaying an image
        image_viewer = ImageViewer(image_path)
        tab_name = image_path.split('/')[-1]  # Use the file name as the tab title
        self.tab_widget.addTab(image_viewer, tab_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow()

    window.show()
    sys.exit(app.exec())
