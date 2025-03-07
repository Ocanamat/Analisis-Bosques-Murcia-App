# Bosques App

Qt6-based GUI application for forest management. This application allows users to load Excel files, map variables to grammar of graphics features, and generate visualizations that can be saved and exported.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Development](#development)
- [Project Structure](#project-structure)
- [Package Management](#package-management)
- [Documentation](#documentation)
- [Creating an Executable](#creating-an-executable)
- [License](#license)

## Overview

Bosques App is a Python-Qt6 application designed for forest management and visualization. Key features include:
- Loading and processing Excel files
- Mapping variables to grammar of graphics features
- Generating and customizing visualizations
- Saving/loading grammar of graphics specifications
- Exporting graphs as JPG/PNG

## Installation

### Using Poetry (Recommended)

[Poetry](https://python-poetry.org/) provides the most streamlined installation experience:

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run the application
poetry run bosques-app
```

### Using Conda

For Conda users, you can set up the environment as follows:

```bash
# Create and activate the environment
conda create -n qt6_dev_env python=3.8
conda activate qt6_dev_env

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Complete Conda Environment Setup

For a full reproduction of the development environment:

```bash
# Create a new conda environment
conda create -n qt6_dev_env python=3.8

# Activate the environment
conda activate qt6_dev_env

# Install core dependencies
conda install -c conda-forge pyqt=6.4
conda install pandas numpy openpyxl

# Install development tools
pip install pytest pytest-qt black isort flake8

# Install documentation tools
pip install mkdocs mkdocs-material

# Install packaging tools
pip install poetry pyinstaller

# Verify installation
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 installed successfully')"
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest
```

### Package Management

#### Poetry

Poetry is the recommended tool for dependency management in this project.

```bash
# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update all dependencies
poetry update

# Update a specific dependency
poetry update package-name

# Export dependencies to requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

#### Requirements.txt

The `requirements.txt` file is maintained for compatibility with traditional pip-based workflows and conda environments.

```bash
# Update requirements.txt from current environment
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt
```

#### Setuptools

The project uses `setup.py` for packaging and distribution.

```bash
# Install the package in development mode
pip install -e .

# Build distribution packages
python setup.py sdist bdist_wheel

# Install from the built package
pip install dist/bosques_app-0.1.0-py3-none-any.whl
```

## Project Structure

```
bosques-app/
├── README.md                  # Project overview and instructions
├── requirements.txt           # Project dependencies
├── setup.py                   # Packaging and distribution configuration
├── pyproject.toml             # Poetry configuration
├── mkdocs.yml                 # MkDocs configuration
├── .gitignore                 # Files/folders to exclude from version control
├── .vscode/                   # VS Code configuration
├── data/                      # Data files
│   ├── Datos ESFP_2019-2024.xlsx
│   └── Datos_REDD_CARM_2024.xlsx
├── docs/                      # Documentation
│   ├── api/                   # API documentation
│   ├── assets/                # Documentation assets
│   ├── codebase/              # Codebase documentation
│   ├── en/                    # English documentation
│   └── es/                    # Spanish documentation
├── out/                       # Output directory
├── site/                      # Generated documentation site
├── src/                       # Source code
│   ├── main.py                # Application entry point
│   └── bosques_app/           # Main application package
│       ├── __init__.py
│       ├── app.py             # Application initialization and main loop
│       ├── config/            # Configuration files
│       ├── controllers/       # Controllers that handle interactions
│       ├── logs/              # Application logs
│       ├── models/            # Data models and business logic
│       ├── resources/         # Static resources (images, icons, styles)
│       ├── sample_data/       # Sample data for testing
│       ├── ui/                # UI design files and generated code
│       ├── utils/             # Utility functions and classes
│       └── views/             # Custom widget implementations
└── tests/                     # Unit and integration tests
```

## Documentation

This project uses [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/) for documentation.

### Working with MkDocs

```bash
# Start the live-reloading docs server
mkdocs serve

# Build the documentation site
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy --force
```

### Documentation Structure

Documentation is organized in the `docs/` directory:

```
docs/
├── index.md              # Home page
├── user-guide/           # User documentation
│   ├── installation.md
│   ├── getting-started.md
│   └── ...
├── developer-guide/      # Developer documentation
│   ├── architecture.md
│   ├── contributing.md
│   └── ...
└── api/                  # API documentation
    ├── models.md
    ├── controllers.md
    └── ...
```

## Creating an Executable

### Using PyInstaller (Recommended)

[PyInstaller](https://pyinstaller.org/) can bundle the application into a standalone executable:

```bash
# Install PyInstaller
conda activate qt6_dev_env
pip install pyinstaller

# Create a spec file
pyi-makespec --name bosques-app --windowed src/main.py

# Build using the spec file (after customizing it if needed)
pyinstaller bosques-app.spec
```

The executable will be created in the `dist/` directory.

### Alternative Methods

Other packaging options include:

- **cx_Freeze**: 
  ```bash
  pip install cx_Freeze
  python setup.py build
  ```

- **Nuitka**: 
  ```bash
  pip install nuitka
  python -m nuitka --follow-imports --standalone --enable-plugin=pyqt6 --windows-disable-console src/main.py
  ```

- **Briefcase** (part of BeeWare): 
  ```bash
  pip install briefcase
  briefcase create
  briefcase build
  briefcase package
  ```

Each method has different trade-offs in terms of executable size, performance, and complexity. PyInstaller is recommended for its balance of simplicity and functionality.

## License

[License information]
