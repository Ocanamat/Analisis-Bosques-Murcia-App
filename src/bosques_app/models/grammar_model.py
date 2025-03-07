from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from ..config import Settings

class GrammarModel(QObject):
    """Model for managing the grammar of graphics state"""
    
    # Signal emitted when the grammar state changes
    state_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # Initialize state with None values
        self._grammar_state = Settings.GRAMMAR_STATE_KEYS.copy()
        
        # Set default plot type to 'Dispersión'
        self._grammar_state['plot_type'] = 'Dispersión'
        
    def handle_variable_drop(self, frame_id: str, variable_name: str) -> bool:
        """Handle a variable being dropped onto a frame
        
        Args:
            frame_id: ID of the frame that received the drop
            variable_name: Name of the dropped variable
            
        Returns:
            bool: True if the drop was handled, False otherwise
        """
        if frame_id not in Settings.FRAME_TO_STATE:
            return False
            
        # Update internal state
        state_key = Settings.FRAME_TO_STATE[frame_id]
        self._grammar_state[state_key] = variable_name
        
        # Emit state changed signal
        self.state_changed.emit()
        return True
    
    def handle_combo_change(self, combo_id: str, value: str):
        """Handle a combo box selection change
        
        Args:
            combo_id: ID of the combo box that changed
            value: New value selected
        """
        if combo_id in Settings.COMBO_TO_STATE:
            state_key = Settings.COMBO_TO_STATE[combo_id]
            self._grammar_state[state_key] = value
            self.state_changed.emit()
    
    def handle_combo_change(self, combo_id: str, value: str):
        """Handle a combo box selection change
        
        Args:
            combo_id: ID of the combo box that changed
            value: New value selected
        """
        if combo_id in Settings.COMBO_TO_STATE:
            state_key = Settings.COMBO_TO_STATE[combo_id]
            self._grammar_state[state_key] = value
            self.state_changed.emit()
    
    def clear_frame(self, frame_id: str) -> bool:
        """Clear a frame's variable assignment
        
        Args:
            frame_id: ID of the frame to clear
            
        Returns:
            bool: True if the frame was cleared, False otherwise
        """
        if frame_id in Settings.FRAME_TO_STATE:
            state_key = Settings.FRAME_TO_STATE[frame_id]
            self._grammar_state[state_key] = None
            self.state_changed.emit()
            return True
        return False
    
    def get_state(self) -> Dict[str, Optional[str]]:
        """Get the current grammar state
        
        Returns:
            Dict mapping aesthetic properties to variable names
        """
        return self._grammar_state.copy()
