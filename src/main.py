#!/usr/bin/env python3
import os
import sys
from PyQt6.QtWidgets import QApplication
from bosques_app.app import Application

def main():
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create and run application
    application = Application(app)
    application.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()