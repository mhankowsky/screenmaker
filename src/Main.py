#Main Applicaiton 

import os, sys, csv
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("F9|ScreenMakker")

        button = QPushButton("Button1")

        self.setCentralWidget(button)


app = QApplication()

window = MainWindow()
window.show()

#Start Event Loop 
app.exec()


#Event Loop ends here....