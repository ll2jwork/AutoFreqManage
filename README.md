# NYC Mesh Frequency Management Tool Documentation

## Overview

The NYC Mesh Frequency Management Tool is a comprehensive solution for managing frequency allocations and detecting interference in wireless mesh networks. This tool integrates data collection from UISP, frequency visualization, geographical positioning, and interference detection to provide network administrators with actionable insights for optimizing frequency usage.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
   - [Command Line Interface](#command-line-interface)
   - [Interactive Dashboard](#interactive-dashboard)
4. [Components](#components)
   - [Data Collection](#data-collection)
   - [Frequency Visualization](#frequency-visualization)
   - [Geographical Positioning](#geographical-positioning)
   - [Interference Detection](#interference-detection)
5. [Workflow](#workflow)
6. [Troubleshooting](#troubleshooting)
7. [Development](#development)
8. [License](#license)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- UISP instance with API access (optional, for live data collection)

### Dependencies

The tool requires the following Python packages:

- dash
- dash-bootstrap-components
- plotly
- pandas
- numpy
- folium
- geopy
- scikit-learn
- scipy
- requests
- sqlite3

### Installation Steps

1. Clone the repository or download the source code.

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a configuration file (see [Configuration](#configuration) section).

## Configuration

The tool uses a JSON configuration file to store settings. Create a file named `config.json` in the tool's directory with the following structure:

```json
{
  "uisp": {
    "base_url": "https://uisp.example.com",
    "api_token": "your_api_token",
    "username": "your_username",
    "password": "your_password"
  },
  "database": {
    "path": "frequency_data.db"
  },
  "output": {
    "directory": "output"
  },
  "dashboard": {
    "port": 8050
  }
}
```

### Configuration Options

- **uisp**: UISP API connection settings
  - **base_url**: URL of your UISP instance
  - **api_token**: API token for authentication (preferred method)
  - **username** and **password**: Alternative authentication method
- **database**: Database settings
  - **path**: Path to SQLite database file
- **output**: Output settings
  - **directory**: Directory for saving reports and visualizations
- **dashboard**: Dashboard settings
  - **port**: Port for the web dashboard

## Usage

### Command Line Interface

The tool provides a command-line interface for various operations:

```bash
python nyc_mesh_frequency_tool.py [options]
```

#### Options

- `--config PATH`: Path to configuration file (default: `config.json`)
- `--collect`: Collect data from UISP API
- `--force-refresh`: Force refresh from API (ignore cache)
- `--visualize`: Generate visualizations
- `--analyze`: Analyze interference
- `--dashboard`: Run integrated dashboard
- `--port PORT`: Dashboard port (overrides config)

#### Examples

Collect data from UISP API:
```bash
python nyc_mesh_frequency_tool.py --collect
```

Generate visualizations:
```bash
python nyc_mesh_frequency_tool.py --visualize
```

Analyze interference:
```bash
python nyc_mesh_frequency_tool.py --analyze
```

Run the dashboard:
```bash
python nyc_mesh_frequency_tool.py --dashboard
```

### Interactive Dashboard

The tool provides an interactive web dashboard for easy access to all functionality. To start the dashboard:

```bash
python nyc_mesh_frequency_tool.py --dashboard
```

Then open a web browser and navigate to `http://localhost:8050` (or the port specified in your configuration).

#### Dashboard Tabs

1. **Data Collection**: Collect and view data from UISP API
2. **Frequency Visualization**: Generate and view frequency charts
3. **Geographical Positioning**: Generate and view maps
4. **Interference Detection**: Analyze and view interference issues
5. **Reports**: Generate and access all reports

## Components

### Data Collection

The data collection component retrieves information from UISP API and stores it in a local database. It includes:

- **UISP API Client**: Handles authentication and API requests
- **Data Collector**: Retrieves device, site, and wireless configuration data
- **Database**: Stores collected data for offline analysis

#### Key Files

- `uisp_api_client.py`: UISP API client implementation
- `frequency_database.py`: Database implementation
- `frequency_data_manager.py`: Data collection and management

### Frequency Visualization

The frequency visualization component provides various charts and graphs for analyzing frequency allocations:

- **Frequency Allocation Chart**: Shows each device's frequency range
- **Conflict Matrix**: Displays potential frequency conflicts between devices
- **Frequency Spectrum**: Visualizes the overall spectrum usage

#### Key Files

- `frequency_visualization.py`: Visualization implementation

### Geographical Positioning

The geographical positioning component provides map-based visualizations:

- **Device Map**: Shows device locations
- **Sector Coverage**: Visualizes sector coverage patterns
- **Interference Zones**: Highlights potential interference areas
- **Frequency Heatmap**: Shows frequency usage density

#### Key Files

- `geographical_positioning.py`: Geographical visualization implementation

### Interference Detection

The interference detection component analyzes frequency data to identify potential interference issues:

- **Interference Detector**: Identifies frequency overlaps
- **Scoring System**: Calculates interference severity
- **Recommendation Engine**: Suggests solutions for interference issues
- **Clustering**: Groups related interference issues

#### Key Files

- `interference_detection.py`: Interference detection implementation

## Workflow

A typical workflow for using the tool:

1. **Configure**: Set up the configuration file with UISP API credentials
2. **Collect Data**: Retrieve data from UISP API
3. **Visualize**: Generate frequency and geographical visualizations
4. **Analyze**: Detect and analyze interference issues
5. **Review**: Examine recommendations and reports
6. **Implement**: Apply recommended changes to the network
7. **Verify**: Collect new data and verify improvements

## Troubleshooting

### Common Issues

#### Cannot connect to UISP API

- Verify that the base URL is correct
- Check API token or username/password
- Ensure the UISP instance is accessible from your network

#### No data displayed in visualizations

- Verify that data collection was successful
- Check the database file exists and has data
- Look for error messages in the console output

#### Dashboard not starting

- Check if the specified port is already in use
- Verify that all dependencies are installed
- Look for error messages in the console output

### Logging

The tool uses Python's logging module to provide detailed information about its operation. By default, logs are output to the console. To save logs to a file, you can redirect the output:

```bash
python nyc_mesh_frequency_tool.py --dashboard > tool.log 2>&1
```

## Development

### Architecture

The tool follows a modular architecture with the following components:

1. **Data Collection**: Retrieves and stores data
2. **Data Processing**: Processes and analyzes data
3. **Visualization**: Generates visual representations
4. **User Interface**: Provides access to functionality

### Adding New Features

To add new features to the tool:

1. Identify the appropriate component for your feature
2. Implement the feature in the corresponding module
3. Update the integration module (`nyc_mesh_frequency_tool.py`) to expose the feature
4. Update the documentation to describe the new feature

### Testing

The tool includes test scripts for each component:

- `test_data_collection.py`: Tests data collection functionality
- `test_visualization.py`: Tests visualization functionality
- `test_geo_positioning.py`: Tests geographical positioning functionality
- `test_interference_detection.py`: Tests interference detection functionality
- `test_integration.py`: Tests the integrated solution

To run tests:

```bash
python test_integration.py
```

## License

This tool is provided under the MIT License. See the LICENSE file for details.

---

## Appendix: File Structure

```
nyc_mesh_frequency_tool/
├── nyc_mesh_frequency_tool.py    # Main integration module
├── uisp_api_client.py            # UISP API client
├── frequency_database.py         # Database module
├── frequency_data_manager.py     # Data management module
├── frequency_visualization.py    # Frequency visualization module
├── geographical_positioning.py   # Geographical positioning module
├── interference_detection.py     # Interference detection module
├── config.json                   # Configuration file
├── requirements.txt              # Dependencies
├── test_data_collection.py       # Data collection tests
├── test_visualization.py         # Visualization tests
├── test_geo_positioning.py       # Geographical positioning tests
├── test_interference_detection.py # Interference detection tests
├── test_integration.py           # Integration tests
└── README.md                     # Documentation
```
