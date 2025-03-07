import os
import pyqtgraph as pg
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QScreen
from PyQt6 import uic

class MainWindow(QMainWindow):
    """Main window of the application"""
    
    def __init__(self):
        super().__init__()
        
        # Get the directory containing this script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load the UI file directly
        ui_file = os.path.join(current_dir, "main_window.ui")
        uic.loadUi(ui_file, self)
        
        # Store self as ui for compatibility with controller
        self.ui = self

        # Initialize plot
        self.plot = pg.PlotWidget()
        self.plot.setBackground("w")  # White background
        self.plot.showGrid(x=True, y=True)
        self.plot.addLegend()

        # Add plot to the container
        plot_layout = QVBoxLayout(self.plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.plot)

        # Store active plots
        self.active_plots = {}
        
        # Center window on screen
        self.center_on_screen()
        
    def center_on_screen(self):
        """Center the window on the current screen"""
        # Get the current screen
        screen = self.screen()
        if not screen:
            screen = QScreen.primaryScreen()

        # Get the screen's geometry
        screen_geometry = screen.availableGeometry()

        # Calculate the centered position
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()

        # Move the window's center point to the screen's center point
        window_geometry.moveCenter(center_point)
        
        # Apply a 15-pixel vertical offset to move the window up
        position = window_geometry.topLeft()
        position.setY(position.y() - 15)  # Subtract 15 pixels from Y coordinate
        
        self.move(position)