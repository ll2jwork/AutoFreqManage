#!/usr/bin/env python3
"""
Frequency Visualization Component for NYC Mesh Frequency Management Tool
This module provides visualization of frequency data using Plotly and Dash.
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

from frequency_database import FrequencyDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('frequency_visualization')

class FrequencyVisualizer:
    """Visualizes frequency data using Plotly"""
    
    def __init__(self, database: FrequencyDatabase):
        """
        Initialize the frequency visualizer
        
        Args:
            database: Initialized frequency database
        """
        self.database = database
    
    def create_frequency_chart(self, output_file: Optional[str] = None) -> go.Figure:
        """
        Create a frequency allocation chart
        
        Args:
            output_file: Optional file path to save the chart
            
        Returns:
            Plotly figure object
        """
        # Get data from database
        wireless_configs = self.database.get_wireless_configs()
        devices = self.database.get_devices()
        
        # Create device lookup
        device_map = {}
        for device in devices:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = device
        
        # Prepare data for visualization
        chart_data = []
        for config in wireless_configs:
            device_id = config.get('deviceId')
            frequency = config.get('frequency')
            channel_width = config.get('channelWidth')
            
            if not device_id or not frequency or not channel_width:
                continue
            
            device = device_map.get(device_id, {})
            device_name = device.get('name', 'Unknown')
            device_type = device.get('type', 'Unknown')
            site_id = device.get('siteId')
            
            # Calculate frequency range
            half_width = channel_width / 2
            freq_min = frequency - half_width
            freq_max = frequency + half_width
            
            chart_data.append({
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type,
                'site_id': site_id,
                'frequency': frequency,
                'channel_width': channel_width,
                'freq_min': freq_min,
                'freq_max': freq_max,
                'ssid': config.get('ssid', '')
            })
        
        if not chart_data:
            logger.warning("No frequency data available for visualization")
            fig = go.Figure()
            fig.add_annotation(
                text="No frequency data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(chart_data)
        
        # Sort by frequency
        df = df.sort_values('frequency')
        
        # Create figure
        fig = go.Figure()
        
        # Add frequency bands for each device
        for _, row in df.iterrows():
            fig.add_trace(go.Bar(
                x=[row['device_name']],
                y=[row['channel_width']],
                base=[row['freq_min']],
                name=f"{row['device_name']} ({row['frequency']} MHz)",
                hovertemplate=(
                    f"<b>{row['device_name']}</b><br>" +
                    f"Frequency: {row['frequency']} MHz<br>" +
                    f"Channel Width: {row['channel_width']} MHz<br>" +
                    f"Range: {row['freq_min']} - {row['freq_max']} MHz<br>" +
                    f"SSID: {row['ssid']}<br>" +
                    f"Device Type: {row['device_type']}"
                )
            ))
        
        # Update layout
        fig.update_layout(
            title="NYC Mesh Frequency Allocation",
            xaxis_title="Device",
            yaxis_title="Frequency (MHz)",
            barmode='overlay',
            bargap=0.25,
            legend_title="Devices",
            height=800,
            margin=dict(l=50, r=50, t=100, b=100)
        )
        
        # Save to file if specified
        if output_file:
            fig.write_html(output_file)
            logger.info(f"Frequency chart saved to {output_file}")
        
        return fig
    
    def create_conflict_matrix(self, output_file: Optional[str] = None) -> go.Figure:
        """
        Create a conflict matrix visualization
        
        Args:
            output_file: Optional file path to save the chart
            
        Returns:
            Plotly figure object
        """
        # Get conflicts from database
        conflicts = self.database.get_frequency_conflicts()
        
        if not conflicts:
            logger.warning("No frequency conflicts found for visualization")
            fig = go.Figure()
            fig.add_annotation(
                text="No frequency conflicts found",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Extract unique devices
        devices = set()
        for conflict in conflicts:
            devices.add(conflict['device1']['name'])
            devices.add(conflict['device2']['name'])
        
        devices = sorted(list(devices))
        n_devices = len(devices)
        
        # Create device index mapping
        device_indices = {device: i for i, device in enumerate(devices)}
        
        # Initialize matrix
        matrix = np.zeros((n_devices, n_devices))
        
        # Fill matrix with conflict data
        for conflict in conflicts:
            i = device_indices[conflict['device1']['name']]
            j = device_indices[conflict['device2']['name']]
            # Make matrix symmetric
            matrix[i, j] = conflict['overlap']
            matrix[j, i] = conflict['overlap']
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=devices,
            y=devices,
            colorscale='Reds',
            hoverongaps=False,
            hovertemplate=(
                "Device 1: %{y}<br>" +
                "Device 2: %{x}<br>" +
                "Overlap: %{z} MHz<extra></extra>"
            )
        ))
        
        # Update layout
        fig.update_layout(
            title="Frequency Conflict Matrix",
            xaxis_title="Device",
            yaxis_title="Device",
            height=800,
            margin=dict(l=50, r=50, t=100, b=100)
        )
        
        # Save to file if specified
        if output_file:
            fig.write_html(output_file)
            logger.info(f"Conflict matrix saved to {output_file}")
        
        return fig
    
    def create_frequency_spectrum(self, output_file: Optional[str] = None) -> go.Figure:
        """
        Create a frequency spectrum visualization
        
        Args:
            output_file: Optional file path to save the chart
            
        Returns:
            Plotly figure object
        """
        # Get data from database
        wireless_configs = self.database.get_wireless_configs()
        devices = self.database.get_devices()
        
        # Create device lookup
        device_map = {}
        for device in devices:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = device
        
        # Prepare data for visualization
        chart_data = []
        for config in wireless_configs:
            device_id = config.get('deviceId')
            frequency = config.get('frequency')
            channel_width = config.get('channelWidth')
            
            if not device_id or not frequency or not channel_width:
                continue
            
            device = device_map.get(device_id, {})
            device_name = device.get('name', 'Unknown')
            device_type = device.get('type', 'Unknown')
            
            # Calculate frequency range
            half_width = channel_width / 2
            freq_min = frequency - half_width
            freq_max = frequency + half_width
            
            chart_data.append({
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type,
                'frequency': frequency,
                'channel_width': channel_width,
                'freq_min': freq_min,
                'freq_max': freq_max,
                'ssid': config.get('ssid', '')
            })
        
        if not chart_data:
            logger.warning("No frequency data available for visualization")
            fig = go.Figure()
            fig.add_annotation(
                text="No frequency data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(chart_data)
        
        # Create frequency range
        freq_range = np.linspace(
            df['freq_min'].min() - 50,
            df['freq_max'].max() + 50,
            1000
        )
        
        # Calculate spectrum density
        spectrum = np.zeros_like(freq_range)
        
        for _, row in df.iterrows():
            # Create a simple rectangular filter for each frequency band
            mask = (freq_range >= row['freq_min']) & (freq_range <= row['freq_max'])
            spectrum[mask] += 1
        
        # Create figure
        fig = go.Figure()
        
        # Add spectrum trace
        fig.add_trace(go.Scatter(
            x=freq_range,
            y=spectrum,
            mode='lines',
            fill='tozeroy',
            name='Frequency Utilization',
            line=dict(color='blue', width=2)
        ))
        
        # Add markers for each device's center frequency
        for _, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['frequency']],
                y=[0],
                mode='markers+text',
                marker=dict(size=10, color='red'),
                text=[row['device_name']],
                textposition='top center',
                name=row['device_name'],
                hovertemplate=(
                    f"<b>{row['device_name']}</b><br>" +
                    f"Frequency: {row['frequency']} MHz<br>" +
                    f"Channel Width: {row['channel_width']} MHz<br>" +
                    f"Range: {row['freq_min']} - {row['freq_max']} MHz<br>" +
                    f"SSID: {row['ssid']}<br>" +
                    f"Device Type: {row['device_type']}"
                )
            ))
        
        # Update layout
        fig.update_layout(
            title="NYC Mesh Frequency Spectrum",
            xaxis_title="Frequency (MHz)",
            yaxis_title="Number of Overlapping Devices",
            height=600,
            margin=dict(l=50, r=50, t=100, b=100),
            showlegend=False
        )
        
        # Save to file if specified
        if output_file:
            fig.write_html(output_file)
            logger.info(f"Frequency spectrum saved to {output_file}")
        
        return fig


class FrequencyDashboard:
    """Interactive dashboard for frequency visualization"""
    
    def __init__(self, database: FrequencyDatabase):
        """
        Initialize the frequency dashboard
        
        Args:
            database: Initialized frequency database
        """
        self.database = database
        self.visualizer = FrequencyVisualizer(database)
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            title="NYC Mesh Frequency Management"
        )
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Set up the dashboard layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("NYC Mesh Frequency Management", className="text-center my-4"),
                    html.P(
                        "Interactive visualization of frequency allocations and potential conflicts",
                        className="text-center lead mb-4"
                    )
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Visualization Controls"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Visualization Type"),
                                    dcc.Dropdown(
                                        id="visualization-type",
                                        options=[
                                            {"label": "Frequency Allocation Chart", "value": "allocation"},
                                            {"label": "Conflict Matrix", "value": "conflicts"},
                                            {"label": "Frequency Spectrum", "value": "spectrum"}
                                        ],
                                        value="allocation"
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label("Filter by Device Type"),
                                    dcc.Dropdown(
                                        id="device-type-filter",
                                        options=[],  # Will be populated in callback
                                        multi=True
                                    )
                                ], width=6)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Frequency Range (MHz)"),
                                    dcc.RangeSlider(
                                        id="frequency-range",
                                        min=5000,
                                        max=6000,
                                        step=10,
                                        marks={
                                            5000: "5000",
                                            5200: "5200",
                                            5400: "5400",
                                            5600: "5600",
                                            5800: "5800",
                                            6000: "6000"
                                        },
                                        value=[5000, 6000]
                                    )
                                ])
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "Export Visualization",
                                        id="export-button",
                                        color="primary",
                                        className="me-2"
                                    ),
                                    dbc.Button(
                                        "Refresh Data",
                                        id="refresh-button",
                                        color="secondary"
                                    )
                                ])
                            ])
                        ])
                    ], className="mb-4")
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Frequency Visualization"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-visualization",
                                type="circle",
                                children=[
                                    dcc.Graph(
                                        id="frequency-visualization",
                                        figure=go.Figure(),
                                        style={"height": "700px"}
                                    )
                                ]
                            )
                        ])
                    ])
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Frequency Conflicts"),
                        dbc.CardBody([
                            html.Div(id="conflict-summary")
                        ])
                    ], className="mt-4")
                ])
            ]),
            
            dbc.Modal([
                dbc.ModalHeader("Export Visualization"),
                dbc.ModalBody([
                    dbc.Input(
                        id="export-filename",
                        placeholder="Enter filename",
                        type="text",
                        value="frequency_visualization.html"
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
                    "NYC Mesh Frequency Management Tool",
                    className="text-center text-muted my-4"
                )
            ])
        ], fluid=True)
    
    def _setup_callbacks(self):
        """Set up the dashboard callbacks"""
        
        @self.app.callback(
            Output("device-type-filter", "options"),
            Input("refresh-button", "n_clicks")
        )
        def update_device_type_options(n_clicks):
            """Update device type filter options"""
            devices = self.database.get_devices()
            device_types = set()
            
            for device in devices:
                device_type = device.get('type')
                if device_type:
                    device_types.add(device_type)
            
            return [{"label": dtype, "value": dtype} for dtype in sorted(device_types)]
        
        @self.app.callback(
            Output("frequency-visualization", "figure"),
            [
                Input("visualization-type", "value"),
                Input("device-type-filter", "value"),
                Input("frequency-range", "value"),
                Input("refresh-button", "n_clicks")
            ]
        )
        def update_visualization(viz_type, device_types, freq_range, n_clicks):
            """Update the visualization based on user selections"""
            if viz_type == "allocation":
                return self.visualizer.create_frequency_chart()
            elif viz_type == "conflicts":
                return self.visualizer.create_conflict_matrix()
            elif viz_type == "spectrum":
                return self.visualizer.create_frequency_spectrum()
            else:
                return go.Figure()
        
        @self.app.callback(
            Output("conflict-summary", "children"),
            Input("refresh-button", "n_clicks")
        )
        def update_conflict_summary(n_clicks):
            """Update the conflict summary"""
            conflicts = self.database.get_frequency_conflicts()
            
            if not conflicts:
                return html.P("No frequency conflicts detected.")
            
            return html.Div([
                html.P(f"Detected {len(conflicts)} potential frequency conflicts:"),
                html.Ul([
                    html.Li([
                        f"{conflict['device1']['name']} and {conflict['device2']['name']} ",
                        f"at {conflict['frequency']} MHz ",
                        f"(overlap: {conflict['overlap']:.1f} MHz)"
                    ]) for conflict in conflicts[:10]  # Show first 10 conflicts
                ]),
                html.P(f"... and {len(conflicts) - 10} more conflicts") if len(conflicts) > 10 else None
            ])
        
        @self.app.callback(
            Output("export-modal", "is_open"),
            [
                Input("export-button", "n_clicks"),
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
            if button_id == "export-button":
                return True
            elif button_id in ["export-cancel", "export-confirm"]:
                return False
            return is_open
        
        @self.app.callback(
            Output("loading-visualization", "children"),
            [Input("export-confirm", "n_clicks")],
            [
                State("visualization-type", "value"),
                State("export-filename", "value")
            ]
        )
        def export_visualization(n_clicks, viz_type, filename):
            """Export the current visualization"""
            if n_clicks is None:
                return [
                    dcc.Graph(
                        id="frequency-visualization",
                        figure=go.Figure(),
                        style={"height": "700px"}
                    )
                ]
            
            if not filename:
                filename = "frequency_visualization.html"
            
            if viz_type == "allocation":
                self.visualizer.create_frequency_chart(output_file=filename)
            elif viz_type == "conflicts":
                self.visualizer.create_conflict_matrix(output_file=filename)
            elif viz_type == "spectrum":
                self.visualizer.create_frequency_spectrum(output_file=filename)
            
            return [
                dcc.Graph(
                    id="frequency-visualization",
                    figure=go.Figure(),
                    style={"height": "700px"}
                )
            ]
    
    def run_server(self, debug=False, port=8050):
        """Run the dashboard server"""
        self.app.run_server(debug=debug, port=port)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NYC Mesh Frequency Visualization')
    parser.add_argument('--db', default='frequency_data.db', help='Database file path')
    parser.add_argument('--output', help='Output file for static visualization')
    parser.add_argument('--type', choices=['allocation', 'conflicts', 'spectrum'], 
                        default='allocation', help='Visualization type')
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
        dashboard = FrequencyDashboard(database)
        print(f"Starting dashboard on http://localhost:{args.port}")
        dashboard.run_server(debug=True, port=args.port)
    else:
        # Create static visualization
        visualizer = FrequencyVisualizer(database)
        
        if args.type == 'allocation':
            fig = visualizer.create_frequency_chart(output_file=args.output)
        elif args.type == 'conflicts':
            fig = visualizer.create_conflict_matrix(output_file=args.output)
        elif args.type == 'spectrum':
            fig = visualizer.create_frequency_spectrum(output_file=args.output)
        
        if args.output:
            print(f"Visualization saved to {args.output}")
        else:
            # Show figure
            fig.show()

if __name__ == "__main__":
    main()
