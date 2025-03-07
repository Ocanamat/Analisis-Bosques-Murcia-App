import os
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import tempfile
from ..utils.logging import Logger

class MapModel:
    """Model for handling map operations and data visualization"""
    
    def __init__(self):
        """Initialize the map model"""
        self.logger = Logger(__name__)
        self.stations_df = None
        self.map = None
        self.temp_html = None
        
        # Load stations data
        self._load_stations_data()
        
    def _load_stations_data(self):
        """Load stations data from CSV file"""
        try:
            stations_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 
                'stations.csv'
            )
            
            if os.path.exists(stations_path):
                self.stations_df = pd.read_csv(stations_path)
                self.logger.info(f"Loaded {len(self.stations_df)} stations from {stations_path}")
            else:
                self.logger.warning(f"Stations file not found: {stations_path}")
                self.stations_df = pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error loading stations data: {str(e)}")
            self.stations_df = pd.DataFrame()
    
    def create_map(self, center=None):
        """Create a Folium map centered at the specified location
        
        Args:
            center: Tuple of (latitude, longitude) for map center. If None, uses the center of all stations.
        
        Returns:
            Path to the HTML file containing the map
        """
        # If no stations data, return None
        if self.stations_df.empty:
            self.logger.warning("No stations data available to create map")
            return None
            
        # Determine map center if not provided
        if center is None:
            center = [
                self.stations_df['latitude'].mean(),
                self.stations_df['longitude'].mean()
            ]
            
        # Create a map
        self.map = folium.Map(
            location=center,
            zoom_start=9,
            tiles='OpenStreetMap'
        )
        
        # Add a marker cluster
        marker_cluster = MarkerCluster().add_to(self.map)
        
        # Add markers for each station
        for _, station in self.stations_df.iterrows():
            # Create popup content
            popup_content = f"""
            <div style="width: 200px">
                <b>{station['name']}</b><br>
                ID: {station['station_id']}<br>
                Elevation: {station['elevation']} m<br>
                Type: {station['type']}<br>
                Region: {station['region']}
            </div>
            """
            
            # Add marker to cluster
            folium.Marker(
                location=[station['latitude'], station['longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=station['name'],
                icon=folium.Icon(color='green', icon='tree', prefix='fa')
            ).add_to(marker_cluster)
        
        # Add layer control
        folium.LayerControl().add_to(self.map)
        
        # Save to temporary file
        fd, self.temp_html = tempfile.mkstemp(suffix='.html')
        os.close(fd)  # Close file descriptor
        
        self.map.save(self.temp_html)
        self.logger.info(f"Map saved to temporary file: {self.temp_html}")
        
        return self.temp_html
    
    def get_map_html(self):
        """Get the HTML content of the map
        
        Returns:
            HTML content as string
        """
        if self.map is None:
            self.create_map()
            
        if self.temp_html and os.path.exists(self.temp_html):
            with open(self.temp_html, 'r', encoding='utf-8') as f:
                return f.read()
        
        return "<html><body><h1>Map not available</h1></body></html>"
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_html and os.path.exists(self.temp_html):
            try:
                os.remove(self.temp_html)
                self.logger.info(f"Removed temporary file: {self.temp_html}")
            except Exception as e:
                self.logger.error(f"Error removing temporary file: {str(e)}")
