from typing import Dict, Optional
from PyQt6.QtWidgets import QFrame, QLabel, QComboBox
from PyQt6.QtCore import QObject, pyqtSignal

from ..config import Settings

class GrammarHandler(QObject):
    """Handles the grammar of graphics state and interactions"""
    
    # Signal emitted when the grammar state changes
    state_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Internal state dictionary for grammar of graphics
        self._grammar_state = Settings.GRAMMAR_STATE_KEYS.copy()
        
        # Dictionary to store frame labels
        self._labels: Dict[str, QLabel] = {}
        
        # Store references to frames and their labels
        self._frames: Dict[str, QFrame] = {}
        self._combos: Dict[str, QComboBox] = {}
    
    def register_frame(self, frame_id: str, frame: QFrame, label: QLabel):
        """Register a QFrame and its label for tracking"""
        self._frames[frame_id] = frame
        self._labels[frame_id] = label
        
        # Make the frame accept drops
        frame.setAcceptDrops(True)
        
        # Set initial label text
        label.setText("Drop variable here")
    
    def register_combo(self, combo_id: str, combo: QComboBox):
        """Register a QComboBox for tracking"""
        self._combos[combo_id] = combo
        combo.currentTextChanged.connect(
            lambda text, id=combo_id: self._handle_combo_change(id, text)
        )
    
    def handle_variable_drop(self, frame_id: str, variable_name: str) -> bool:
        """Handle a variable being dropped onto a frame"""
        if frame_id not in Settings.FRAME_TO_STATE:
            return False
            
        # Update internal state
        state_key = Settings.FRAME_TO_STATE[frame_id]
        self._grammar_state[state_key] = variable_name
        
        # Emit state changed signal
        self.state_changed.emit()
        return True
    
    def _handle_combo_change(self, combo_id: str, value: str):
        """Handle a combo box selection change"""
        if combo_id in Settings.COMBO_TO_STATE:
            state_key = Settings.COMBO_TO_STATE[combo_id]
            self._grammar_state[state_key] = value
            self.state_changed.emit()
    
    def clear_frame(self, frame_id: str):
        """Clear a frame's variable assignment"""
        if frame_id in Settings.FRAME_TO_STATE:
            state_key = Settings.FRAME_TO_STATE[frame_id]
            self._grammar_state[state_key] = None
            if frame_id in self._labels:
                self._labels[frame_id].setText("Drop variable here")
            self.state_changed.emit()
    
    def get_state(self) -> dict:
        """Get the current grammar state"""
        return self._grammar_state.copy()
