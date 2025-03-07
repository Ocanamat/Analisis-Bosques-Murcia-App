# Bosques App

Qt6-based GUI application for forest management.

## Installation

### Using Poetry (recommended)
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run the application
poetry run bosques-app
```

### Using Conda
```bash
# Create and activate the environment
conda create -n qt6_dev_env python=3.8
conda activate qt6_dev_env

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Development Setup
```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest
```

## Project Structure
```
project/
├── README.md                  # Project overview and instructions
├── requirements.txt           # Project dependencies
├── setup.py                   # Packaging and distribution configuration
├── .gitignore                 # Files/folders to exclude from version control
├── docs/                      # Documentation
│   └── ...
├── src/
│   ├── main.py                # Application entry point
│   └── bosques_app/           # Main application package
│       ├── __init__.py
│       ├── app.py             # Application initialization and main loop
│       ├── ui/                # UI design files and generated code
│       │   ├── __init__.py
│       │   ├── main_window.ui # Qt Designer UI file
│       │   ├── main_window.py # Generated Python code from .ui file
│       │   └── dialogs/       # Subfolder for dialog UI files
│       │       ├── __init__.py
│       │       ├── about_dialog.ui
│       │       ├── about_dialog.py
│       │       └── ...
│       ├── views/             # Custom widget implementations (hand-coded UI)
│       │   ├── __init__.py
│       │   └── custom_widget.py
│       ├── controllers/       # Controllers that handle interactions
│       │   ├── __init__.py
│       │   ├── main_controller.py
│       │   └── dialog_controllers.py
│       ├── models/            # Data models and business logic
│       │   ├── __init__.py
│       │   ├── data_model.py
│       │   └── settings.py
│       ├── utils/             # Utility functions and classes
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── logging.py
│       └── resources/         # Static resources (images, icons, styles)
│           ├── images/
│           │   └── logo.png
│           ├── qss/
│           │   └── style.qss
│           └── qrc/           # Qt Resource Collection files
│               ├── resources.qrc
│               └── resources_rc.py
└── tests/                     # Unit and integration tests
    ├── __init__.py
    ├── test_models.py
    ├── test_controllers.py
    └── ...

