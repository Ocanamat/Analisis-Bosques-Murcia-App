from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                          QDialogButtonBox, QScrollArea, QWidget)
from PyQt6.QtCore import Qt

class SummaryDialog(QDialog):
    """Dialog to display Excel file summary"""
    
    def __init__(self, parent=None, summary_text: str = ""):
        super().__init__(parent)
        
        self.setWindowTitle("Excel File Summary")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Add summary text
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        content_layout.addWidget(summary_label)
        
        # Set content layout
        content.setLayout(content_layout)
        scroll.setWidget(content)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll)
        
        # Add close button
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        self.setLayout(main_layout)
