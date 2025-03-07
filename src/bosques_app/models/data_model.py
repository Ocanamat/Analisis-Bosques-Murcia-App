from typing import Dict, Tuple, List, Optional
import pandas as pd
import yaml
import os
from pathlib import Path
from ..utils.logging import Logger

def standardize_date(date_str):
    """Convert all dates to YYYY-MM-DD format"""
    return pd.to_datetime(date_str).strftime('%Y-%m-%d')

def convert_numeric(value):
    """Convert numeric values with comma decimals to float"""
    if pd.isna(value) or value == 'Na':
        return None
    return float(str(value).replace(',', '.'))

class DataModel:
    """Model for handling Excel data operations"""
    
    # Load variable definitions for column mapping
    CONFIG_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent / 'config'
    
    try:
        with open(CONFIG_DIR / 'variables.yaml', 'r', encoding='utf-8') as f:
            _variables_config = yaml.safe_load(f)
    except Exception as e:
        _variables_config = {'variables': []}
        # We'll log this properly once the logger is initialized
    
    def __init__(self):
        self.data: Optional[Dict[str, pd.DataFrame]] = None
        self.filename: Optional[str] = None
        self.sheet_names: Optional[List[str]] = None
        self.unified_df: Optional[pd.DataFrame] = None
        self.logger = Logger.get_instance("data_model")
        
        # Log any config loading errors that happened before logger was initialized
        if self._variables_config == {'variables': []}:
            self.logger.error("Error loading variables config")
        
    def load_excel(self, filename: str) -> Tuple[bool, str]:
        """Load Excel file and store all sheets"""
        try:
            excel_file = pd.ExcelFile(filename)
            self.sheet_names = excel_file.sheet_names
            self.data = pd.read_excel(excel_file, sheet_name=None)
            self.filename = filename
            summary = self.get_summary()
            return True, summary
        except Exception as e:
            return False, f"Error loading Excel file: {str(e)}"

    def transform_temperatures(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform temperature data from wide to long format and aggregate by day"""
        melted = pd.melt(
            df,
            id_vars=['id', 'year', 'nmes', 'mes', 'Fecha', 'Hora'],
            var_name='Estacion',
            value_name='Temperatura'
        )
        melted['Temperatura'] = melted['Temperatura'].apply(convert_numeric)
        melted['Fecha'] = melted['Fecha'].apply(standardize_date)
        
        # Aggregate by day and station
        self.logger.info("Aggregating temperature data by day")
        daily_temps = melted.groupby(['Fecha', 'Estacion']).agg(
            Temp_Min=('Temperatura', 'min'),
            Temp_Max=('Temperatura', 'max'),
            Temp_Mean=('Temperatura', 'mean'),
            Temp_Count=('Temperatura', 'count')
        ).reset_index()
        
        return daily_temps

    def transform_dendrometers(self, df: pd.DataFrame, is_carm: bool = False) -> pd.DataFrame:
        """Transform dendrometer data"""
        df = df.copy()
        station_col = 'CARM' if is_carm else 'Punto'
        df = df.rename(columns={station_col: 'Estacion'})
        df['Diam'] = df['Diam'].apply(convert_numeric)
        df['Fecha'] = df['Fecha'].apply(standardize_date)
        return df

    def transform_desfronde(self, df: pd.DataFrame, is_carm: bool = False) -> pd.DataFrame:
        """Transform desfronde data"""
        df = df.copy()
        station_col = 'CARM' if is_carm else 'Esfp'
        df = df.rename(columns={station_col: 'Estacion'})
        df['MO'] = df['MO'].apply(convert_numeric)
        df['Fecha'] = df['Fecha'].apply(standardize_date)
        return df

    def transform_capturas(self, df: pd.DataFrame, is_carm: bool = False) -> pd.DataFrame:
        """Transform capturas data"""
        df = df.copy()
        station_col = 'CARM' if is_carm else 'Esfp'
        df = df.rename(columns={station_col: 'Estacion'})
        
        # Standardize dates
        df['Fecha'] = df['Fecha'].apply(standardize_date)
        
        # Convert all species columns to numeric and fill NAs
        species_cols = df.columns.difference(['id', 'Year', 'Mes', 'Nmes', 'Fecha', 'Estacion'])
        for col in species_cols:
            df[col] = df[col].apply(convert_numeric)
            df[col] = df[col].fillna(pd.NA)
            
        return df

    def _standardize_join_columns(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """Standardize column names for joining based on variables.yaml configuration"""
        # Find variables that need to be standardized for joining (Fecha and Estacion)
        join_columns = {'Fecha': 'Fecha', 'Estacion': 'Estacion'}
        
        # Look for variables with excel_name that should be standardized
        for var in self._variables_config['variables']:
            if 'excel_name' in var and 'name' in var:
                var_name = var['name']
                excel_name = var['excel_name']
                
                # Only process variables that are used for joining
                if var_name in ['Fecha', 'Estación']:
                    join_column = 'Fecha' if var_name == 'Fecha' else 'Estacion'
                    
                    # Handle excel_name as a list or a single value
                    excel_names = excel_name if isinstance(excel_name, list) else [excel_name]
                    
                    # Check if any of the excel_names are in the dataframe columns
                    for name in excel_names:
                        if name in df.columns and join_column not in df.columns:
                            df = df.rename(columns={name: join_column})
                            self.logger.info(f"Renamed '{name}' to '{join_column}' in {sheet_name}")
                            break
        
        return df
    
    def transform_sheet(self, sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """Transform a sheet based on its type"""
        is_carm = 'CARM' in sheet_name
        
        # Transform based on sheet type
        if 'temperaturas' in sheet_name.lower():
            transformed_df = self.transform_temperatures(df)
        elif 'dendrometros' in sheet_name.lower():
            transformed_df = self.transform_dendrometers(df, is_carm)
        elif 'desfronde' in sheet_name.lower():
            transformed_df = self.transform_desfronde(df, is_carm)
        elif 'capturas' in sheet_name.lower():
            transformed_df = self.transform_capturas(df, is_carm)
        else:
            self.logger.warning(f"Unknown sheet type: {sheet_name}, returning untransformed")
            transformed_df = df
            
        # Standardize column names for joining based on variables.yaml configuration
        transformed_df = self._standardize_join_columns(transformed_df, sheet_name)
            
        return transformed_df

    def _drop_unnecessary_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop unnecessary columns from dataframe"""
        # List of columns to drop (exact matches)
        columns_to_drop = [
            'id', 'year', 'nmes', 'mes', 'Year', 'Mes', 'Nmes',
            'id_ESFP_capturas_trampas_final', 'Year_ESFP_capturas_trampas_final',
            'Mes_ESFP_capturas_trampas_final', 'Nmes_ESFP_capturas_trampas_final',
            'id_ESFP_datos_temperaturas_final', 'Year_ESFP_dendrometros_final',
            'Mes_ESFP_dendrometros_final', 'Nmes_ESFP_dendrometros_final'
        ]
        
        # Drop columns that exist in the dataframe
        cols_to_drop = [col for col in columns_to_drop if col in df.columns]
        if cols_to_drop:
            self.logger.info(f"Dropping columns: {', '.join(cols_to_drop)}")
            df = df.drop(columns=cols_to_drop)
            
        return df

    def _build_column_mapping(self) -> Dict[str, str]:
        """Build mapping dictionary from excel_name to name based on variables.yaml"""
        column_mapping = {}
        
        for var in self._variables_config['variables']:
            if 'excel_name' in var and 'name' in var:
                excel_name = var['excel_name']
                display_name = var['name']
                
                # Handle excel_name as a list or a single value
                if isinstance(excel_name, list):
                    for name in excel_name:
                        column_mapping[name] = display_name
                else:
                    column_mapping[excel_name] = display_name
        
        self.logger.info(f"Built column mapping with {len(column_mapping)} entries")
        return column_mapping
    
    def create_unified_dataframe(self, selected_sheets: List[str]) -> Tuple[bool, str]:
        """Create unified dataframe from selected sheets with standardized format"""
        if not self.data or not selected_sheets:
            return False, "No data loaded or no sheets selected"
            
        try:
            transformed_dfs = {}
            messages = []
            
            # Transform each selected sheet
            for sheet_name in selected_sheets:
                if sheet_name not in self.data:
                    messages.append(f"Sheet {sheet_name} not found in data")
                    continue
                    
                df = self.data[sheet_name]
                transformed_df = self.transform_sheet(sheet_name, df)
                
                # Verify required columns exist
                if 'Fecha' not in transformed_df.columns or 'Estacion' not in transformed_df.columns:
                    messages.append(f"Warning: Sheet {sheet_name} missing required columns (Fecha, Estacion)")
                    continue
                
                # Drop unnecessary columns before joining
                transformed_df = self._drop_unnecessary_columns(transformed_df)
                    
                transformed_dfs[sheet_name] = transformed_df
                messages.append(f"Transformed {sheet_name}")
            
            if not transformed_dfs:
                return False, "No valid sheets to process"
            
            # Start joining with first sheet
            base_sheet = selected_sheets[0]
            self.unified_df = transformed_dfs[base_sheet].copy()
            
            # Join with remaining sheets
            for sheet_name in selected_sheets[1:]:
                if sheet_name not in transformed_dfs:
                    continue
                    
                df = transformed_dfs[sheet_name]
                
                # Perform the join on Fecha and Estacion
                self.unified_df = pd.merge(
                    self.unified_df,
                    df,
                    on=['Fecha', 'Estacion'],
                    how='outer',
                    suffixes=(f'_{base_sheet}', f'_{sheet_name}')
                )
                messages.append(f"Joined sheet {sheet_name} on Fecha and Estacion")
            
            # Drop any unnecessary columns that might have been created during join
            self.unified_df = self._drop_unnecessary_columns(self.unified_df)
            
            # Rename columns based on mapping from excel_name to name
            column_mapping = self._build_column_mapping()
            # Create a mapping dict with only the columns that exist in the dataframe
            actual_mapping = {col: column_mapping[col] for col in self.unified_df.columns 
                             if col in column_mapping}
            
            if actual_mapping:
                self.unified_df = self.unified_df.rename(columns=actual_mapping)
                mapped_cols = ", ".join([f"{old} → {new}" for old, new in actual_mapping.items()])
                messages.append(f"Renamed columns: {mapped_cols}")
            
            # Good place for a breakpoint to inspect self.unified_df
            summary = "\n".join(messages)
            return True, f"Successfully transformed and joined sheets:\n{summary}"
            
        except Exception as e:
            return False, f"Error processing sheets: {str(e)}"

    def get_summary(self) -> str:
        """Get summary of loaded data"""
        if not self.data:
            return "No data loaded"
            
        summary = [f"File: {self.filename}"]
        summary.append(f"Number of sheets: {len(self.sheet_names)}")
        summary.append("\nAvailable sheets:")
        
        for name, df in self.data.items():
            summary.append(f"\n{name}:")
            summary.append(f"- Rows: {df.shape[0]}")
            summary.append(f"- Columns: {df.shape[1]}")
            summary.append(f"- Columns: {', '.join(df.columns)}")
            
        return "\n".join(summary)