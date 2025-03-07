from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidgetItem, QTreeWidget
from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QFont
from typing import List, Optional

from ..config import Settings

class VariablesModel:
    """Model for displaying variables and their measurement options"""
    
    # Signals
    variable_selection_changed = pyqtSignal(str, bool)  # (variable_name, is_selected)
    
    def __init__(self, parent=None):
        self.parent = parent
        self._setup_headers()
        self._populate_predefined_variables()
        self.parent.variables_treewidget.itemChanged.connect(self._on_item_changed)
    
    def _setup_headers(self):
        """Set up the header labels for the model"""
        headers = ["Variable", "Tipo"]  
        tree = self.parent.variables_treewidget
        tree.setHeaderLabels(headers)
        
        # Enable drag and drop
        tree.setDragEnabled(True)
        tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        
        # Set mime type for drag and drop
        tree.mimeTypes = lambda: ['text/plain']
        tree.mimeData = lambda items: self.mimeData(items)
    
    def _populate_predefined_variables(self):
        """Populate the tree with predefined variables"""
        tree = self.parent.variables_treewidget
        tree.clear()
        
        # Group variables by origin
        variables_by_origin = {}
        for origin, variable, tipo in Settings.PREDEFINED_VARIABLES:
            if origin not in variables_by_origin:
                variables_by_origin[origin] = []
            variables_by_origin[origin].append((variable, tipo))
        
        # Add variables grouped by origin
        for origin, variables in variables_by_origin.items():
            # Create origin item with bold font
            origin_item = QTreeWidgetItem(tree)
            origin_item.setText(0, origin)  
            origin_item.setText(1, "")  
            
            # Make origin text bold
            font = QFont()
            font.setBold(True)
            origin_item.setFont(0, font)
            
            # Add variables under this origin
            for variable, tipo in variables:
                var_item = QTreeWidgetItem(origin_item)
                var_item.setText(0, variable)  
                var_item.setText(1, tipo)  
                
                # Enable dragging for variable items
                var_item.setFlags(var_item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
                
                # Add subhierarchy if defined
                subhierarchy = self._get_variable_subhierarchy(variable)
                if subhierarchy:
                    for sub in subhierarchy:
                        sub_item = QTreeWidgetItem(var_item)
                        sub_item.setText(0, sub)
                        sub_item.setText(1, tipo)
                        sub_item.setFlags(sub_item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
                    
                    # Collapse the variable item to hide subhierarchy
                    var_item.setExpanded(False)
            
            # Expand the origin item to show variables
            origin_item.setExpanded(True)
        
    def _get_variable_subhierarchy(self, variable_name: str) -> list:
        """Get subhierarchy for a variable if defined"""
        for var in Settings._variables_config['variables']:
            if var['name'] == variable_name:
                return var.get('subhierarchy', [])
        return []

    def mimeData(self, items):
        """Create mime data for drag and drop"""
        if not items:
            return None
            
        mime_data = QMimeData()
        # Get the variable name from the selected item
        variable = items[0].text(0)
        mime_data.setText(variable)
        return mime_data

    def _on_item_changed(self, item, column):
        """Handle item changes (checkbox toggles)"""
        if column == 1:  
            variable_name = item.text(0)
            is_selected = item.checkState(1) == Qt.CheckState.Checked
            self.variable_selection_changed.emit(variable_name, is_selected)

    def get_sample_data(self, variable_name: str) -> Optional[List[float]]:
        """Get sample data for a variable"""
        return Settings.SAMPLE_DATA.get(variable_name)
