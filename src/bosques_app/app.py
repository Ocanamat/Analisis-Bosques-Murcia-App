from PyQt6.QtWidgets import QApplication
from bosques_app.ui.main_window import MainWindow
from bosques_app.models.data_model import DataModel
from bosques_app.controllers.main_controller import MainController
from bosques_app.utils.logging import Logger
import yaml
from pathlib import Path

class Application:
    """Main application class"""
    
    def __init__(self, app):
        # Create views
        self.main_window = MainWindow()
        
        # Initialize logger with QTextEdit widget - this will be the single logger instance for the app
        from bosques_app.utils.logging import logger as loguru_logger
        
        # Clear any existing handlers for QTextEdit to avoid duplicates
        for handler_id, handler in list(loguru_logger._core.handlers.items()):
            if hasattr(handler, '_sink') and hasattr(handler._sink, '__self__') and \
               hasattr(handler._sink.__self__, 'write') and 'QtTextEditSink' in str(handler._sink.__self__.__class__):
                loguru_logger.remove(handler_id)
        
        # Create the single logger instance for the entire application
        self.logger = Logger.get_instance("app", self.main_window.log_textedit)
        
        # Load and display app info
        app_info = self._load_app_info()
        self.logger.info("="*50)
        self.logger.info(f"{app_info['name']} v{app_info['version']}")
        self.logger.info(f"Author: {app_info['author']}")
        self.logger.info(f"{app_info['copyright']}")
        self.logger.info(f"{app_info['description']}")
        self.logger.info(f"License: {app_info['license']}")
        self.logger.info("="*50)
        
        # Create models and pass the logger to them
        self.data_model = DataModel()
        self.data_model.logger = self.logger
        
        # Create controllers
        self.main_controller = MainController(
            view=self.main_window,
            data_model=self.data_model
        )
        
        self.app = app
    
    def _load_app_info(self):
        """Load application information from config file"""
        config_path = Path(__file__).parent / "config" / "app_info.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)['app_info']
    
    def show(self):
        """Show the main window"""
        self.main_window.show()
    
    def run(self):
        """Run the application"""
        return self.app.exec()