# Forest Dashboard Architecture

This document provides an overview of the Forest Dashboard application architecture for developers who want to understand, modify, or extend the codebase.

## Overview

The Forest Dashboard application follows the Model-View-Controller (MVC) architectural pattern:

- **Models**: Handle data processing, storage, and business logic
- **Views**: Define the UI components (using PyQt6)
- **Controllers**: Connect models and views, handling user interactions

## Project Structure

```
src/
├── bosques_app/
│   ├── config/           # Configuration files and settings
│   ├── controllers/      # Controller classes
│   ├── models/           # Model classes
│   ├── resources/        # Images, icons, and other resources
│   ├── ui/               # UI definition files (.ui)
│   └── utils/            # Utility functions and classes
└── main.py               # Application entry point
```

## Key Components

### Models

- **DataModel**: Handles loading and processing Excel data
- **PlotModel**: Creates and manages plots based on grammar of graphics
- **GrammarModel**: Manages the state of the grammar of graphics
- **VariablesModel**: Handles variable selection and management
- **MapModel**: Manages map visualization
- **TaskQueueModel**: Handles task queue management

### Controllers

- **MainController**: Primary controller that coordinates all components
- **DialogControllers**: Handle various dialog interactions

### Views

- **MainWindow**: Primary application window defined in main_window.ui
- **Dialogs**: Various dialog windows for specific interactions

## Data Flow

1. User loads an Excel file via the UI
2. MainController passes the file to DataModel
3. DataModel processes the file and creates a unified dataframe
4. User selects variables and maps them to visual properties
5. GrammarModel updates its state based on user selections
6. PlotModel creates visualizations based on the grammar state and data
7. MainController updates the UI to display the visualizations and data tables

## Interactive Features

The application includes several interactive features:

1. **Zooming and Panning**: Implemented in PlotModel using PyQtGraph's capabilities
2. **Tooltips**: Custom implementation using QToolTip to display data point information
3. **Legend Toggling**: Implemented in PlotModel to show/hide data series
4. **Data Tables**: Displays the subset of data used in plots using a custom DataTableModel

## Extension Points

When extending the application, consider these key integration points:

1. **Adding New Plot Types**: Extend PlotModel with new plot creation methods
2. **Supporting New Data Sources**: Extend DataModel with new data loading methods
3. **Adding UI Components**: Modify main_window.ui and update MainController
4. **Adding New Analysis Features**: Create new models and integrate with MainController

## Technology Stack

- **PyQt6**: UI framework
- **PyQtGraph**: Interactive plotting library
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **Markdown**: Documentation formatting

## Development Guidelines

1. **Docstrings**: Use Google-style docstrings for all classes and methods
2. **Logging**: Use the Logger class for all logging needs
3. **Error Handling**: Use try-except blocks with appropriate error messages
4. **UI Updates**: Make UI changes in Qt Designer when possible
5. **Testing**: Write tests for new functionality

## Common Development Tasks

### Adding a New Plot Type

1. Add a new option to the plot type dropdown in main_window.ui
2. Create a new plot creation method in PlotModel
3. Update the update_plot method in PlotModel to call your new method

### Supporting a New Data Format

1. Add a new data loading method to DataModel
2. Update the UI to support selecting the new format
3. Modify create_unified_dataframe to handle the new format
