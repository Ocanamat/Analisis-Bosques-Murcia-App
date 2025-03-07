from typing import Dict, Optional, List, Tuple, Any
import pandas as pd
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QObject, pyqtSignal, QDateTime, Qt
from PyQt6.QtGui import QColor
import datetime

from ..utils.logging import Logger


class PlotModel(QObject):
    """Model for creating and updating plots based on grammar of graphics state"""
    
    # Signal emitted when the plot is updated
    plot_updated = pyqtSignal()
    
    def __init__(self, plot_widget: pg.PlotWidget):
        super().__init__()
        self.plot_widget = plot_widget
        self.logger = Logger("PlotModel")
        
        # Initialize plot items
        self.plot_items = []
        
        # Set up plot widget
        self._setup_plot_widget()
        
    def _setup_plot_widget(self):
        """Set up the plot widget with default settings"""
        # Set background to white
        self.plot_widget.setBackground('w')
        
        # Add grid
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Set up axes labels with larger font
        font = {'color': 'k', 'size': '12pt'}
        self.plot_widget.getAxis('bottom').setLabel(text='', **font)
        self.plot_widget.getAxis('left').setLabel(text='', **font)
        
        # Enable zooming and panning
        self.plot_widget.setMouseEnabled(x=True, y=True)  # Enable panning by dragging
        self.plot_widget.enableAutoRange()  # Auto-range initially
        self.plot_widget.setAutoVisible(y=True)  # Auto-visible for y-axis
        
        # Enable rectangle zooming
        viewbox = self.plot_widget.getPlotItem().getViewBox()
        viewbox.setMouseMode(pg.ViewBox.RectMode)  # Enable rectangle zooming
        
        # Disable right-click menu for now
        self.plot_widget.setMenuEnabled(False)
        
        # Mouse coordinate tracking and tooltips disabled for now
        self.mouse_coords_label = None  # Will be set from the controller
        
        # Debug info
        self.logger.info(f"Plot widget initialized with size: {self.plot_widget.size()}")
        
        # Set up legend with interactive capabilities
        self.legend = self.plot_widget.addLegend()
        self.legend_items = {}  # To track legend items for toggling
        
        # Store original dataframe for tooltips
        self.current_df = None
        
    def _reset_plot_view(self):
        """Reset the plot view to default"""
        self.plot_widget.autoRange()
        self.logger.info("Vista del gráfico restablecida")
    
    def update_plot(self, grammar_state: Dict[str, Optional[str]], dataframe: pd.DataFrame):
        """Update the plot based on grammar state and dataframe
        
        Args:
            grammar_state: Dictionary mapping aesthetic properties to variable names
            dataframe: Pandas dataframe containing the data to plot
        """
        # Clear existing plot items
        self._clear_plot()
        
        # Store current dataframe and grammar state for tooltips and interactions
        self.current_df = dataframe.copy()
        self.current_grammar_state = grammar_state.copy()
        
        # Check if we have data and necessary mappings
        if dataframe is None or dataframe.empty:
            self.logger.warning("No hay datos disponibles para graficar")
            return
            
        # Get x and y mappings (required for plotting)
        x_var = grammar_state.get('x')
        y_var = grammar_state.get('y')
        
        if not x_var or not y_var:
            self.logger.info("Mapeo de X o Y no establecido, no se puede crear el gráfico")
            return
            
        # Check if variables exist in dataframe
        if x_var not in dataframe.columns or y_var not in dataframe.columns:
            missing = []
            if x_var not in dataframe.columns:
                missing.append(f"X variable '{x_var}'")
            if y_var not in dataframe.columns:
                missing.append(f"Y variable '{y_var}'")
            self.logger.warning(f"Variables faltantes en el dataframe: {', '.join(missing)}")
            return
            
        # Get other aesthetic mappings
        color_var = grammar_state.get('color')
        size_var = grammar_state.get('size')
        alpha_var = grammar_state.get('alpha')
        
        # Always ensure we have a plot type, defaulting to 'Dispersión' if not set
        plot_type = grammar_state.get('plot_type')
        if not plot_type:
            plot_type = 'Dispersión'
            self.logger.info(f"Tipo de gráfico no especificado, usando {plot_type} por defecto")
        
        # Create a working copy of the dataframe
        plot_df = dataframe.copy()
        
        # Handle datetime conversion for x and y variables
        self._convert_datetime_columns(plot_df, [x_var, y_var])
        
        # Set axis labels
        self.plot_widget.getAxis('bottom').setLabel(text=x_var)
        self.plot_widget.getAxis('left').setLabel(text=y_var)
        
        # Create plot based on type
        if plot_type == 'Dispersión':
            self._create_scatter_plot(plot_df, x_var, y_var, color_var, size_var, alpha_var)
        elif plot_type == 'Líneas':
            self._create_line_plot(plot_df, x_var, y_var, color_var)
        elif plot_type == 'Barras':
            self._create_bar_plot(plot_df, x_var, y_var, color_var)
        elif plot_type is None:
            # This should never happen now, but just in case
            self.logger.warning("Tipo de gráfico es None, usando gráfico de dispersión por defecto")
            self._create_scatter_plot(plot_df, x_var, y_var, color_var, size_var, alpha_var)
        else:
            self.logger.warning(f"Tipo de gráfico '{plot_type}' aún no implementado")
            
        # Connect legend items to click events for toggling visibility
        self._connect_legend_toggling()
        
        # Emit signal that plot has been updated
        self.plot_updated.emit()
        
    def _clear_plot(self):
        """Clear all plot items"""
        self.plot_widget.clear()
        self.plot_items = []
        self.legend_items = {}
        
        # Re-add legend
        self.legend = self.plot_widget.addLegend()
        
        # Connect legend item clicks for toggling visibility
        # This needs to be done after items are added to the legend
        # We'll connect this in the update_plot method after all items are added
        
    def _convert_datetime_columns(self, df: pd.DataFrame, columns: List[str]):
        """Convert datetime columns to timestamps for plotting
        
        Args:
            df: Dataframe to modify (in-place)
            columns: List of column names to check and convert if they are datetime
        """
        for col in columns:
            if col in df.columns:
                # Check if column contains datetime-like strings
                if df[col].dtype == 'object':
                    try:
                        # Try to convert to datetime
                        temp_series = pd.to_datetime(df[col])
                        
                        # If successful, convert to timestamp (seconds since epoch)
                        df[col] = temp_series.astype('int64') // 10**9
                        
                        # Create custom time axis if this is the first datetime column we find
                        if not hasattr(self, 'time_axis_set') or not self.time_axis_set:
                            self.logger.info(f"Configurando eje de tiempo para {col}")
                            axis = self.plot_widget.getAxis('bottom') if col == columns[0] else self.plot_widget.getAxis('left')
                            axis.setLabel(text=col)
                            axis.setStyle(tickFont=pg.Qt.QtGui.QFont('Arial', 8))
                            
                            # Create a function to format timestamps as dates
                            def timestamp_to_date(timestamp):
                                try:
                                    dt = datetime.datetime.fromtimestamp(timestamp)
                                    return dt.strftime('%Y-%m-%d')
                                except:
                                    return ''
                            
                            # Set the tick formatter
                            axis.tickFormatter = timestamp_to_date
                            self.time_axis_set = True
                            
                        self.logger.info(f"Convertido {col} de datetime a timestamp para graficar")
                    except Exception as e:
                        self.logger.warning(f"Error al convertir {col} a datetime: {str(e)}")
        
        return df
        
    def _create_scatter_plot(self, df: pd.DataFrame, x_var: str, y_var: str, 
                            color_var: Optional[str] = None, 
                            size_var: Optional[str] = None,
                            alpha_var: Optional[str] = None):
        """Create a scatter plot
        
        Args:
            df: Dataframe containing the data
            x_var: Variable to map to x-axis
            y_var: Variable to map to y-axis
            color_var: Variable to map to color (optional)
            size_var: Variable to map to size (optional)
            alpha_var: Variable to map to transparency (optional)
        """
        # Default scatter plot settings
        symbol_size = 10
        symbol = 'o'
        
        # If no grouping variable, create a single scatter plot
        if not color_var:
            # Get data
            x_data = df[x_var].values
            y_data = df[y_var].values
            
            # Check if data is numeric
            if not np.issubdtype(x_data.dtype, np.number):
                self.logger.warning(f"Variable X '{x_var}' contiene datos no numéricos: {x_data[0]}")
                try:
                    x_data = x_data.astype(float)
                except ValueError:
                    self.logger.error(f"No se pueden graficar datos no numéricos para el eje X: {x_var}")
                    return
                    
            if not np.issubdtype(y_data.dtype, np.number):
                self.logger.warning(f"Variable Y '{y_var}' contiene datos no numéricos: {y_data[0]}")
                try:
                    y_data = y_data.astype(float)
                except ValueError:
                    self.logger.error(f"No se pueden graficar datos no numéricos para el eje Y: {y_var}")
                    return
            
            # Handle size mapping
            if size_var and size_var in df.columns:
                # Normalize size values between 5 and 20
                size_data = df[size_var].values
                if np.issubdtype(size_data.dtype, np.number):
                    min_val, max_val = size_data.min(), size_data.max()
                    if min_val != max_val:
                        normalized_sizes = 5 + 15 * (size_data - min_val) / (max_val - min_val)
                        scatter = pg.ScatterPlotItem(x=x_data, y=y_data, size=normalized_sizes, 
                                                    pen=None, brush=QColor(0, 114, 189, 150))
                    else:
                        scatter = pg.ScatterPlotItem(x=x_data, y=y_data, size=symbol_size, 
                                                    pen=None, brush=QColor(0, 114, 189, 150))
                else:
                    self.logger.warning(f"Variable de tamaño '{size_var}' no es numérica")
                    scatter = pg.ScatterPlotItem(x=x_data, y=y_data, size=symbol_size, 
                                                pen=None, brush=QColor(0, 114, 189, 150))
            else:
                scatter = pg.ScatterPlotItem(x=x_data, y=y_data, size=symbol_size, 
                                            pen=None, brush=QColor(0, 114, 189, 150))
                
            # Tooltip functionality disabled for now
            # Will be implemented in a future update
            
            # Add scatter to plot
            self.plot_widget.addItem(scatter)
            self.plot_items.append(scatter)
            
        else:
            # Group by color variable
            if color_var in df.columns:
                # Get unique values of color variable
                color_values = df[color_var].unique()
                
                # Color palette (using standard colors)
                colors = [
                    QColor(0, 114, 189),  # blue
                    QColor(217, 83, 25),   # orange
                    QColor(237, 177, 32),  # yellow
                    QColor(126, 47, 142),  # purple
                    QColor(119, 172, 48),  # green
                    QColor(77, 190, 238),  # light blue
                    QColor(162, 20, 47)    # dark red
                ]
                
                # Create scatter plot for each group
                for i, value in enumerate(color_values):
                    # Get data for this group
                    group_df = df[df[color_var] == value]
                    x_data = group_df[x_var].values
                    y_data = group_df[y_var].values
                    
                    # Check if data is numeric
                    if not np.issubdtype(x_data.dtype, np.number):
                        self.logger.warning(f"Variable X '{x_var}' en grupo de color '{value}' contiene datos no numéricos")
                        try:
                            x_data = x_data.astype(float)
                        except ValueError:
                            self.logger.error(f"No se pueden graficar datos no numéricos para el eje X en grupo de color '{value}'")
                            continue
                            
                    if not np.issubdtype(y_data.dtype, np.number):
                        self.logger.warning(f"Variable Y '{y_var}' en grupo de color '{value}' contiene datos no numéricos")
                        try:
                            y_data = y_data.astype(float)
                        except ValueError:
                            self.logger.error(f"No se pueden graficar datos no numéricos para el eje Y en grupo de color '{value}'")
                            continue
                    
                    # Skip empty groups after filtering
                    if len(x_data) == 0 or len(y_data) == 0:
                        self.logger.warning(f"No hay puntos de datos válidos para el grupo de color '{value}'")
                        continue
                    
                    # Get color with some transparency
                    color_idx = i % len(colors)
                    color = colors[color_idx]
                    color.setAlpha(150)
                    
                    # Create scatter plot
                    scatter = pg.ScatterPlotItem(x=x_data, y=y_data, size=symbol_size, 
                                                pen=None, brush=color, name=str(value))
                    
                    # Tooltip functionality disabled for now
                    # Will be implemented in a future update
                    
                    # Add to plot
                    self.plot_widget.addItem(scatter)
                    self.plot_items.append(scatter)
                    
                    # Store legend item for toggling
                    self.legend_items[str(value)] = {
                        'plot_item': scatter,
                        'visible': True
                    }
            else:
                self.logger.warning(f"Variable de color '{color_var}' no encontrada en el dataframe")
                # Fall back to single scatter plot
                self._create_scatter_plot(df, x_var, y_var)
                
    def _create_line_plot(self, df: pd.DataFrame, x_var: str, y_var: str, color_var: Optional[str] = None):
        """Create a line plot
        
        Args:
            df: Dataframe containing the data
            x_var: Variable to map to x-axis
            y_var: Variable to map to y-axis
            color_var: Variable to map to color (optional)
        """
        # If no grouping variable, create a single line plot
        if not color_var:
            # Sort data by x value for proper line connections
            sorted_df = df.sort_values(by=x_var)
            x_data = sorted_df[x_var].values
            y_data = sorted_df[y_var].values
            
            # Create line plot
            line = pg.PlotDataItem(x=x_data, y=y_data, pen=QColor(0, 114, 189))
            
            # Improve hover events for tooltips
            line.setToolTip('')
            line.curve.setClickable(True)  # Make line clickable for hover events
            
            # Create a custom hover event handler that shows tooltips
            def hover_event_handler(plot_item, points):
                self._show_point_tooltip(points, x_var, y_var)
                
            line.sigPointsHovered.connect(hover_event_handler)
            
            # Make the line more interactive with symbols at data points
            line.setSymbol('o')  # Show points on the line
            line.setSymbolSize(7)  # Size of the points
            
            # Add to plot
            self.plot_widget.addItem(line)
            self.plot_items.append(line)
            
        else:
            # Group by color variable
            if color_var in df.columns:
                # Get unique values of color variable
                color_values = df[color_var].unique()
                
                # Color palette (using standard colors)
                colors = [
                    QColor(0, 114, 189),  # blue
                    QColor(217, 83, 25),   # orange
                    QColor(237, 177, 32),  # yellow
                    QColor(126, 47, 142),  # purple
                    QColor(119, 172, 48),  # green
                    QColor(77, 190, 238),  # light blue
                    QColor(162, 20, 47)    # dark red
                ]
                
                # Create line plot for each group
                for i, value in enumerate(color_values):
                    # Get data for this group and sort by x
                    group_df = df[df[color_var] == value].sort_values(by=x_var)
                    x_data = group_df[x_var].values
                    y_data = group_df[y_var].values
                    
                    # Get color
                    color_idx = i % len(colors)
                    color = colors[color_idx]
                    
                    # Create line plot
                    line = pg.PlotDataItem(x=x_data, y=y_data, pen=color, name=str(value))
                    
                    # Improve hover events for tooltips
                    line.setToolTip('')
                    line.curve.setClickable(True)  # Make line clickable for hover events
                    
                    # Create a custom hover event handler that shows tooltips
                    def hover_event_handler(plot_item, points):
                        self._show_point_tooltip(points, x_var, y_var, color_var=color_var, color_value=value)
                    
                    line.sigPointsHovered.connect(hover_event_handler)
                    
                    # Make the line more interactive with symbols at data points
                    line.setSymbol('o')  # Show points on the line
                    line.setSymbolSize(7)  # Size of the points
                    
                    # Add to plot
                    self.plot_widget.addItem(line)
                    self.plot_items.append(line)
                    
                    # Store legend item for toggling
                    self.legend_items[str(value)] = {
                        'plot_item': line,
                        'visible': True
                    }
            else:
                self.logger.warning(f"Variable de color '{color_var}' no encontrada en el dataframe")
                # Fall back to single line plot
                self._create_line_plot(df, x_var, y_var)
                
    # Tooltip and mouse coordinate tracking functionality has been disabled
    # These features will be implemented in a future update
    
    def _connect_legend_toggling(self):
        """Connect legend items to click events for toggling visibility"""
        if not hasattr(self, 'legend') or self.legend is None:
            return
            
        # PyQtGraph doesn't have a direct way to connect to legend item clicks
        # We need to use a workaround by finding the legend items and connecting to their clicks
        try:
            # Check if the legend has items attribute
            if not hasattr(self.legend, 'items'):
                self.logger.debug("La leyenda no tiene items para conectar eventos")
                return
                
            # Get the legend's layout items
            legend_items = self.legend.items
            
            # For each legend item, connect its label to a click event
            for item_pair in legend_items:
                # Check if we have a valid item pair
                if not isinstance(item_pair, (list, tuple)) or len(item_pair) < 2:
                    continue
                    
                label, item = item_pair
                
                # Skip if we don't have a valid label
                if not hasattr(label, 'mousePressEvent'):
                    continue
                    
                # Skip if we don't have a valid text property
                if not hasattr(label, 'text'):
                    continue
                    
                # Store the original mousePressEvent
                original_mouse_press = label.mousePressEvent
                
                # Create a new mousePressEvent that toggles visibility
                def create_click_handler(name, original_handler):
                    def click_handler(event):
                        # Call original handler first
                        original_handler(event)
                        # Then toggle the item
                        self._toggle_legend_item(name)
                    return click_handler
                
                # Get the name from the label text
                name = label.text
                
                # Set the new mousePressEvent
                label.mousePressEvent = create_click_handler(name, original_mouse_press)
                
                # Change cursor to indicate clickable
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                
                self.logger.debug(f"Conectado evento de clic para leyenda '{name}'")
        except Exception as e:
            self.logger.warning(f"Error al conectar eventos de clic de leyenda: {str(e)}")
    
    def _toggle_legend_item(self, legend_name: str):
        """Toggle visibility of a plot item from the legend
        
        Args:
            legend_name: Name of the legend item to toggle
        """
        if legend_name in self.legend_items:
            item_info = self.legend_items[legend_name]
            plot_item = item_info['plot_item']
            
            # Toggle visibility
            is_visible = item_info['visible']
            plot_item.setVisible(not is_visible)
            
            # Update state
            self.legend_items[legend_name]['visible'] = not is_visible
            
            self.logger.info(f"Serie '{legend_name}' {'ocultada' if is_visible else 'mostrada'}")
    
    def _create_bar_plot(self, df: pd.DataFrame, x_var: str, y_var: str, color_var: Optional[str] = None):
        """Create a bar plot
        
        Args:
            df: Dataframe containing the data
            x_var: Variable to map to x-axis (categories)
            y_var: Variable to map to y-axis (values)
            color_var: Variable to map to color (optional)
        """
        # For bar plots, we need to aggregate data if x has duplicate values
        if df[x_var].duplicated().any():
            # Group by x and calculate mean of y
            agg_df = df.groupby(x_var)[y_var].mean().reset_index()
        else:
            agg_df = df
            
        # Get unique x values and corresponding y values
        x_categories = agg_df[x_var].values
        y_values = agg_df[y_var].values
        
        # Convert categories to positions if not numeric
        if not np.issubdtype(agg_df[x_var].dtype, np.number):
            x_positions = np.arange(len(x_categories))
            # Create custom axis with category labels
            ticks = [(i, str(cat)) for i, cat in enumerate(x_categories)]
            self.plot_widget.getAxis('bottom').setTicks([ticks])
        else:
            x_positions = x_categories
        
        # Create bar plot
        bar_width = 0.6  # Width of bars
        
        # If no color variable, use single color for all bars
        if not color_var:
            # Create bar graph using BarGraphItem
            bar_graph = pg.BarGraphItem(x=x_positions, height=y_values, width=bar_width, 
                                       brush=QColor(0, 114, 189, 150))
            
            # Add to plot
            self.plot_widget.addItem(bar_graph)
            self.plot_items.append(bar_graph)
            
        else:
            # Not implemented yet - fall back to single color
            self.logger.warning("Gráficos de barras con agrupación por color aún no implementados")
            self._create_bar_plot(df, x_var, y_var)
