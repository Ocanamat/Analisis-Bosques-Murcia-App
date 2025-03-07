---
tags:
  - data-management
  - excel-file-loading-and-processing
  - pandas-data-frames-storage
  - software-development
  - ui-events-handling
---


> [!INFO]
> In essence:
> 
> - The UI events are handled by the Controller
> - The actual data loading and storage is handled by the Model
> - The data is stored as pandas **DataFrames** in a dictionary
> - The View is updated through the logger and status bar


1. **User Action**:
    
    - User clicks the "Load" button in the UI
2. **Controller Layer** (`MainController._on_load_button_clicked`):
    
    - Opens a QFileDialog to let user select an Excel file
    - Logs "Loading Excel file..." using loguru
    - Calls `data_model.load_excel(filename)`
    - Updates UI based on result:
        - Success: Shows styled message in status bar + logs summary
        - Error: Clears status bar + logs error
3. **Model Layer** (`DataModel.load_excel`):
    
    - Creates a pandas ExcelFile object
    - Gets list of sheet names
    - Reads all sheets into pandas DataFrames
    - Stores data in the model's attributes:
	```python
    self.data: Dict[str, pd.DataFrame] = {}  # Key: sheet name, Value: DataFrame
	self.filename: str = filename
	self.sheet_names: List[str] = excel_file.sheet_names
	```
    - Calls `get_summary()` to generate a detailed summary
    - Returns (True, summary) on success or (False, error_message) on failure
1. **Data Storage**: The data is held in the `DataModel` class in three main attributes:
    
    - `self.data`: A dictionary where:
        - Keys are sheet names (strings)
        - Values are pandas DataFrames containing the sheet data
    - `self.filename`: The path to the loaded Excel file
    - `self.sheet_names`: List of sheet names in the file
2. **Summary Generation** (`DataModel.get_summary`): For each sheet, collects and formats:
    
    - Number of rows and columns
    - For each column:
        - Data type
        - Number of unique values
        - Number of null values
