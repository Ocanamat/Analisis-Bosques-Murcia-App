"""Application settings and constants"""

import os
import yaml
from pathlib import Path

class Settings:
    """Application settings and constants"""
    
    # Get the directory containing this script
    CONFIG_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = CONFIG_DIR.parent
    
    # Load variable definitions
    with open(CONFIG_DIR / 'variables.yaml', 'r', encoding='utf-8') as f:
        _variables_config = yaml.safe_load(f)
        
    # Extract variable information
    PREDEFINED_VARIABLES = [
        (var['origin'], var['name'], var['type'])
        for var in _variables_config['variables']
    ]
    
    # Get numeric variables
    NUMERIC_VARIABLES = {
        var['name']
        for var in _variables_config['variables']
        if var['type'] == 'Numérica'
    }
    
    # Column indices for tree view
    COLUMN_INDICES = {
        'VARIABLE': 0,
        'TYPE': 1  # Updated indices after removing origin column
    }
    
    # Grammar of graphics state keys
    GRAMMAR_STATE_KEYS = {
        'x': None,
        'y': None,
        'color': None,
        'size': None,
        'shape': None,
        'alpha': None,
        'facet_row': None,
        'facet_col': None,
        'plot_type': None,
        'stat': None
    }
    
    # Mapping of frame IDs to state keys
    FRAME_TO_STATE = {
        'xaxis_qframe': 'x',
        'yaxis_qframe': 'y',
        'color_qframe': 'color',
        'size_qframe': 'size',
        'shape_qframe': 'shape',
        'alpha_qframe': 'alpha',
        'facetRow_qframe': 'facet_row',
        'facetCol_qframe': 'facet_col'
    }
    
    # Mapping of combo box IDs to state keys
    COMBO_TO_STATE = {
        'geometry_combo': 'plot_type',
        'xAxis_combo': 'x_scale',
        'yAxis_combo': 'y_scale',
        'coords_combo': 'coords'
    }
