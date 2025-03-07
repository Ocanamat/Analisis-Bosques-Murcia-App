from typing import Dict, List, Optional, Any
import os
import json
import yaml
from datetime import datetime
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import pyqtgraph as pg
# Use Agg backend for matplotlib to avoid conflicts with PyQt
import matplotlib
matplotlib.use('Agg')  # Set the backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np

from ..utils.logging import Logger


class GraphTask:
    """Class representing a graph task in the queue"""
    
    def __init__(self, name: str, grammar_state: Dict[str, Any], preview_image=None):
        """Initialize a graph task
        
        Args:
            name: Descriptive name for the graph
            grammar_state: Copy of the grammar state used to create the graph
            preview_image: Optional thumbnail image
        """
        self.name = name
        self.grammar_state = grammar_state
        self.preview_image = preview_image
        self.selected = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            'name': self.name,
            'grammar_state': self.grammar_state,
            'selected': self.selected
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphTask':
        """Create task from dictionary"""
        task = cls(
            name=data['name'],
            grammar_state=data['grammar_state']
        )
        task.selected = data.get('selected', False)
        return task


class TaskQueueModel(QObject):
    """Model for managing a queue of graph tasks"""
    
    # Signal emitted when the queue changes
    queue_changed = pyqtSignal()
    
    def __init__(self, plot_model=None, data_model=None):
        """Initialize the task queue model
        
        Args:
            plot_model: Reference to the plot model for rendering graphs
            data_model: Reference to the data model for accessing data
        """
        super().__init__()
        self.tasks: List[GraphTask] = []
        self.plot_model = plot_model
        self.data_model = data_model
        self.logger = Logger("TaskQueueModel")
    
    def add_task(self, name: str, grammar_state: Dict[str, Any]) -> bool:
        """Add a new task to the queue
        
        Args:
            name: Descriptive name for the graph
            grammar_state: Copy of the grammar state used to create the graph
            
        Returns:
            bool: True if task was added successfully
        """
        # Create a deep copy of the grammar state
        state_copy = grammar_state.copy()
        
        # Create and add the task
        task = GraphTask(name, state_copy)
        self.tasks.append(task)
        
        # Emit signal
        self.queue_changed.emit()
        self.logger.info(f"Tarea añadida a la cola: {name}")
        return True
    
    def remove_selected_tasks(self) -> int:
        """Remove all selected tasks from the queue
        
        Returns:
            int: Number of tasks removed
        """
        initial_count = len(self.tasks)
        self.tasks = [task for task in self.tasks if not task.selected]
        removed_count = initial_count - len(self.tasks)
        
        if removed_count > 0:
            self.queue_changed.emit()
            self.logger.info(f"Se eliminaron {removed_count} tareas de la cola")
        
        return removed_count
    
    def clear_queue(self) -> int:
        """Clear all tasks from the queue
        
        Returns:
            int: Number of tasks removed
        """
        count = len(self.tasks)
        self.tasks = []
        
        if count > 0:
            self.queue_changed.emit()
            self.logger.info(f"Cola de tareas limpiada ({count} tareas eliminadas)")
        
        return count
    
    def get_task(self, index: int) -> Optional[GraphTask]:
        """Get task at the specified index
        
        Args:
            index: Index of the task to get
            
        Returns:
            GraphTask or None if index is out of range
        """
        if 0 <= index < len(self.tasks):
            return self.tasks[index]
        return None
    
    def set_task_selected(self, index: int, selected: bool) -> bool:
        """Set the selected state of a task
        
        Args:
            index: Index of the task to update
            selected: New selected state
            
        Returns:
            bool: True if task was updated successfully
        """
        if 0 <= index < len(self.tasks):
            self.tasks[index].selected = selected
            self.queue_changed.emit()
            return True
        return False
    
    def generate_queue(self, output_dir: str) -> bool:
        """Generate a text file with the queue information in the specified directory
        
        Args:
            output_dir: Directory to save the text file to
            
        Returns:
            bool: True if the text file was generated successfully
        """
        if not self.tasks:
            self.logger.warning("No hay tareas en la cola para generar")
            return False
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.logger.error(f"Error al crear directorio de salida: {e}")
                return False
        
        try:
            # Create a filename with the current date and time
            current_datetime = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{current_datetime}_ListaGraficos.txt"
            filepath = os.path.join(output_dir, filename)
            
            # Create the text file with the queue information
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("LISTA DE GRÁFICOS\n")
                f.write("=================\n\n")
                f.write(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write information about each task
                for i, task in enumerate(self.tasks):
                    f.write(f"Gráfico {i+1}: {task.name}\n")
                    f.write("-" * (len(f"Gráfico {i+1}: {task.name}")) + "\n")
                    
                    # Write grammar state
                    f.write("Configuración:\n")
                    
                    # Plot type
                    plot_type = task.grammar_state.get('plot_type', 'No especificado')
                    f.write(f"  - Tipo de gráfico: {plot_type}\n")
                    
                    # Mappings
                    mappings = [
                        ('x', 'Eje X'),
                        ('y', 'Eje Y'),
                        ('color', 'Color'),
                        ('size', 'Tamaño'),
                        ('shape', 'Forma'),
                        ('alpha', 'Transparencia'),
                        ('facet_row', 'Faceta (fila)'),
                        ('facet_col', 'Faceta (columna)')
                    ]
                    
                    for key, label in mappings:
                        value = task.grammar_state.get(key)
                        if value:
                            f.write(f"  - {label}: {value}\n")
                    
                    # Scales
                    x_scale = task.grammar_state.get('x_scale', 'lineal')
                    y_scale = task.grammar_state.get('y_scale', 'lineal')
                    f.write(f"  - Escala X: {x_scale}\n")
                    f.write(f"  - Escala Y: {y_scale}\n")
                    
                    # Coordinates
                    coords = task.grammar_state.get('coords', 'cartesiano')
                    f.write(f"  - Coordenadas: {coords}\n")
                    
                    # Add a separator between tasks
                    f.write("\n" + "=" * 50 + "\n\n")
                
                # Add a footer
                f.write(f"Total de gráficos: {len(self.tasks)}\n")
            
            self.logger.info(f"Lista de gráficos guardada en: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al generar lista de gráficos: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def save_analysis_to_yaml(self, filepath: str = None) -> bool:
        """Save the current task queue to a YAML file
        
        Args:
            filepath: Path to save the YAML file. If None, a file dialog will be shown.
            
        Returns:
            bool: True if the file was saved successfully
        """
        if not self.tasks:
            self.logger.warning("No hay tareas en la cola para guardar")
            return False
        
        # If no filepath is provided, show a file dialog
        if filepath is None:
            filepath, _ = QFileDialog.getSaveFileName(
                None, 
                "Guardar Análisis", 
                os.path.expanduser("~"),
                "Archivos YAML (*.yaml);;Todos los archivos (*)"
            )
            
            if not filepath:  # User cancelled
                return False
                
            # Add .yaml extension if not present
            if not filepath.lower().endswith('.yaml'):
                filepath += '.yaml'
        
        try:
            # Create the data structure to save
            data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'description': 'Análisis de datos forestales',
                'tasks': []
            }
            
            # Add each task to the data
            for i, task in enumerate(self.tasks):
                task_data = {
                    'id': i + 1,
                    'name': task.name,
                    'plot_type': task.grammar_state.get('plot_type', 'No especificado'),
                    'variables': {},
                    'aesthetics': {},
                    'coordinates': {},
                    'facet_settings': {}
                }
                
                # Add variable mappings
                for key in ['x', 'y', 'color', 'size', 'shape', 'alpha']:
                    if key in task.grammar_state and task.grammar_state[key]:
                        task_data['variables'][key] = task.grammar_state[key]
                
                # Add aesthetic settings
                for key in ['title', 'x_label', 'y_label', 'color_palette']:
                    if key in task.grammar_state and task.grammar_state[key]:
                        task_data['aesthetics'][key] = task.grammar_state[key]
                
                # Add coordinate settings
                task_data['coordinates']['flip'] = task.grammar_state.get('coords') == 'flip'
                task_data['coordinates']['x_scale'] = task.grammar_state.get('x_scale', 'lineal')
                task_data['coordinates']['y_scale'] = task.grammar_state.get('y_scale', 'lineal')
                
                # Add facet settings
                if 'facet_row' in task.grammar_state or 'facet_col' in task.grammar_state:
                    task_data['facet_settings']['rows'] = task.grammar_state.get('facet_row', None)
                    task_data['facet_settings']['cols'] = task.grammar_state.get('facet_col', None)
                    task_data['facet_settings']['scales'] = task.grammar_state.get('facet_scales', 'fixed')
                
                # Add the full grammar state for future compatibility
                task_data['grammar_state'] = task.grammar_state
                
                # Add the task to the data
                data['tasks'].append(task_data)
            
            # Save the data to the YAML file
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            self.logger.info(f"Análisis guardado en: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar análisis: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def load_analysis_from_yaml(self, filepath: str = None) -> bool:
        """Load a task queue from a YAML file
        
        Args:
            filepath: Path to the YAML file to load. If None, a file dialog will be shown.
            
        Returns:
            bool: True if the file was loaded successfully
        """
        # If no filepath is provided, show a file dialog
        if filepath is None:
            filepath, _ = QFileDialog.getOpenFileName(
                None, 
                "Cargar Análisis", 
                os.path.expanduser("~"),
                "Archivos YAML (*.yaml);;Todos los archivos (*)"
            )
            
            if not filepath:  # User cancelled
                return False
        
        if not os.path.exists(filepath):
            self.logger.error(f"El archivo no existe: {filepath}")
            return False
        
        try:
            # Load the data from the YAML file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Validate the data
            if not isinstance(data, dict) or 'tasks' not in data or not isinstance(data['tasks'], list):
                self.logger.error("Formato de archivo inválido")
                return False
            
            # Check version for compatibility
            version = data.get('version', '1.0')
            if version != '1.0':
                self.logger.warning(f"Versión de archivo ({version}) puede no ser compatible")
            
            # Clear the current queue
            old_tasks = self.tasks.copy()
            self.tasks = []
            
            # Add each task from the file
            for task_data in data['tasks']:
                # Check if we have the full grammar state
                if 'grammar_state' in task_data:
                    grammar_state = task_data['grammar_state']
                else:
                    # Reconstruct grammar state from individual fields
                    grammar_state = {}
                    
                    # Add plot type
                    grammar_state['plot_type'] = task_data.get('plot_type', 'Dispersión')
                    
                    # Add variable mappings
                    if 'variables' in task_data:
                        for key, value in task_data['variables'].items():
                            grammar_state[key] = value
                    
                    # Add aesthetic settings
                    if 'aesthetics' in task_data:
                        for key, value in task_data['aesthetics'].items():
                            grammar_state[key] = value
                    
                    # Add coordinate settings
                    if 'coordinates' in task_data:
                        coords = task_data['coordinates']
                        if coords.get('flip', False):
                            grammar_state['coords'] = 'flip'
                        else:
                            grammar_state['coords'] = 'cartesiano'
                        
                        grammar_state['x_scale'] = coords.get('x_scale', 'lineal')
                        grammar_state['y_scale'] = coords.get('y_scale', 'lineal')
                    
                    # Add facet settings
                    if 'facet_settings' in task_data:
                        facet = task_data['facet_settings']
                        if 'rows' in facet and facet['rows']:
                            grammar_state['facet_row'] = facet['rows']
                        if 'cols' in facet and facet['cols']:
                            grammar_state['facet_col'] = facet['cols']
                        if 'scales' in facet:
                            grammar_state['facet_scales'] = facet['scales']
                
                # Create the task
                task = GraphTask(
                    name=task_data.get('name', f"Gráfico {len(self.tasks) + 1}"),
                    grammar_state=grammar_state
                )
                
                # Add the task to the queue
                self.tasks.append(task)
            
            # If no tasks were loaded, restore the old tasks
            if not self.tasks and old_tasks:
                self.tasks = old_tasks
                self.logger.warning("No se pudieron cargar tareas del archivo")
                return False
            
            # Emit signal to update the UI
            self.queue_changed.emit()
            
            self.logger.info(f"Análisis cargado desde: {filepath} ({len(self.tasks)} tareas)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al cargar análisis: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _create_matplotlib_plot(self, ax, grammar_state, dataframe):
        """Create a matplotlib plot based on grammar state
        
        Args:
            ax: Matplotlib axes to plot on
            grammar_state: Grammar state dictionary
            dataframe: Pandas dataframe with data
        """
        # Get x and y mappings (required for plotting)
        x_var = grammar_state.get('x')
        y_var = grammar_state.get('y')
        
        if not x_var or not y_var or x_var not in dataframe.columns or y_var not in dataframe.columns:
            raise ValueError("Variables de mapeo X o Y no válidas")
        
        # Get other aesthetic mappings
        color_var = grammar_state.get('color')
        size_var = grammar_state.get('size')
        alpha_var = grammar_state.get('alpha')
        
        # Get plot type
        plot_type = grammar_state.get('plot_type', 'Dispersión')
        
        # Create plot based on type
        if plot_type == 'Dispersión':
            if color_var and color_var in dataframe.columns:
                # Create scatter plot with color mapping
                for color_value in dataframe[color_var].unique():
                    subset = dataframe[dataframe[color_var] == color_value]
                    ax.scatter(subset[x_var], subset[y_var], label=str(color_value))
                ax.legend()
            else:
                # Simple scatter plot
                ax.scatter(dataframe[x_var], dataframe[y_var])
        
        elif plot_type == 'Líneas':
            if color_var and color_var in dataframe.columns:
                # Create line plot with color mapping
                for color_value in dataframe[color_var].unique():
                    subset = dataframe[dataframe[color_var] == color_value]
                    ax.plot(subset[x_var], subset[y_var], label=str(color_value))
                ax.legend()
            else:
                # Simple line plot
                ax.plot(dataframe[x_var], dataframe[y_var])
        
        elif plot_type == 'Barras':
            if color_var and color_var in dataframe.columns:
                # Group by x and color, then plot
                grouped = dataframe.groupby([x_var, color_var])[y_var].mean().unstack()
                grouped.plot(kind='bar', ax=ax)
            else:
                # Simple bar plot
                dataframe.groupby(x_var)[y_var].mean().plot(kind='bar', ax=ax)
        
        elif plot_type == 'Histograma':
            ax.hist(dataframe[x_var], bins=20)
        
        else:
            # Default to scatter plot for other types
            ax.scatter(dataframe[x_var], dataframe[y_var])
        
        # Set labels
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f"{plot_type}: {x_var} vs {y_var}")
        
        # Apply axis scales
        x_scale = grammar_state.get('x_scale', 'lineal')
        y_scale = grammar_state.get('y_scale', 'lineal')
        
        if x_scale == 'log':
            ax.set_xscale('log')
        if y_scale == 'log':
            ax.set_yscale('log')
