from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (QFileDialog, QHeaderView, QVBoxLayout, QLabel, 
                          QTreeWidgetItem, QComboBox, QFrame, QMessageBox, 
                          QListWidgetItem, QDialog, QDialogButtonBox, QScrollArea,
                          QWidget, QTableView)
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QPalette, QDragEnterEvent, QDropEvent
from PyQt6.QtWebEngineWidgets import QWebEngineView
import pyqtgraph as pg
import os
import pandas as pd

from ..models.data_model import DataModel
from ..models.variables_model import VariablesModel
from ..models.grammar_model import GrammarModel
from ..models.plot_model import PlotModel
from ..models.map_model import MapModel
from ..models.task_queue_model import TaskQueueModel
from ..utils.config import Config
from ..utils.logging import Logger
from ..ui.dialogs.summary_dialog import SummaryDialog

class MainController:
    def __init__(self, view, data_model: DataModel):
        self.view = view
        
        # Reuse the existing logger from the data_model
        self.logger = data_model.logger
        
        # Set the data_model
        self.data_model = data_model
        
        # Initialize components
        self.variables_model = VariablesModel(self.view)
        self.config = Config()
        
        # Initialize models
        self.grammar_model = GrammarModel()
        
        # Initialize plot
        self._setup_plot()
        
        # Initialize map
        self._setup_map()
        
        # Initialize task queue
        self._setup_task_queue()
        
        # Load app info
        self._load_app_info()
        
        # Initialize UI components
        self._setup_ui()
        
        # Setup UI components for drag and drop functionality
        self._setup_drag_drop_frames()
        self._setup_combo_boxes()
        
        # Connect signals
        self.grammar_model.state_changed.connect(self._on_grammar_state_changed)
        self.task_queue_model.queue_changed.connect(self._update_task_list)
        self.view.summary_button.clicked.connect(self._on_summary_button_clicked)
        
    def _setup_plot(self):
        """Set up the plot widget"""
        # Plot is already initialized in MainWindow
        self.plot = self.view.plot
        
        # Initialize plot model
        self.plot_model = PlotModel(self.plot)
        
        # Connect plot_updated signal to update the data table
        self.plot_model.plot_updated.connect(self._update_data_table)
        
        # Mouse coordinate tracking in status bar disabled for now
        # Will be implemented in a future update
        
    def _setup_map(self):
        """Set up the map widget with Folium and QWebEngineView"""
        self.logger.info("Setting up map widget")
        
        # Initialize map model
        self.map_model = MapModel()
        
        # Create web view for the map
        self.map_view = QWebEngineView()
        
        # Get the map HTML content
        map_html = self.map_model.get_map_html()
        
        # Load the HTML content into the web view
        self.map_view.setHtml(map_html)
        
        # Replace the placeholder widget with the web view
        map_layout = self.view.verticalLayout  # The layout containing the map_widget
        placeholder = self.view.map_widget     # The placeholder widget
        
        # Add the web view to the layout
        map_layout.replaceWidget(placeholder, self.map_view)
        
        # Hide the original placeholder
        placeholder.hide()
        
        self.logger.info("Map widget setup complete")
        
    def _setup_task_queue(self):
        """Set up the task queue model"""
        self.task_queue_model = TaskQueueModel(self.plot_model, self.data_model)
        
    def _load_app_info(self):
        """Load application information and convert Markdown content to HTML for the intro text browser"""
        try:
            # Get the path to the app_info.yaml file
            app_info_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 
                'app_info.yaml'
            )
            
            # Load the YAML file
            with open(app_info_path, 'r', encoding='utf-8') as f:
                import yaml
                app_info = yaml.safe_load(f)
                
            # Get the Markdown content and CSS
            app_info_dict = app_info.get('app_info', {})
            markdown_content = app_info_dict.get('markdown_intro', '')
            css_style = app_info_dict.get('css_style', '')
            
            if markdown_content:
                # Convert Markdown to HTML with HTML tag support
                import markdown
                html_content = markdown.markdown(
                    markdown_content,
                    extensions=['extra']  # Enables handling of HTML within Markdown
                )
                
                # Combine with CSS
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                {css_style}
                </style>
                </head>
                <body>
                {html_content}
                </body>
                </html>
                """
                
                # Set the HTML content in the text browser
                self.view.appIntro_txtbrwser.setHtml(full_html)
                
                # Enable external links
                self.view.appIntro_txtbrwser.setOpenExternalLinks(True)
                
                # Remove frame for cleaner appearance
                self.view.appIntro_txtbrwser.setFrameShape(QFrame.Shape.NoFrame)
                
                self.logger.info("App introduction content loaded successfully")
            else:
                self.logger.warning("No Markdown content found in app_info.yaml")
                
        except Exception as e:
            self.logger.error(f"Error loading app info: {str(e)}")
            # Set a fallback message
            self.view.appIntro_txtbrwser.setHtml(
                "<h2>Bienvenido a la Aplicación de Análisis de Datos Forestales</h2>"
                "<p>Esta aplicación le permite analizar y visualizar datos forestales.</p>"
            )
            
    def _setup_ui(self):
        """Set up the UI components"""
        # Set up tree widget
        tree = self.view.variables_treewidget
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        # Connect signals
        self.view.load_button.clicked.connect(self._on_load_button_clicked)
        self.view.variables_treewidget.itemChanged.connect(self._on_variable_selection_changed)
        self.view.clear_gg_button.clicked.connect(self._clear_all_frames)
        
        # Connect task queue buttons
        self.view.add_task_button.clicked.connect(self._on_add_task_button_clicked)
        self.view.remove_task_button.clicked.connect(self._on_remove_task_button_clicked)
        self.view.delete_queue_button.clicked.connect(self._on_delete_queue_button_clicked)
        self.view.generateQueue_button.clicked.connect(self._on_generate_queue_button_clicked)
        self.view.tasks_list.itemClicked.connect(self._on_task_item_clicked)
        
        # Connect load and save analysis buttons
        self.view.load_analysis_button.clicked.connect(self._on_load_analysis_button_clicked)
        self.view.save_analysis_button.clicked.connect(self._on_save_analysis_button_clicked)
        
        # Set icons for load and save analysis buttons
        from PyQt6.QtGui import QIcon
        import os
        
        # Get the base path for resources
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons')
        
        # Set load analysis button icon
        load_icon_path = os.path.join(base_path, '16', 'file', 'folder-open.svg')
        if os.path.exists(load_icon_path):
            self.view.load_analysis_button.setIcon(QIcon(load_icon_path))
        
        # Set save analysis button icon
        save_icon_path = os.path.join(base_path, '16', 'action', 'save.svg')
        if os.path.exists(save_icon_path):
            self.view.save_analysis_button.setIcon(QIcon(save_icon_path))
        
        # Ensure the first tabs are selected in both tab widgets
        self._set_initial_tabs()
        
    def _set_initial_tabs(self):
        """Ensure the first tabs are selected in both left and right tab widgets"""
        try:
            # Set the left tab widget to the first tab (index 0)
            if hasattr(self.view, 'left_tabwidget') and self.view.left_tabwidget is not None:
                self.view.left_tabwidget.setCurrentIndex(0)
                self.logger.info("Set left tab widget to first tab")
            
            # Set the right tab widget to the first tab (index 0)
            if hasattr(self.view, 'right_tabwidget') and self.view.right_tabwidget is not None:
                self.view.right_tabwidget.setCurrentIndex(0)
                self.logger.info("Set right tab widget to first tab")
        except Exception as e:
            self.logger.error(f"Error setting initial tabs: {str(e)}")
    
    def _setup_drag_drop_frames(self):
        """Setup drag and drop functionality for existing QFrames"""
        frames_to_setup = [
            ('xaxis_qframe', 'labelPlaceholderX'),
            ('yaxis_qframe', 'labelPlaceholderY'),
            ('color_qframe', 'labelPlaceholderColor'),
            ('size_qframe', 'labelPlaceholderTamanio'),
            ('shape_qframe', 'labelPlaceholderForma'),
            ('alpha_qframe', 'labelPlaceholderTransparencia'),
            ('facetRow_qframe', 'labelPlaceholderFacetaFila'),
            ('facetCol_qframe', 'labelPlaceholderFacetaColumna')
        ]
        
        for frame_id, label_name in frames_to_setup:
            frame: QFrame = getattr(self.view, frame_id)
            label: QLabel = getattr(self.view, label_name)
            
            # Store frame ID and label reference
            frame.frame_id = frame_id
            frame.placeholder_label = label
            
            # Enable drop functionality
            frame.setAcceptDrops(True)
            
            # Add event handlers
            def dragEnterEvent(event: QDragEnterEvent, frame=frame):
                if event.mimeData().hasText():
                    event.accept()  
                    frame.setFrameShadow(QFrame.Shadow.Sunken)
            
            def dragLeaveEvent(event, frame=frame):
                frame.setFrameShadow(QFrame.Shadow.Raised)
            
            def dropEvent(event: QDropEvent, frame=frame):
                variable_name = event.mimeData().text()
                event.accept()  
                if self.grammar_model.handle_variable_drop(frame.frame_id, variable_name):
                    frame.placeholder_label.setText(variable_name)
                    frame.placeholder_label.setStyleSheet("color: black;")  
                    frame.placeholder_label.setEnabled(True)
                frame.setFrameShadow(QFrame.Shadow.Raised)
            
            # Attach event handlers
            frame.dragEnterEvent = lambda event, f=frame: dragEnterEvent(event, f)
            frame.dragLeaveEvent = lambda event, f=frame: dragLeaveEvent(event, f)
            frame.dropEvent = lambda event, f=frame: dropEvent(event, f)
            
            # Add clear method
            def clear(frame=frame):
                if self.grammar_model.clear_frame(frame.frame_id):
                    frame.placeholder_label.setText("Arrastrar variable")
                    frame.placeholder_label.setStyleSheet("")  
                    frame.placeholder_label.setEnabled(False)
            
            frame.clear = lambda f=frame: clear(f)
    
    def _setup_combo_boxes(self):
        """Setup combo boxes for plot type and stat selection"""
        combos_to_setup = {
            'geometry_combo': [
                'Dispersión', 'Líneas', 'Barras', 'Histograma', 'Cajas',
                'Densidad', 'Diagrama de puntos', 'Violín', 'Área'
            ],
            'xAxis_combo': ['lineal', 'log'],
            'yAxis_combo': ['lineal', 'log'],
            'coords_combo': ['cartesiano', 'polar', 'invertido']
        }
        
        for combo_id, values in combos_to_setup.items():
            combo: QComboBox = getattr(self.view, combo_id)
            combo.clear()  # Clear existing items
            combo.addItems(values)
            combo.currentTextChanged.connect(
                lambda text, id=combo_id: self.grammar_model.handle_combo_change(id, text)
            )
            
            # Set initial value to trigger state update
            if combo_id == 'geometry_combo':
                combo.setCurrentText('Dispersión')
    
    def _on_load_button_clicked(self):
        """Handle load button click"""
        file_dialog = QFileDialog(self.view)
        file_dialog.setNameFilter("Excel files (*.xlsx *.xls)")
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            if files:
                filename = files[0]
                self.logger.info("Cargando archivo Excel...")
                success, message = self.data_model.load_excel(filename)
                
                if success:
                    # Enable summary button
                    self.view.summary_button.setEnabled(True)
                    
                    # Show sheet selection dialog
                    self.view.sheetSel_groupBox.show()
                    
                    # Clear and populate sheet list
                    self.view.sheetSelector_widget.clear()
                    for sheet in self.data_model.sheet_names:
                        item = QListWidgetItem(sheet)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Checked)
                        self.view.sheetSelector_widget.addItem(item)
                    
                    # Connect button box signals
                    self.view.buttonBox.accepted.connect(self._on_sheet_selection_accepted)
                    self.view.buttonBox.rejected.connect(self._on_sheet_selection_rejected)
                    
                    # Update status bar with file name
                    self.view.statusBar().showMessage(f"Analizando fichero: {os.path.basename(filename)}")
                    
                    # Log the summary
                    self.logger.info("="*50)
                    self.logger.info("Resumen del Archivo Excel")
                    self.logger.info("="*50)
                    self.logger.info(message)
                    self.logger.info("="*50)
                else:
                    # Clear status bar and show error
                    self.view.statusBar().clearMessage()
                    self.logger.error(f"Error al cargar archivo Excel: {message}")

    def _on_sheet_selection_accepted(self):
        """Handle OK button click in sheet selection"""
        # Get selected sheets
        selected_sheets = []
        for i in range(self.view.sheetSelector_widget.count()):
            item = self.view.sheetSelector_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_sheets.append(item.text())
        
        # Create unified dataframe
        success, message = self.data_model.create_unified_dataframe(selected_sheets)
        
        if success:
            self.logger.info("="*50)
            self.logger.info("Hojas unidas correctamente")
            self.logger.info("="*50)
            self.logger.info(message)
            self.logger.info("="*50)
            
            # Switch to the Graph Builder tab in the left tabwidget
            self.view.left_tabwidget.setCurrentWidget(self.view.graphbuilder_tab)
            
            # Also switch to the Plot tab in the right tabwidget
            self.view.right_tabwidget.setCurrentWidget(self.view.plot_tab)
            
            # Ensure the plot type is set to 'Dispersión' in both the UI and model
            self.view.geometry_combo.setCurrentText('Dispersión')
            self.grammar_model._grammar_state['plot_type'] = 'Dispersión'
            
            # Update plot if grammar state has mappings
            state = self.grammar_model.get_state()
            if state.get('x') and state.get('y'):
                self.logger.info("Actualizando gráfico con nuevos datos")
                self.plot_model.update_plot(state, self.data_model.unified_df)
        else:
            self.logger.error(f"Error al unir hojas: {message}")
        
        # Disconnect signals
        self.view.buttonBox.accepted.disconnect(self._on_sheet_selection_accepted)
        self.view.buttonBox.rejected.disconnect(self._on_sheet_selection_rejected)
    
    def _on_sheet_selection_rejected(self):
        """Handle Cancel button click in sheet selection"""
        # Hide sheet selection
        self.view.sheetSel_groupBox.hide()
        
        # Disconnect signals
        self.view.buttonBox.accepted.disconnect(self._on_sheet_selection_accepted)
        self.view.buttonBox.rejected.disconnect(self._on_sheet_selection_rejected)
        
        self.logger.info("Selección de hojas cancelada")
    
    def _on_variable_selection_changed(self, item: QTreeWidgetItem, column: int):
        """Handle variable selection changes"""
        if column == 0:  # Variable column
            variable_name = item.text(0)
            self.variables_model.variable_selection_changed.emit(variable_name, True)
    
    def _on_grammar_state_changed(self):
        """Handle changes in the grammar state"""
        state = self.grammar_model.get_state()
        
        # Create compact state description
        parts = []
        
        # Add plot type if set
        plot_type = state.get('plot_type')
        if plot_type:
            parts.append(f"Gráfico: {plot_type}")
        
        # Add mapped variables
        mappings = {
            'x': 'x', 'y': 'y', 'color': 'color', 'size': 'tamaño',
            'shape': 'forma', 'alpha': 'transparencia',
            'facet_row': 'fila', 'facet_col': 'columna'
        }
        
        for key, label in mappings.items():
            if state.get(key):
                parts.append(f"{label}: {state[key]}")
        
        # Join all parts with semicolons
        status = "; ".join(parts) if parts else "Sin mapeo"
        
        # Update status label
        self.view.gg_status_label.setText(status)
        
        # Update plot if we have data available
        if hasattr(self.data_model, 'unified_df') and self.data_model.unified_df is not None:
            self.logger.info("Actualizando gráfico con nuevo estado de gramática")
            self.plot_model.update_plot(state, self.data_model.unified_df)
            
            # Switch to the Plot tab in the right tabwidget
            self.view.right_tabwidget.setCurrentWidget(self.view.plot_tab)
        else:
            self.logger.info("No hay datos disponibles para graficar")
    
    def _clear_all_frames(self):
        """Clear all grammar frames to their initial state"""
        frames_to_clear = [
            'xaxis_qframe', 'yaxis_qframe', 'color_qframe', 
            'size_qframe', 'shape_qframe', 'alpha_qframe',
            'facetRow_qframe', 'facetCol_qframe'
        ]
        
        # First clear the grammar model state
        for frame_id in frames_to_clear:
            self.grammar_model.clear_frame(frame_id)
            
            # Then update the UI
            frame = getattr(self.view, frame_id)
            frame.placeholder_label.setText("Arrastrar variable")
            frame.placeholder_label.setStyleSheet("")
            frame.placeholder_label.setEnabled(False)
        
        # Clear the status label
        self.view.gg_status_label.setText("")
    
    def _on_summary_button_clicked(self):
        """Handle summary button click"""
        if not self.data_model.data:
            return
            
        # Show summary dialog
        dialog = SummaryDialog(
            parent=self.view,
            summary_text=self.data_model.get_summary()
        )
        dialog.exec()
        
    def _on_add_task_button_clicked(self):
        """Handle add task button click"""
        # Check if we have data and a valid grammar state
        if not hasattr(self.data_model, 'unified_df') or self.data_model.unified_df is None:
            self.logger.warning("No hay datos disponibles para añadir a la cola")
            return
            
        # Get current grammar state
        state = self.grammar_model.get_state()
        
        # Check if we have necessary mappings
        if not state.get('x') or not state.get('y'):
            self.logger.warning("Se requiere mapeo de X e Y para añadir a la cola")
            return
            
        # Get task name from status label
        task_name = self.view.gg_status_label.text()
        if not task_name:
            task_name = f"Gráfico {len(self.task_queue_model.tasks) + 1}"
            
        # Add task to queue
        self.task_queue_model.add_task(task_name, state)
        
        # Reset grammar state
        self._clear_all_frames()
        
    def _on_remove_task_button_clicked(self):
        """Handle remove task button click"""
        # Remove selected tasks
        removed = self.task_queue_model.remove_selected_tasks()
        if removed > 0:
            self.logger.info(f"Se eliminaron {removed} tareas de la cola")
        else:
            self.logger.info("No hay tareas seleccionadas para eliminar")
            
    def _on_delete_queue_button_clicked(self):
        """Handle delete queue button click"""
        # Ask for confirmation
        if self.task_queue_model.tasks:
            reply = QMessageBox.question(
                self.view,
                "Confirmar eliminación",
                "¿Está seguro de que desea eliminar toda la cola de tareas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Clear queue
                removed = self.task_queue_model.clear_queue()
                self.logger.info(f"Cola de tareas limpiada ({removed} tareas eliminadas)")
        else:
            self.logger.info("No hay tareas en la cola para eliminar")
            
    def _on_generate_queue_button_clicked(self):
        """Handle generate queue button click"""
        # Check if we have tasks
        if not self.task_queue_model.tasks:
            self.logger.warning("No hay tareas en la cola para generar")
            return
            
        # Ask for output directory
        directory = QFileDialog.getExistingDirectory(
            self.view,
            "Seleccionar directorio de salida",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # Generate queue
            success = self.task_queue_model.generate_queue(directory)
            if success:
                self.logger.info(f"Gráficos generados en: {directory}")
                
                # Show success message
                QMessageBox.information(
                    self.view,
                    "Generación completada",
                    f"Los gráficos han sido generados exitosamente en:\n{directory}"
                )
            else:
                self.logger.error("Error al generar gráficos")
                
    def _on_task_item_clicked(self, item):
        """Handle task item click"""
        # Get task index
        index = self.view.tasks_list.row(item)
        
        # Get task
        task = self.task_queue_model.get_task(index)
        if task:
            # Apply grammar state
            self._apply_grammar_state(task.grammar_state)
            
            # Update plot
            if hasattr(self.data_model, 'unified_df') and self.data_model.unified_df is not None:
                self.plot_model.update_plot(task.grammar_state, self.data_model.unified_df)
                
    def _apply_grammar_state(self, state):
        """Apply a grammar state to the UI
        
        Args:
            state: Grammar state dictionary
        """
        # First clear all frames
        self._clear_all_frames()
        
        # Apply combo box selections
        if state.get('plot_type'):
            self.view.geometry_combo.setCurrentText(state['plot_type'])
        if state.get('x_scale'):
            self.view.xAxis_combo.setCurrentText(state['x_scale'])
        if state.get('y_scale'):
            self.view.yAxis_combo.setCurrentText(state['y_scale'])
        if state.get('coords'):
            self.view.coords_combo.setCurrentText(state['coords'])
            
        # Apply variable mappings
        frame_mappings = {
            'x': 'xaxis_qframe',
            'y': 'yaxis_qframe',
            'color': 'color_qframe',
            'size': 'size_qframe',
            'shape': 'shape_qframe',
            'alpha': 'alpha_qframe',
            'facet_row': 'facetRow_qframe',
            'facet_col': 'facetCol_qframe'
        }
        
        for state_key, frame_id in frame_mappings.items():
            variable_name = state.get(state_key)
            if variable_name:
                frame = getattr(self.view, frame_id)
                frame.placeholder_label.setText(variable_name)
                frame.placeholder_label.setStyleSheet("color: black;")
                frame.placeholder_label.setEnabled(True)
                
                # Update grammar model
                self.grammar_model.handle_variable_drop(frame_id, variable_name)
                
    def _update_task_list(self):
        """Update the task list widget"""
        # Clear the list
        self.view.tasks_list.clear()
        
        # Add tasks
        for task in self.task_queue_model.tasks:
            # Create item with checkbox
            item = QListWidgetItem(task.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if task.selected else Qt.CheckState.Unchecked)
            
            # Add to list
            self.view.tasks_list.addItem(item)
            
        # Connect item change signal
        self.view.tasks_list.itemChanged.connect(self._on_task_item_changed)
        
    def _on_task_item_changed(self, item):
        """Handle task item change"""
        # Get task index
        index = self.view.tasks_list.row(item)
        
        # Update task selected state
        selected = item.checkState() == Qt.CheckState.Checked
        self.task_queue_model.set_task_selected(index, selected)
    
    def _on_load_analysis_button_clicked(self):
        """Handle load analysis button click"""
        # Check if we have data loaded
        if not hasattr(self.data_model, 'unified_df') or self.data_model.unified_df is None:
            self.logger.warning("Debe cargar datos antes de cargar un análisis")
            QMessageBox.warning(
                self.view,
                "No hay datos cargados",
                "Debe cargar datos antes de cargar un análisis."
            )
            return
        
        # If there are tasks in the queue, ask for confirmation
        if self.task_queue_model.tasks:
            reply = QMessageBox.question(
                self.view,
                "Confirmar carga",
                "Cargar un análisis reemplazará la cola de tareas actual. ¿Desea continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Load analysis from YAML file
        success = self.task_queue_model.load_analysis_from_yaml()
        
        if success:
            # Update the task list
            self._update_task_list()
            
            # Show success message
            QMessageBox.information(
                self.view,
                "Análisis cargado",
                f"Se han cargado {len(self.task_queue_model.tasks)} tareas."
            )
        else:
            # Show error message if no tasks were loaded
            if not self.task_queue_model.tasks:
                QMessageBox.warning(
                    self.view,
                    "Error al cargar análisis",
                    "No se pudieron cargar tareas del archivo seleccionado."
                )
    
    def _on_save_analysis_button_clicked(self):
        """Handle save analysis button click"""
        # Check if we have tasks to save
        if not self.task_queue_model.tasks:
            self.logger.warning("No hay tareas en la cola para guardar")
            QMessageBox.warning(
                self.view,
                "Cola vacía",
                "No hay tareas en la cola para guardar."
            )
            return
        
        # Save analysis to YAML file
        success = self.task_queue_model.save_analysis_to_yaml()
        
        if success:
            # Show success message
            QMessageBox.information(
                self.view,
                "Análisis guardado",
                f"Se han guardado {len(self.task_queue_model.tasks)} tareas."
            )
        else:
            # Show error message
            QMessageBox.warning(
                self.view,
                "Error al guardar análisis",
                "No se pudo guardar el análisis en el archivo seleccionado."
            )
    
    def _update_data_table(self):
        """Update the data table with the current plot data"""
        if hasattr(self.data_model, 'unified_df') and self.data_model.unified_df is not None:
            state = self.grammar_model.get_state()
            
            # Check if we have necessary mappings for a plot
            if not state.get('x') or not state.get('y'):
                return
                
            # Get the columns that are being used in the plot
            columns_to_show = []
            for key in ['x', 'y', 'color', 'size', 'shape', 'alpha']:
                if state.get(key) and state[key] in self.data_model.unified_df.columns:
                    columns_to_show.append(state[key])
            
            # Create a subset of the dataframe with only the columns used in the plot
            if columns_to_show:
                plot_data = self.data_model.unified_df[columns_to_show].copy()
                
                # Create a table model and set it to the table view
                table_model = DataTableModel(plot_data)
                self.view.data_tableview.setModel(table_model)
                
                # Configure the table view
                self.view.data_tableview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                self.view.data_tableview.verticalHeader().setVisible(True)
                
                # Switch to the Table tab
                self.view.right_tabwidget.setCurrentWidget(self.view.table_tab)
                
                self.logger.info(f"Tabla actualizada con {len(plot_data)} filas y {len(columns_to_show)} columnas")


class DataTableModel(QAbstractTableModel):
    """Model for displaying data in a table view"""
    
    def __init__(self, data):
        super().__init__()
        self._data = data
        
    def rowCount(self, parent=None):
        return len(self._data)
        
    def columnCount(self, parent=None):
        return len(self._data.columns)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            
            # Format the value based on its type
            if pd.isna(value):
                return ""
            elif isinstance(value, (int, float)):
                # Format numbers with 4 decimal places if they're floats
                if isinstance(value, float):
                    return f"{value:.4f}"
                return str(value)
            else:
                return str(value)
                
        return None
        
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section + 1)  # Row numbers starting from 1
                
        return None