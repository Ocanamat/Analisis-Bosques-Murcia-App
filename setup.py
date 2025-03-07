# Package configuration will be defined here

from setuptools import setup, find_packages

setup(
    name="bosques-app",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
        "PyQt6-Qt6>=6.4.0",
        "PyQt6-sip>=13.4.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "openpyxl>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-qt>=4.2.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bosques-app=bosques_app.main:main",
        ],
    },
)
