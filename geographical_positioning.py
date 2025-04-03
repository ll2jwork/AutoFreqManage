#!/usr/bin/env python3
"""
Geographical Positioning Module for NYC Mesh Frequency Management Tool
This module provides map-based visualization of device locations and interference zones.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import folium
from folium.plugins import MarkerCluster, HeatMap
import math
import geopy.distance

from frequency_database import FrequencyDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('geographical_positioning')

class GeoPositioningVisualizer:
    """Visualizes geographical positioning of devices and interference zones"""
    
    def __init__(self, database: FrequencyDatabase):
        """
        Initialize the geographical positioning visualizer
        
        Args:
            database: Initialized frequency database
        """
        self.database = database
    
    def create_device_map(self, output_file: Optional[str] = None) -> folium.Map:
        """
        Create a map of device locations
        
        Args:
            output_file: Optional file path to save the map
            
        Returns:
            Folium map object
        """
        # Get data from database
        sites = self.database.get_sites()
        devices = self.database.get_devices()
        wireless_configs = self.database.get_wireless_configs()
        
        # Create device lookup
        device_map = {}
        for device in devices:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = device
        
        # Create wireless config lookup
        wireless_map = {}
        for config in wireless_configs:
            device_id = config.get('deviceId')
            if device_id:
                wireless_map[device_id] = config
        
        # Filter sites with valid coordinates
        valid_sites = []
        for site in sites:
            lat = site.get('latitude')
            lon = site.get('longitude')
            if lat is not None and lon is not None:
                valid_sites.append(site)
        
        if not valid_sites:
            logger.warning("No sites with valid coordinates found")
            # Create empty map centered on NYC
            m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
            
            if output_file:
                m.save(output_file)
                logger.info(f"Empty map saved to {output_file}")
            
            return m
        
        # Calculate map center
        lats = [site.get('latitude') for site in valid_sites]
        lons = [site.get('longitude') for site in valid_sites]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Create marker cluster for devices
        marker_cluster = MarkerCluster().add_to(m)
        
        # Add sites and their devices to map
        for site in valid_sites:
            site_id = site.get('id')
            site_name = site.get('name', 'Unknown Site')
            lat = site.get('latitude')
            lon = site.get('longitude')
            
            # Get devices for this site
            site_devices = []
            for device in devices:
                if device.get('siteId') == site_id:
                    site_devices.append(device)
            
            # Create site marker
            site_popup = f"""
            <b>{site_name}</b><br>
            Latitude: {lat}<br>
            Longitude: {lon}<br>
            Devices: {len(site_devices)}
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=site_popup,
                tooltip=site_name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(marker_cluster)
            
            # Add device markers
            for device in site_devices:
                device_id = device.get('id')
                device_name = device.get('name', 'Unknown Device')
                device_model = device.get('model', 'Unknown Model')
                device_type = device.get('type', 'Unknown Type')
                
                # Get wireless config for this device
                wireless_config = wireless_map.get(device_id, {})
                frequency = wireless_config.get('frequency')
                channel_width = wireless_config.get('channelWidth')
                
                # Create device popup
                device_popup = f"""
                <b>{device_name}</b><br>
                Model: {device_model}<br>
                Type: {device_type}<br>
                """
                
                if frequency and channel_width:
                    freq_min = frequency - (channel_width / 2)
                    freq_max = frequency + (channel_width / 2)
                    device_popup += f"""
                    Frequency: {frequency} MHz<br>
                    Channel Width: {channel_width} MHz<br>
                    Range: {freq_min} - {freq_max} MHz
                    """
                
                # Slightly offset device markers from site location
                device_lat = lat + (0.0001 * (hash(device_id) % 10))
                device_lon = lon + (0.0001 * (hash(device_id[::-1]) % 10))
                
                # Determine icon color based on device type
                icon_color = 'green'
                if device_type == 'ap':
                    icon_color = 'red'
                elif device_type == 'station':
                    icon_color = 'orange'
                
                folium.Marker(
                    location=[device_lat, device_lon],
                    popup=device_popup,
                    tooltip=device_name,
                    icon=folium.Icon(color=icon_color, icon='signal')
                ).add_to(marker_cluster)
        
        # Save to file if specified
        if output_file:
            m.save(output_file)
            logger.info(f"Device map saved to {output_file}")
        
        return m
    
    def create_sector_coverage_map(self, output_file: Optional[str] = None) -> folium.Map:
        """
        Create a map showing sector coverage patterns
        
        Args:
            output_file: Optional file path to save the map
            
        Returns:
            Folium map object
        """
        # Get data from database
        sites = self.database.get_sites()
        devices = self.database.get_devices()
        wireless_configs = self.database.get_wireless_configs()
        
        # Create device lookup
        device_map = {}
        for device in devices:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = device
        
        # Create wireless config lookup
        wireless_map = {}
        for config in wireless_configs:
            device_id = config.get('deviceId')
            if device_id:
                wireless_map[device_id] = config
        
        # Filter sites with valid coordinates
        valid_sites = []
        for site in sites:
            lat = site.get('latitude')
            lon = site.get('longitude')
            if lat is not None and lon is not None:
                valid_sites.append(site)
        
        if not valid_sites:
            logger.warning("No sites with valid coordinates found")
            # Create empty map centered on NYC
            m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
            
            if output_file:
                m.save(output_file)
                logger.info(f"Empty map saved to {output_file}")
            
            return m
        
        # Calculate map center
        lats = [site.get('latitude') for site in valid_sites]
        lons = [site.get('longitude') for site in valid_sites]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add sites and sector coverage to map
        for site in valid_sites:
            site_id = site.get('id')
            site_name = site.get('name', 'Unknown Site')
            lat = site.get('latitude')
            lon = site.get('longitude')
            
            # Get devices for this site
            site_devices = []
            for device in devices:
                if device.get('siteId') == site_id:
                    site_devices.append(device)
            
            # Create site marker
            site_popup = f"""
            <b>{site_name}</b><br>
            Latitude: {lat}<br>
            Longitude: {lon}<br>
            Devices: {len(site_devices)}
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=site_popup,
                tooltip=site_name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
            # Add sector coverage for AP devices
            for device in site_devices:
                device_id = device.get('id')
                device_name = device.get('name', 'Unknown Device')
                device_type = device.get('type', 'Unknown Type')
                
                # Only show coverage for AP devices
                if device_type != 'ap':
                    continue
                
                # Get wireless config for this device
                wireless_config = wireless_map.get(device_id, {})
                frequency = wireless_config.get('frequency')
                
                if not frequency:
                    continue
                
                # Determine coverage radius based on frequency
                # Lower frequencies have better range
                if frequency < 5500:
                    radius = 500  # meters
                else:
                    radius = 300  # meters
                
                # Determine sector direction and width
                # This is a simplification - in reality would need actual antenna data
                # Extract direction from device name if possible (e.g., "north", "south", etc.)
                direction = None
                sector_width = 90  # degrees
                
                name_lower = device_name.lower()
                if 'north' in name_lower:
                    direction = 0
                elif 'east' in name_lower:
                    direction = 90
                elif 'south' in name_lower:
                    direction = 180
                elif 'west' in name_lower:
                    direction = 270
                
                # If direction couldn't be determined, use a full circle
                if direction is None:
                    # Create a circle for omnidirectional coverage
                    folium.Circle(
                        location=[lat, lon],
                        radius=radius,
                        popup=f"{device_name} coverage",
                        color='red',
                        fill=True,
                        fill_opacity=0.2
                    ).add_to(m)
                else:
                    # Create a sector for directional coverage
                    self._add_sector_to_map(
                        m, lat, lon, radius, direction, sector_width, 
                        device_name, frequency
                    )
        
        # Save to file if specified
        if output_file:
            m.save(output_file)
            logger.info(f"Sector coverage map saved to {output_file}")
        
        return m
    
    def _add_sector_to_map(self, m, lat, lon, radius, direction, width, name, frequency):
        """
        Add a sector coverage pattern to the map
        
        Args:
            m: Folium map object
            lat: Latitude of the sector center
            lon: Longitude of the sector center
            radius: Radius of the sector in meters
            direction: Direction of the sector in degrees (0 = North, 90 = East, etc.)
            width: Width of the sector in degrees
            name: Name of the device
            frequency: Frequency of the device
        """
        # Calculate start and end angles
        start_angle = (direction - (width / 2)) % 360
        end_angle = (direction + (width / 2)) % 360
        
        # Generate points for the sector
        points = []
        
        # Add center point
        points.append((lat, lon))
        
        # Add arc points
        num_points = 20
        for i in range(num_points + 1):
            angle_rad = math.radians(start_angle + (i * (width / num_points)))
            # Calculate point at given angle and distance
            point = geopy.distance.distance(meters=radius).destination(
                (lat, lon), bearing=angle_rad
            )
            points.append((point.latitude, point.longitude))
        
        # Add center point again to close the polygon
        points.append((lat, lon))
        
        # Create sector polygon
        folium.Polygon(
            locations=points,
            popup=f"{name} ({frequency} MHz)",
            color='red',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
    
    def create_interference_zone_map(self, output_file: Optional[str] = None) -> folium.Map:
        """
        Create a map showing potential interference zones
        
        Args:
            output_file: Optional file path to save the map
            
        Returns:
            Folium map object
        """
        # Get data from database
        sites = self.database.get_sites()
        devices = self.database.get_devices()
        wireless_configs = self.database.get_wireless_configs()
        conflicts = self.database.get_frequency_conflicts()
        
        # Create device lookup
        device_map = {}
        for device in devices:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = device
        
        # Create wireless config lookup
        wireless_map = {}
        for config in wireless_configs:
            device_id = config.get('deviceId')
            if device_id:
                wireless_map[device_id] = config
        
        # Filter sites with valid coordinates
        valid_sites = []
        for site in sites:
            lat = site.get('latitude')
            lon = site.get('longitude')
            if lat is not None and lon is not None:
                valid_sites.append(site)
        
        if not valid_sites:
            logger.warning("No sites with valid coordinates found")
            # Create empty map centered on NYC
            m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
            
            if output_file:
                m.save(output_file)
                logger.info(f"Empty map saved to {output_file}")
            
            return m
        
        # Calculate map center
        lats = [site.get('latitude') for site in valid_sites]
        lons = [site.get('longitude') for site in valid_sites]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Create site lookup
        site_map = {}
        for site in valid_sites:
            site_id = site.get('id')
            if site_id:
                site_map[site_id] = site
        
        # Add sites to map
        for site in valid_sites:
            site_id = site.get('id')
            site_name = site.get('name', 'Unknown Site')
            lat = site.get('latitude')
            lon = site.get('longitude')
            
            # Create site marker
            folium.Marker(
                location=[lat, lon],
                popup=site_name,
                tooltip=site_name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        
        # Add interference zones for conflicting devices
        for conflict in conflicts:
            device1_id = conflict['device1']['id']
            device2_id = conflict['device2']['id']
            
            # Get site information for both devices
            device1 = device_map.get(device1_id, {})
            device2 = device_map.get(device2_id, {})
            
            site1_id = device1.get('siteId')
            site2_id = device2.get('siteId')
            
            site1 = site_map.get(site1_id, {})
            site2 = site_map.get(site2_id, {})
            
            # Skip if either site doesn't have valid coordinates
            if not site1 or not site2:
                continue
                
            lat1 = site1.get('latitude')
            lon1 = site1.get('longitude')
            lat2 = site2.get('latitude')
            lon2 = site2.get('longitude')
            
            if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
                continue
            
            # Calculate midpoint between sites
            mid_lat = (lat1 + lat2) / 2
            mid_lon = (lon1 + lon2) / 2
            
            # Calculate distance between sites
            distance = geopy.distance.distance((lat1, lon1), (lat2, lon2)).meters
            
            # Create interference zone (circle at midpoint)
            folium.Circle(
                location=[mid_lat, mid_lon],
                radius=distance / 2,  # Use half the distance as radius
                popup=f"Potential interference zone between {device1.get('name')} and {device2.get('name')}",
                color='red',
                fill=True,
                fill_opacity=0.3
            ).add_to(m)
            
            # Draw line between conflicting sites
            folium.PolyLine(
                locations=[(lat1, lon1), (lat2, lon2)],
                color='red',
                weight=2,
                opacity=0.7,
                popup=f"Conflict: {device1.get('name')} and {device2.get('name')} at {conflict['frequency']} MHz"
            ).add_to(m)
        
        # Save to file if specified
        if output_file:
            m.save(output_file)
            logger.info(f"Interference zone map saved to {output_file}")
        
        return m
    
    def create_frequency_heatmap(self, output_file: Optional[str] = None) -> folium.Map:
        """
        Create a heatmap of frequency usage
        
        Args:
            output_file: Optional file path to save the map
            
        Returns:
            Folium map object
        """
        # Get data from database
        sites = self.database.get_sites()
        devices = self.database.get_devices()
        wireless_configs = self.database.get_wireless_configs()
        
        # Create device lookup
        device_map = {}
        for device in devices:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = device
        
        # Create wireless config lookup
        wireless_map = {}
        for config in wireless_configs:
            device_id = config.get('deviceId')
            if device_id:
                wireless_map[device_id] = config
        
        # Filter sites with valid coordinates
        valid_sites = []
        for site in sites:
            lat = site.get('latitude')
            lon = site.get('longitude')
            if lat is not None and lon is not None:
                valid_sites.append(site)
        
        if not valid_sites:
            logger.warning("No sites with valid coordinates found")
            # Create empty map centered on NYC
            m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
            
            if output_file:
                m.save(output_file)
                logger.info(f"Empty map saved to {output_file}")
            
            return m
        
        # Calculate map center
        lats = [site.get('latitude') for site in valid_sites]
        lons = [site.get('longitude') for site in valid_sites]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Prepare heatmap data
        heatmap_data = []
        
        # Group devices by frequency
        frequency_groups = {}
        
        for device in devices:
            device_id = device.get('id')
            site_id = device.get('siteId')
            
            if not device_id or not site_id:
                continue
            
            # Get site information
            site = None
            for s in valid_sites:
                if s.get('id') == site_id:
                    site = s
                    break
            
            if not site:
                continue
            
            # Get wireless config
            wireless_config = wireless_map.get(device_id)
            if not wireless_config:
                continue
            
            frequency = wireless_config.get('frequency')
            if not frequency:
                continue
            
            # Round frequency to nearest 5 MHz for grouping
            rounded_freq = round(frequency / 5) * 5
            
            if rounded_freq not in frequency_groups:
                frequency_groups[rounded_freq] = []
            
            lat = site.get('latitude')
            lon = site.get('longitude')
            
            if lat is not None and lon is not None:
                frequency_groups[rounded_freq].append((lat, lon))
        
        # Create a separate heatmap layer for each frequency group
        for frequency, points in frequency_groups.items():
            if not points:
                continue
            
            # Add points to heatmap data with weight based on frequency
            # Higher frequencies get higher weight (arbitrary choice for visualization)
            weight = (frequency - 5000) / 1000  # Normalize to 0-1 range for 5GHz band
            weight = max(0.1, min(1.0, weight))  # Clamp to 0.1-1.0 range
            
            weighted_points = [[lat, lon, weight] for lat, lon in points]
            
            # Create heatmap layer
            heatmap = HeatMap(
                weighted_points,
                name=f"{frequency} MHz",
                radius=15,
                blur=10,
                gradient={0.4: 'blue', 0.65: 'lime', 0.8: 'yellow', 1.0: 'red'}
            )
            
            # Add to map
            heatmap.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save to file if specified
        if output_file:
            m.save(output_file)
            logger.info(f"Frequency heatmap saved to {output_file}")
        
        return m


class GeoDashboard:
    """Interactive dashboard for geographical positioning visualization"""
    
    def __init__(self, database: FrequencyDatabase):
        """
        Initialize the geographical dashboard
        
        Args:
            database: Initialized frequency database
        """
        self.database = database
        self.visualizer = GeoPositioningVisualizer(database)
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            title="NYC Mesh Geographical Positioning"
        )
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Set up the dashboard layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("NYC Mesh Geographical Positioning", className="text-center my-4"),
                    html.P(
                        "Interactive visualization of device locations and interference zones",
                        className="text-center lead mb-4"
                    )
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Map Controls"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Map Type"),
                                    dcc.Dropdown(
                                        id="map-type",
                                        options=[
                                            {"label": "Device Locations", "value": "devices"},
                                            {"label": "Sector Coverage", "value": "sectors"},
                                            {"label": "Interference Zones", "value": "interference"},
                                            {"label": "Frequency Heatmap", "value": "heatmap"}
                                        ],
                                        value="devices"
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label("Actions"),
                                    dbc.Button(
                                        "Generate Map",
                                        id="generate-map-button",
                                        color="primary",
                                        className="me-2"
                                    ),
                                    dbc.Button(
                                        "Export Map",
                                        id="export-map-button",
                                        color="secondary"
                                    )
                                ], width=6)
                            ])
                        ])
                    ], className="mb-4")
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Map Visualization"),
                        dbc.CardBody([
                            html.Iframe(
                                id="map-iframe",
                                style={"width": "100%", "height": "600px", "border": "none"}
                            )
                        ])
                    ])
                ])
            ]),
            
            dbc.Modal([
                dbc.ModalHeader("Export Map"),
                dbc.ModalBody([
                    dbc.Input(
                        id="export-filename",
                        placeholder="Enter filename",
                        type="text",
                        value="nyc_mesh_map.html"
                    )
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Cancel",
                        id="export-cancel",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Export",
                        id="export-confirm",
                        color="primary"
                    )
                ])
            ], id="export-modal"),
            
            html.Footer([
                html.P(
                    "NYC Mesh Geographical Positioning Tool",
                    className="text-center text-muted my-4"
                )
            ])
        ], fluid=True)
    
    def _setup_callbacks(self):
        """Set up the dashboard callbacks"""
        
        @self.app.callback(
            Output("map-iframe", "src"),
            Input("generate-map-button", "n_clicks"),
            State("map-type", "value")
        )
        def generate_map(n_clicks, map_type):
            """Generate map based on selected type"""
            if n_clicks is None:
                # Default map on load
                map_file = "device_map.html"
                self.visualizer.create_device_map(output_file=map_file)
                return map_file
            
            if map_type == "devices":
                map_file = "device_map.html"
                self.visualizer.create_device_map(output_file=map_file)
            elif map_type == "sectors":
                map_file = "sector_map.html"
                self.visualizer.create_sector_coverage_map(output_file=map_file)
            elif map_type == "interference":
                map_file = "interference_map.html"
                self.visualizer.create_interference_zone_map(output_file=map_file)
            elif map_type == "heatmap":
                map_file = "heatmap.html"
                self.visualizer.create_frequency_heatmap(output_file=map_file)
            else:
                map_file = "device_map.html"
                self.visualizer.create_device_map(output_file=map_file)
            
            return map_file
        
        @self.app.callback(
            Output("export-modal", "is_open"),
            [
                Input("export-map-button", "n_clicks"),
                Input("export-cancel", "n_clicks"),
                Input("export-confirm", "n_clicks")
            ],
            State("export-modal", "is_open")
        )
        def toggle_export_modal(n_export, n_cancel, n_confirm, is_open):
            """Toggle the export modal"""
            ctx = dash.callback_context
            if not ctx.triggered:
                return is_open
            
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "export-map-button":
                return True
            elif button_id in ["export-cancel", "export-confirm"]:
                return False
            return is_open
        
        @self.app.callback(
            Output("map-iframe", "src", allow_duplicate=True),
            Input("export-confirm", "n_clicks"),
            [
                State("map-type", "value"),
                State("export-filename", "value")
            ],
            prevent_initial_call=True
        )
        def export_map(n_clicks, map_type, filename):
            """Export the current map"""
            if n_clicks is None:
                return dash.no_update
            
            if not filename:
                filename = "nyc_mesh_map.html"
            
            if map_type == "devices":
                self.visualizer.create_device_map(output_file=filename)
            elif map_type == "sectors":
                self.visualizer.create_sector_coverage_map(output_file=filename)
            elif map_type == "interference":
                self.visualizer.create_interference_zone_map(output_file=filename)
            elif map_type == "heatmap":
                self.visualizer.create_frequency_heatmap(output_file=filename)
            
            # Return the current map (no change to display)
            return dash.no_update
    
    def run_server(self, debug=False, port=8050):
        """Run the dashboard server"""
        self.app.run_server(debug=debug, port=port)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NYC Mesh Geographical Positioning')
    parser.add_argument('--db', default='frequency_data.db', help='Database file path')
    parser.add_argument('--output', help='Output directory for maps')
    parser.add_argument('--type', choices=['devices', 'sectors', 'interference', 'heatmap'], 
                        default='devices', help='Map type')
    parser.add_argument('--dashboard', action='store_true', help='Run interactive dashboard')
    parser.add_argument('--port', type=int, default=8050, help='Dashboard port')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        sys.exit(1)
    
    # Initialize database
    database = FrequencyDatabase(args.db)
    
    if args.dashboard:
        # Run interactive dashboard
        dashboard = GeoDashboard(database)
        print(f"Starting dashboard on http://localhost:{args.port}")
        dashboard.run_server(debug=True, port=args.port)
    else:
        # Create output directory if it doesn't exist
        if args.output and not os.path.exists(args.output):
            os.makedirs(args.output)
        
        # Create static map
        visualizer = GeoPositioningVisualizer(database)
        
        if args.type == 'devices':
            output_file = os.path.join(args.output, 'device_map.html') if args.output else None
            visualizer.create_device_map(output_file=output_file)
        elif args.type == 'sectors':
            output_file = os.path.join(args.output, 'sector_map.html') if args.output else None
            visualizer.create_sector_coverage_map(output_file=output_file)
        elif args.type == 'interference':
            output_file = os.path.join(args.output, 'interference_map.html') if args.output else None
            visualizer.create_interference_zone_map(output_file=output_file)
        elif args.type == 'heatmap':
            output_file = os.path.join(args.output, 'heatmap.html') if args.output else None
            visualizer.create_frequency_heatmap(output_file=output_file)
        
        if args.output:
            print(f"Map saved to {output_file}")

if __name__ == "__main__":
    main()
