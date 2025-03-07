from PyQt6.QtWidgets import QFrame, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPaintEvent, QPainter, QColor

from ..utils.grammar_handler import GrammarHandler

class GrammarFrame(QFrame):
    """Custom QFrame that accepts variable drops for grammar of graphics"""
    
    def __init__(self, parent=None, grammar_handler: GrammarHandler = None, frame_id: str = None):
        super().__init__(parent)
        self.grammar_handler = grammar_handler
        self.frame_id = frame_id
        self.label = None
        
        # Enable dropping
        self.setAcceptDrops(True)
        
        # Set frame style
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(1)
        
        # Set minimum size
        self.setMinimumSize(100, 40)
        
        # Set background color
        self.setStyleSheet("background-color: #f8f9fa;")  # Light gray background
        
        # Store active variable
        self.active_variable = None
    
    def set_label(self, label: QLabel):
        """Set the label widget for this frame"""
        self.label = label
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Highlight the frame
            self.setStyleSheet("background-color: #e9ecef; border: 1px solid #6c757d;")
    
    def dragLeaveEvent(self, event):
        """Handle drag leave events"""
        # Reset frame style
        self.setStyleSheet("background-color: #f8f9fa;")
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        variable_name = event.mimeData().text()
        
        # Reset frame style
        self.setStyleSheet("background-color: #f8f9fa;")
        
        if self.grammar_handler and self.grammar_handler.handle_variable_drop(self.frame_id, variable_name):
            # Update label
            if self.label:
                self.label.setText(variable_name)
                self.label.setStyleSheet("color: #212529;")  # Dark gray text
            self.active_variable = variable_name
            event.acceptProposedAction()
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event to draw a border"""
        super().paintEvent(event)
        
        # Draw border
        painter = QPainter(self)
        painter.setPen(QColor("#dee2e6"))  # Light gray border
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.RightButton and self.active_variable:
            # Clear the variable on right click
            if self.grammar_handler:
                self.grammar_handler.clear_frame(self.frame_id)
            if self.label:
                self.label.setText("Drop variable here")
                self.label.setStyleSheet("color: #808080;")
            self.active_variable = None
