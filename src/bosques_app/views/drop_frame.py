from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QDragEnterEvent, QDropEvent

class DropFrame(QFrame):
    """A QFrame that accepts variable drops"""
    
    def __init__(self, parent=None, frame_id=None):
        super().__init__(parent)
        self.frame_id = frame_id
        self.grammar_handler = None  # Will be set by MainController
        
        # Setup UI
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Create label for showing current variable
        self.label = QLabel("Drop variable here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.label)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Visual feedback
            self.setFrameShadow(QFrame.Shadow.Sunken)
            
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.setFrameShadow(QFrame.Shadow.Raised)
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        variable_name = event.mimeData().text()
        if self.grammar_handler and self.frame_id:
            if self.grammar_handler.handle_variable_drop(self.frame_id, variable_name):
                self.label.setText(variable_name)
        self.setFrameShadow(QFrame.Shadow.Raised)
        event.acceptProposedAction()
        
    def clear(self):
        """Clear the frame's variable"""
        if self.grammar_handler and self.frame_id:
            self.grammar_handler.clear_frame(self.frame_id)
            self.label.setText("Drop variable here")
