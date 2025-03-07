from loguru import logger
import os
import sys
from datetime import datetime
from typing import Optional, Union, Dict, Any
from PyQt6.QtWidgets import QTextEdit, QPlainTextEdit

# Global variables to track logger state
_text_edit_widget = None
_logger_initialized = False

# Create a function to intercept all warnings and redirect them to the logger
def _redirect_warnings():
    import warnings
    
    def warning_to_logger(message, category, filename, lineno, *args, **kwargs):
        # Extract module name from filename for consistent logging
        module_name = os.path.basename(filename).split('.')[0]
        logger.bind(module=module_name).warning(f"{category.__name__}: {message} (in {filename}:{lineno})")
    
    # Replace the warnings.showwarning function
    warnings.showwarning = warning_to_logger

# Initialize warning redirection
_redirect_warnings()

class QtTextEditSink:
    """Custom sink to redirect logs to QTextEdit or QPlainTextEdit widget"""
    def __init__(self, text_edit: Union[QTextEdit, QPlainTextEdit], colorize: bool = False):
        self.text_edit = text_edit
        self.colorize = colorize
        self.last_record = None
    
    def write(self, message: str):
        """Write message to text widget"""
        message = message.strip()
        if not message:
            return
            
        # Check if this is a continuation of a multi-line message
        is_continuation = False
        if self.last_record and '|' in self.last_record and '|' not in message:
            # This appears to be a continuation of the previous message
            # Add the prefix from the last record
            prefix = self.last_record.split(' - ')[0] + ' - '
            message = prefix + message
            is_continuation = True
        
        # Store this message as the last record for potential continuation
        if not is_continuation:
            self.last_record = message
        
        if isinstance(self.text_edit, QPlainTextEdit):
            self.text_edit.appendPlainText(message)
            # Scroll to the bottom
            self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
        else:  # QTextEdit
            if self.colorize:
                # Parse the message into components for colorful formatting
                try:
                    # Expected format: "2025-03-06 13:35:35 | INFO     | main_controller - - Columns: codigos, Especies, Unnamed: 2, Unnamed: 3"
                    parts = message.split(' | ', 2)
                    
                    if len(parts) >= 3:
                        timestamp = parts[0]
                        level = parts[1].strip()
                        rest = parts[2]
                        
                        # Split the rest into module and message
                        module_msg = rest.split(' - ', 1)
                        module = module_msg[0].strip()
                        msg = module_msg[1].strip() if len(module_msg) > 1 else ""
                        
                        # Apply colors based on log level
                        level_color = {
                            "INFO": "#3498db",      # Blue
                            "WARNING": "#f39c12",  # Orange
                            "ERROR": "#e74c3c",    # Red
                            "CRITICAL": "#c0392b", # Dark Red
                            "DEBUG": "#2ecc71"     # Green
                        }.get(level.strip(), "#3498db")
                        
                        # Format with different colors for each part
                        html_message = (
                            f'<span style="color: #7f8c8d;">{timestamp}</span> | '
                            f'<span style="color: {level_color}; font-weight: bold;">{level}</span> | '
                            f'<span style="color: #16a085;">{module}</span> - '
                            f'<span style="color: #2c3e50;">{msg}</span>'
                        )
                    else:
                        # Fallback for messages that don't match the expected format
                        html_message = f'<span style="color: #3498db;">{message}</span>'
                except Exception:
                    # If parsing fails, use a simple color based on log level
                    if " | INFO     | " in message:
                        html_message = f'<span style="color: #3498db;">{message}</span>'
                    elif " | WARNING  | " in message:
                        html_message = f'<span style="color: #f39c12;">{message}</span>'
                    elif " | ERROR    | " in message:
                        html_message = f'<span style="color: #e74c3c;">{message}</span>'
                    elif " | CRITICAL | " in message:
                        html_message = f'<span style="color: #c0392b; font-weight: bold;">{message}</span>'
                    elif " | DEBUG    | " in message:
                        html_message = f'<span style="color: #2ecc71;">{message}</span>'
                    else:
                        html_message = message
                
                self.text_edit.append(html_message)
            else:
                self.text_edit.append(message)
            
            # Scroll to the bottom
            self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
    
    def flush(self):
        """Flush is required for file-like objects"""
        pass

