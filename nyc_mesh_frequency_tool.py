#!/usr/bin/env python3
"""
NYC Mesh Frequency Management Tool - Main Integration Module
This module integrates all components of the frequency management tool.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Import all components
from uisp_api_client import UISPAPIClient, FrequencyDataCollector
from frequency_database import FrequencyDatabase, create_database
from frequency_data_manager import FrequencyDataManager
from frequency_visualization import FrequencyVisualizer
from geographical_positioning import GeoPositioningVisualizer
from interference_detection import InterferenceDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('nyc_mesh_frequency_tool')

class NYCMeshFrequencyTool:
    """Main class integrating all components of the NYC Mesh Frequency Management Tool"""
    
    def __init__(self, config_file=None):
        """
        Initialize the NYC Mesh Frequency Management Tool
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config = self._load_config(config_file)
        self.api_client = None
        self.database = None
        self.data_manager = None
        self.visualizer = None
        self.geo_visualizer = None
        self.interference_detector = None
        
        # Initialize components
        self._initialize_components()
    
    def _load_config(self, config_file):
        """
        Load configuration from file
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'uisp': {
                'base_url': None,
                'api_token': None,
                'username': None,
                'password': None
            },
            'database': {
                'path': 'frequency_data.db'
            },
            'output': {
                'directory': 'output'
            },
            'dashboard': {
                'port': 8050
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                
                # Merge user config with default config
                for section, values in user_config.items():
                    if section in default_config:
                        default_config[section].update(values)
                    else:
                        default_config[section] = values
                
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration: {str(e)}")
        
        return default_config
    
    def _initialize_components(self):
        """Initialize all components"""
        # Create output directory if it doesn't exist
        output_dir = self.config['output']['directory']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Initialize database
        db_path = self.config['database']['path']
        self.database = create_database(db_path)
        logger.info(f"Initialized database at {db_path}")
        
        # Initialize API client if credentials are provided
        uisp_config = self.config['uisp']
        if uisp_config['base_url']:
            self.api_client = UISPAPIClient(
                base_url=uisp_config['base_url'],
                api_token=uisp_config['api_token'],
                username=uisp_config['username'],
                password=uisp_config['password']
            )
            logger.info(f"Initialized UISP API client for {uisp_config['base_url']}")
            
            # Initialize data manager
            self.data_manager = FrequencyDataManager(self.api_client, self.database)
            logger.info("Initialized frequency data manager")
        
        # Initialize visualizer
        self.visualizer = FrequencyVisualizer(self.database)
        logger.info("Initialized frequency visualizer")
        
        # Initialize geographical visualizer
        self.geo_visualizer = GeoPositioningVisualizer(self.database)
        logger.info("Initialized geographical positioning visualizer")
        
        # Initialize interference detector
        self.interference_detector = InterferenceDetector(self.database)
        logger.info("Initialized interference detector")
    
    def collect_data(self, force_refresh=False):
        """
        Collect data from UISP API
        
        Args:
            force_refresh: Force refresh from API ignoring cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.data_manager:
            logger.error("Data manager not initialized. Check UISP API configuration.")
            return False
        
        try:
            # Collect and store data
            scan_id = self.data_manager.collect_and_store_data(force_refresh)
            logger.info(f"Data collection completed. Scan ID: {scan_id}")
            
            # Generate frequency report
            report_file = os.path.join(self.config['output']['directory'], 'frequency_report.json')
            self.data_manager.generate_frequency_report(report_file)
            logger.info(f"Frequency report generated: {report_file}")
            
            return True
        except Exception as e:
            logger.error(f"Error collecting data: {str(e)}")
            return False
    
    def generate_visualizations(self):
        """
        Generate all visualizations
        
        Returns:
            Dictionary of generated visualization files
        """
        output_dir = self.config['output']['directory']
        visualization_files = {}
        
        try:
            # Generate frequency visualizations
            freq_allocation_file = os.path.join(output_dir, 'frequency_allocation.html')
            self.visualizer.create_frequency_chart(output_file=freq_allocation_file)
            visualization_files['frequency_allocation'] = freq_allocation_file
            
            conflict_matrix_file = os.path.join(output_dir, 'frequency_conflicts.html')
            self.visualizer.create_conflict_matrix(output_file=conflict_matrix_file)
            visualization_files['conflict_matrix'] = conflict_matrix_file
            
            spectrum_file = os.path.join(output_dir, 'frequency_spectrum.html')
            self.visualizer.create_frequency_spectrum(output_file=spectrum_file)
            visualization_files['frequency_spectrum'] = spectrum_file
            
            # Generate geographical visualizations
            device_map_file = os.path.join(output_dir, 'device_map.html')
            self.geo_visualizer.create_device_map(output_file=device_map_file)
            visualization_files['device_map'] = device_map_file
            
            sector_map_file = os.path.join(output_dir, 'sector_coverage.html')
            self.geo_visualizer.create_sector_coverage_map(output_file=sector_map_file)
            visualization_files['sector_coverage'] = sector_map_file
            
            interference_map_file = os.path.join(output_dir, 'interference_zones.html')
            self.geo_visualizer.create_interference_zone_map(output_file=interference_map_file)
            visualization_files['interference_zones'] = interference_map_file
            
            heatmap_file = os.path.join(output_dir, 'frequency_heatmap.html')
            self.geo_visualizer.create_frequency_heatmap(output_file=heatmap_file)
            visualization_files['frequency_heatmap'] = heatmap_file
            
            logger.info(f"Generated {len(visualization_files)} visualizations")
            return visualization_files
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
            return visualization_files
    
    def analyze_interference(self):
        """
        Analyze interference and generate report
        
        Returns:
            Path to interference report file
        """
        output_dir = self.config['output']['directory']
        
        try:
            # Detect interference
            results = self.interference_detector.detect_frequency_interference()
            logger.info(f"Detected {len(results)} potential interference issues")
            
            # Generate report
            report_file = os.path.join(output_dir, 'interference_report.json')
            report = self.interference_detector.generate_interference_report(report_file)
            
            # Generate recommendations summary
            recommendations_file = os.path.join(output_dir, 'interference_recommendations.txt')
            with open(recommendations_file, 'w') as f:
                f.write("NYC Mesh Interference Recommendations\n")
                f.write("===================================\n\n")
                
                f.write("Summary:\n")
                f.write(f"- Total devices analyzed: {report['summary']['total_devices']}\n")
                f.write(f"- Devices with frequency data: {report['summary']['devices_with_frequency']}\n")
                f.write(f"- Total interference issues detected: {report['summary']['total_interference_issues']}\n")
                f.write(f"- High severity issues: {report['summary']['high_severity_issues']}\n")
                f.write(f"- Medium severity issues: {report['summary']['medium_severity_issues']}\n")
                f.write(f"- Low severity issues: {report['summary']['low_severity_issues']}\n")
                f.write(f"- Interference clusters identified: {report['summary']['clusters']}\n\n")
                
                f.write("Top Interference Issues:\n")
                for i, issue in enumerate(report['top_issues']):
                    f.write(f"{i+1}. {issue['device1']['name']} and {issue['device2']['name']}\n")
                    f.write(f"   Score: {issue['interference_score']:.1f}, Overlap: {issue['frequency_overlap']:.1f} MHz\n")
                    f.write(f"   Recommendation: {issue['recommendation']}\n\n")
            
            logger.info(f"Interference analysis completed. Report saved to {report_file}")
            logger.info(f"Recommendations saved to {recommendations_file}")
            
            return report_file
        except Exception as e:
            logger.error(f"Error analyzing interference: {str(e)}")
            return None
    
    def run_integrated_dashboard(self, debug=False, port=None):
        """
        Run integrated dashboard with all components
        
        Args:
            debug: Enable debug mode
            port: Dashboard port (overrides config)
        """
        if port is None:
            port = self.config['dashboard']['port']
        
        # Initialize Dash app
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            title="NYC Mesh Frequency Management Tool"
        )
        
        # Set up layout
        app.layout = self._create_dashboard_layout()
        
        # Set up callbacks
        self._setup_dashboard_callbacks(app)
        
        # Run server
        logger.info(f"Starting integrated dashboard on http://localhost:{port}")
        app.run(debug=debug, port=port)
    
    def _create_dashboard_layout(self):
        """
        Create dashboard layout
        
        Returns:
            Dash layout
        """
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("NYC Mesh Frequency Management Tool", className="text-center my-4"),
                    html.P(
                        "Comprehensive tool for managing frequency allocations and detecting interference",
                        className="text-center lead mb-4"
                    )
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Tabs([
                        dbc.Tab([
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H4("Data Collection"),
                                            html.P("Collect data from UISP API and store in database"),
                                            dbc.Button(
                                                "Collect Data",
                                                id="collect-data-button",
                                                color="primary",
                                                className="me-2"
                                            ),
                                            dbc.Button(
                                                "Force Refresh",
                                                id="force-refresh-button",
                                                color="secondary"
                                            ),
                                            html.Div(id="data-collection-status", className="mt-3")
                                        ])
                                    ])
                                ])
                            ], className="mb-4"),
                            
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4("Data Summary"),
                                    html.Div(id="data-summary")
                                ])
                            ])
                        ], label="Data Collection", tab_id="tab-data"),
                        
                        dbc.Tab([
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H4("Frequency Visualization"),
                                            dcc.Dropdown(
                                                id="frequency-viz-type",
                                                options=[
                                                    {"label": "Frequency Allocation Chart", "value": "allocation"},
                                                    {"label": "Conflict Matrix", "value": "conflicts"},
                                                    {"label": "Frequency Spectrum", "value": "spectrum"}
                                                ],
                                                value="allocation"
                                            ),
                                            dbc.Button(
                                                "Generate Visualization",
                                                id="generate-freq-viz-button",
                                                color="primary",
                                                className="mt-2"
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Loading(
                                                id="loading-freq-viz",
                                                type="circle",
                                                children=[
                                                    dcc.Graph(
                                                        id="frequency-visualization",
                                                        figure=go.Figure(),
                                                        style={"height": "600px"}
                                                    )
                                                ]
                                            )
                                        ])
                                    ])
                                ])
                            ])
                        ], label="Frequency Visualization", tab_id="tab-freq-viz"),
                        
                        dbc.Tab([
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H4("Geographical Visualization"),
                                            dcc.Dropdown(
                                                id="geo-viz-type",
                                                options=[
                                                    {"label": "Device Locations", "value": "devices"},
                                                    {"label": "Sector Coverage", "value": "sectors"},
                                                    {"label": "Interference Zones", "value": "interference"},
                                                    {"label": "Frequency Heatmap", "value": "heatmap"}
                                                ],
                                                value="devices"
                                            ),
                                            dbc.Button(
                                                "Generate Map",
                                                id="generate-map-button",
                                                color="primary",
                                                className="mt-2"
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.Iframe(
                                                id="map-iframe",
                                                style={"width": "100%", "height": "600px", "border": "none"}
                                            )
                                        ])
                                    ])
                                ])
                            ])
                        ], label="Geographical Positioning", tab_id="tab-geo-viz"),
                        
                        dbc.Tab([
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H4("Interference Analysis"),
                                            dbc.Button(
                                                "Analyze Interference",
                                                id="analyze-interference-button",
                                                color="primary"
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div(id="interference-summary", className="mt-3")
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.H5("Top Interference Issues", className="mt-4"),
                                            html.Div(id="interference-issues")
                                        ])
                                    ])
                                ])
                            ])
                        ], label="Interference Detection", tab_id="tab-interference"),
                        
                        dbc.Tab([
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H4("Generate Reports"),
                                            dbc.Button(
                                                "Generate All Reports",
                                                id="generate-reports-button",
                                                color="primary"
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div(id="reports-status", className="mt-3")
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.H5("Available Reports", className="mt-4"),
                                            html.Div(id="reports-list")
                                        ])
                                    ])
                                ])
                            ])
                        ], label="Reports", tab_id="tab-reports")
                    ], id="tabs", active_tab="tab-data")
                ])
            ]),
            
            html.Footer([
                html.P(
                    "NYC Mesh Frequency Management Tool",
                    className="text-center text-muted my-4"
                )
            ])
        ], fluid=True)
    
    def _setup_dashboard_callbacks(self, app):
        """
        Set up dashboard callbacks
        
        Args:
            app: Dash app
        """
        @app.callback(
            [
                Output("data-collection-status", "children"),
                Output("data-summary", "children")
            ],
            [
                Input("collect-data-button", "n_clicks"),
                Input("force-refresh-button", "n_clicks")
            ]
        )
        def handle_data_collection(n_collect, n_refresh):
            """Handle data collection button clicks"""
            ctx = dash.callback_context
            if not ctx.triggered:
                # Initial load
                return None, self._get_data_summary_component()
            
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            if button_id == "collect-data-button" and n_collect:
                success = self.collect_data(force_refresh=False)
                if success:
                    return dbc.Alert("Data collection successful", color="success"), self._get_data_summary_component()
                else:
                    return dbc.Alert("Data collection failed", color="danger"), self._get_data_summary_component()
            
            elif button_id == "force-refresh-button" and n_refresh:
                success = self.collect_data(force_refresh=True)
                if success:
                    return dbc.Alert("Data refresh successful", color="success"), self._get_data_summary_component()
                else:
                    return dbc.Alert("Data refresh failed", color="danger"), self._get_data_summary_component()
            
            return dash.no_update, dash.no_update
        
        @app.callback(
            Output("frequency-visualization", "figure"),
            [
                Input("generate-freq-viz-button", "n_clicks")
            ],
            [
                State("frequency-viz-type", "value")
            ]
        )
        def generate_frequency_visualization(n_clicks, viz_type):
            """Generate frequency visualization"""
            if not n_clicks:
                return go.Figure()
            
            if viz_type == "allocation":
                return self.visualizer.create_frequency_chart()
            elif viz_type == "conflicts":
                return self.visualizer.create_conflict_matrix()
            elif viz_type == "spectrum":
                return self.visualizer.create_frequency_spectrum()
            else:
                return go.Figure()
        
        @app.callback(
            Output("map-iframe", "src"),
            [
                Input("generate-map-button", "n_clicks")
            ],
            [
                State("geo-viz-type", "value")
            ]
        )
        def generate_map(n_clicks, map_type):
            """Generate map visualization"""
            if not n_clicks:
                return ""
            
            output_dir = self.config['output']['directory']
            
            if map_type == "devices":
                map_file = os.path.join(output_dir, 'device_map.html')
                self.geo_visualizer.create_device_map(output_file=map_file)
                return map_file
            elif map_type == "sectors":
                map_file = os.path.join(output_dir, 'sector_coverage.html')
                self.geo_visualizer.create_sector_coverage_map(output_file=map_file)
                return map_file
            elif map_type == "interference":
                map_file = os.path.join(output_dir, 'interference_zones.html')
                self.geo_visualizer.create_interference_zone_map(output_file=map_file)
                return map_file
            elif map_type == "heatmap":
                map_file = os.path.join(output_dir, 'frequency_heatmap.html')
                self.geo_visualizer.create_frequency_heatmap(output_file=map_file)
                return map_file
            else:
                return ""
        
        @app.callback(
            [
                Output("interference-summary", "children"),
                Output("interference-issues", "children")
            ],
            [
                Input("analyze-interference-button", "n_clicks")
            ]
        )
        def analyze_interference_callback(n_clicks):
            """Analyze interference"""
            if not n_clicks:
                return None, None
            
            try:
                # Detect interference
                results = self.interference_detector.detect_frequency_interference()
                
                # Generate report
                report_file = os.path.join(self.config['output']['directory'], 'interference_report.json')
                report = self.interference_detector.generate_interference_report(report_file)
                
                # Create summary component
                summary = dbc.Card([
                    dbc.CardBody([
                        html.H5("Interference Summary"),
                        html.P(f"Total devices analyzed: {report['summary']['total_devices']}"),
                        html.P(f"Devices with frequency data: {report['summary']['devices_with_frequency']}"),
                        html.P(f"Total interference issues: {report['summary']['total_interference_issues']}"),
                        html.P([
                            "Severity breakdown: ",
                            html.Span(f"High: {report['summary']['high_severity_issues']}", className="text-danger me-2"),
                            html.Span(f"Medium: {report['summary']['medium_severity_issues']}", className="text-warning me-2"),
                            html.Span(f"Low: {report['summary']['low_severity_issues']}", className="text-success")
                        ]),
                        html.P(f"Interference clusters: {report['summary']['clusters']}")
                    ])
                ])
                
                # Create issues component
                issues = []
                for i, issue in enumerate(report['top_issues'][:10]):  # Show top 10
                    severity_class = "text-danger" if issue['interference_score'] > 70 else \
                                    "text-warning" if issue['interference_score'] > 40 else \
                                    "text-success"
                    
                    issues.append(dbc.Card([
                        dbc.CardBody([
                            html.H6([
                                f"{i+1}. {issue['device1']['name']} and {issue['device2']['name']}",
                                html.Span(
                                    f" (Score: {issue['interference_score']:.1f})",
                                    className=severity_class
                                )
                            ]),
                            html.P(f"Frequency overlap: {issue['frequency_overlap']:.1f} MHz"),
                            html.P(f"Recommendation: {issue['recommendation']}")
                        ])
                    ], className="mb-2"))
                
                return summary, html.Div(issues)
            except Exception as e:
                logger.error(f"Error analyzing interference: {str(e)}")
                return dbc.Alert("Error analyzing interference", color="danger"), None
        
        @app.callback(
            [
                Output("reports-status", "children"),
                Output("reports-list", "children")
            ],
            [
                Input("generate-reports-button", "n_clicks")
            ]
        )
        def generate_reports(n_clicks):
            """Generate all reports"""
            if not n_clicks:
                return None, self._get_reports_list_component()
            
            try:
                # Generate all visualizations
                visualizations = self.generate_visualizations()
                
                # Analyze interference
                self.analyze_interference()
                
                # Generate frequency report
                if self.data_manager:
                    report_file = os.path.join(self.config['output']['directory'], 'frequency_report.json')
                    self.data_manager.generate_frequency_report(report_file)
                
                return dbc.Alert("Reports generated successfully", color="success"), self._get_reports_list_component()
            except Exception as e:
                logger.error(f"Error generating reports: {str(e)}")
                return dbc.Alert("Error generating reports", color="danger"), self._get_reports_list_component()
    
    def _get_data_summary_component(self):
        """
        Get data summary component
        
        Returns:
            Dash component
        """
        try:
            # Count devices
            devices = self.database.get_devices()
            sites = self.database.get_sites()
            wireless_configs = self.database.get_wireless_configs()
            
            # Get latest scan
            latest_scan = self.database.get_latest_frequency_scan()
            scan_time = "N/A"
            if latest_scan:
                # Try to extract timestamp from scan data
                scan_time = latest_scan.get('timestamp', 'N/A')
            
            return dbc.Card([
                dbc.CardBody([
                    html.H5("Database Summary"),
                    html.P(f"Total devices: {len(devices)}"),
                    html.P(f"Total sites: {len(sites)}"),
                    html.P(f"Wireless configurations: {len(wireless_configs)}"),
                    html.P(f"Latest scan: {scan_time}")
                ])
            ])
        except Exception as e:
            logger.error(f"Error getting data summary: {str(e)}")
            return dbc.Alert("Error retrieving data summary", color="danger")
    
    def _get_reports_list_component(self):
        """
        Get reports list component
        
        Returns:
            Dash component
        """
        try:
            output_dir = self.config['output']['directory']
            reports = []
            
            # Check for report files
            report_files = {
                'frequency_report.json': 'Frequency Report',
                'interference_report.json': 'Interference Report',
                'interference_recommendations.txt': 'Interference Recommendations',
                'frequency_allocation.html': 'Frequency Allocation Chart',
                'frequency_conflicts.html': 'Frequency Conflict Matrix',
                'frequency_spectrum.html': 'Frequency Spectrum',
                'device_map.html': 'Device Location Map',
                'sector_coverage.html': 'Sector Coverage Map',
                'interference_zones.html': 'Interference Zones Map',
                'frequency_heatmap.html': 'Frequency Heatmap'
            }
            
            for filename, title in report_files.items():
                file_path = os.path.join(output_dir, filename)
                if os.path.exists(file_path):
                    # Get file modification time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    mod_time_str = mod_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    reports.append(dbc.ListGroupItem([
                        html.Div([
                            html.Strong(title),
                            html.Small(f" (Generated: {mod_time_str})", className="text-muted ms-2")
                        ]),
                        html.A("Open", href=file_path, target="_blank", className="ms-2")
                    ]))
            
            if not reports:
                return html.P("No reports generated yet")
            
            return dbc.ListGroup(reports)
        except Exception as e:
            logger.error(f"Error getting reports list: {str(e)}")
            return dbc.Alert("Error retrieving reports list", color="danger")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='NYC Mesh Frequency Management Tool')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--collect', action='store_true', help='Collect data from UISP API')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh from API')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    parser.add_argument('--analyze', action='store_true', help='Analyze interference')
    parser.add_argument('--dashboard', action='store_true', help='Run integrated dashboard')
    parser.add_argument('--port', type=int, help='Dashboard port')
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = NYCMeshFrequencyTool(config_file=args.config)
    
    # Process commands
    if args.collect:
        tool.collect_data(force_refresh=args.force_refresh)
    
    if args.visualize:
        tool.generate_visualizations()
    
    if args.analyze:
        tool.analyze_interference()
    
    if args.dashboard:
        tool.run_integrated_dashboard(port=args.port)
    
    # If no specific command, run dashboard
    if not (args.collect or args.visualize or args.analyze or args.dashboard):
        tool.run_integrated_dashboard()

if __name__ == "__main__":
    main()