# Track logger instances to avoid duplicates
_logger_instances = {}

class Logger:
    """Application logger with enhanced formatting and features using loguru"""
    
    @classmethod
    def get_instance(cls, name: str = "bosques_app", text_edit: Optional[Union[QTextEdit, QPlainTextEdit]] = None):
        """Get or create a logger instance with the given name"""
        global _logger_instances
        
        # Check if we already have a logger instance for this name
        if name in _logger_instances and text_edit is None:
            return _logger_instances[name]
        
        # Create a new instance if it doesn't exist
        instance = cls(name, text_edit, _is_new_instance=True)
        _logger_instances[name] = instance
        return instance
    
    def __init__(self, name: str = "bosques_app", text_edit: Optional[Union[QTextEdit, QPlainTextEdit]] = None, _is_new_instance: bool = False):
        global _text_edit_widget, _logger_initialized
        
        # Store the text edit widget globally
        if text_edit is not None:
            _text_edit_widget = text_edit
        
        # Only initialize the core logger once
        if not _logger_initialized:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            # Log file path with date
            log_file = os.path.join(logs_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
            
            # Remove default handler
            logger.remove()
            
            # Add custom handlers with enhanced formatting
            
            # Console handler - Colorful output for better readability
            logger.add(
                sys.stderr,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[module]}</cyan> - <level>{message}</level>",
                level="INFO",
                colorize=True,
                enqueue=True,  # Enable thread-safe logging
                backtrace=True,  # Show traceback for errors
                diagnose=True    # Enable exception diagnosis
            )
            
            # File handler - Detailed logging with context
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}",
                level="DEBUG",
                rotation="1 day",    # Rotate logs daily
                retention="30 days", # Keep logs for 30 days
                compression="zip",   # Compress rotated logs
                enqueue=True,        # Enable thread-safe logging
                backtrace=True,      # Show traceback for errors
                diagnose=True        # Enable exception diagnosis
            )
            
            _logger_initialized = True
        
        # Add QTextEdit sink if provided
        if text_edit is not None:
            # Check if we can use HTML formatting (QTextEdit)
            use_html = isinstance(text_edit, QTextEdit)
            
            # Remove any existing text edit sinks to avoid duplicates
            for handler_id, handler in list(logger._core.handlers.items()):
                if hasattr(handler, '_sink') and hasattr(handler._sink, '__self__') and \
                   hasattr(handler._sink.__self__, 'write') and 'QtTextEditSink' in str(handler._sink.__self__.__class__):
                    logger.remove(handler_id)
            
            # Format for QTextEdit - with colors if supported
            logger.add(
                QtTextEditSink(text_edit, colorize=use_html).write,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} - {message}",
                level="INFO",
                colorize=False,  # We'll handle colorization ourselves
                catch=True,      # Catch exceptions to prevent logging failures
                enqueue=True,    # Enable thread-safe logging
                backtrace=True,  # Show traceback for errors
                diagnose=True    # Enable exception diagnosis
            )
        
        # Store the module name for this logger instance
        self.name = name
        
        # Get the caller's module name using stack inspection
        import inspect
        frame = inspect.currentframe().f_back
        if frame and inspect.getmodule(frame):
            # Get the full module name and extract just the last part
            full_module_name = inspect.getmodule(frame).__name__
            # Extract just the last part of the module name (after the last dot)
            module_name = full_module_name.split('.')[-1]
        else:
            module_name = name
        
        # Bind the module name to all log messages
        self.logger = logger.bind(module=module_name)
    
    def debug(self, msg: str) -> None:
        """Log debug message with context"""
        # Get the caller's module name using stack inspection
        import inspect
        frame = inspect.currentframe().f_back
        
        if frame and inspect.getmodule(frame):
            # Get the full module name and extract just the last part
            full_module_name = inspect.getmodule(frame).__name__
            # Extract just the last part of the module name (after the last dot)
            module_name = full_module_name.split('.')[-1]
        else:
            module_name = self.name
            
        caller_logger = logger.bind(module=module_name)
        
        # Split multi-line messages and log each line separately
        if '\n' in msg:
            for line in msg.split('\n'):
                if line.strip():  # Skip empty lines
                    caller_logger.debug(line)
        else:
            caller_logger.debug(msg)
    
    def info(self, msg: str) -> None:
        """Log info message with context"""
        # Get the caller's module name using stack inspection
        import inspect
        frame = inspect.currentframe().f_back
        
        if frame and inspect.getmodule(frame):
            # Get the full module name and extract just the last part
            full_module_name = inspect.getmodule(frame).__name__
            # Extract just the last part of the module name (after the last dot)
            module_name = full_module_name.split('.')[-1]
        else:
            module_name = self.name
            
        caller_logger = logger.bind(module=module_name)
        
        # Split multi-line messages and log each line separately
        if '\n' in msg:
            for line in msg.split('\n'):
                if line.strip():  # Skip empty lines
                    caller_logger.info(line)
        else:
            caller_logger.info(msg)
    
    def warning(self, msg: str) -> None:
        """Log warning message with context"""
        # Get the caller's module name using stack inspection
        import inspect
        frame = inspect.currentframe().f_back
        
        if frame and inspect.getmodule(frame):
            # Get the full module name and extract just the last part
            full_module_name = inspect.getmodule(frame).__name__
            # Extract just the last part of the module name (after the last dot)
            module_name = full_module_name.split('.')[-1]
        else:
            module_name = self.name
            
        caller_logger = logger.bind(module=module_name)
        
        # Split multi-line messages and log each line separately
        if '\n' in msg:
            for line in msg.split('\n'):
                if line.strip():  # Skip empty lines
                    caller_logger.warning(line)
        else:
            caller_logger.warning(msg)
    
    def error(self, msg: str) -> None:
        """Log error message with context"""
        # Get the caller's module name using stack inspection
        import inspect
        frame = inspect.currentframe().f_back
        
        if frame and inspect.getmodule(frame):
            # Get the full module name and extract just the last part
            full_module_name = inspect.getmodule(frame).__name__
            # Extract just the last part of the module name (after the last dot)
            module_name = full_module_name.split('.')[-1]
        else:
            module_name = self.name
            
        caller_logger = logger.bind(module=module_name)
        
        # Split multi-line messages and log each line separately
        if '\n' in msg:
            for line in msg.split('\n'):
                if line.strip():  # Skip empty lines
                    caller_logger.error(line)
        else:
            caller_logger.error(msg)
    
    def critical(self, msg: str) -> None:
        """Log critical message with context"""
        # Get the caller's module name using stack inspection
        import inspect
        frame = inspect.currentframe().f_back
        
        if frame and inspect.getmodule(frame):
            # Get the full module name and extract just the last part
            full_module_name = inspect.getmodule(frame).__name__
            # Extract just the last part of the module name (after the last dot)
            module_name = full_module_name.split('.')[-1]
        else:
            module_name = self.name
            
        caller_logger = logger.bind(module=module_name)
        
        # Split multi-line messages and log each line separately
        if '\n' in msg:
            for line in msg.split('\n'):
                if line.strip():  # Skip empty lines
                    caller_logger.critical(line)
        else:
            caller_logger.critical(msg)
    
    def exception(self, msg: str) -> None:
        """Log exception with full traceback"""
        # Get the caller's module name using stack inspection
        import inspect
        frame = inspect.currentframe().f_back
        
        if frame and inspect.getmodule(frame):
            # Get the full module name and extract just the last part
            full_module_name = inspect.getmodule(frame).__name__
            # Extract just the last part of the module name (after the last dot)
            module_name = full_module_name.split('.')[-1]
        else:
            module_name = self.name
            
        caller_logger = logger.bind(module=module_name)
        
        caller_logger.exception(msg)