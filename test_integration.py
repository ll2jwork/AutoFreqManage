#!/usr/bin/env python3
"""
Test Script for NYC Mesh Frequency Management Tool Integration
This script tests the integrated functionality of the tool.
"""

import os
import sys
import json
import logging
import argparse
from nyc_mesh_frequency_tool import NYCMeshFrequencyTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('integration_test')

def create_test_config(output_dir):
    """Create test configuration file"""
    config = {
        'uisp': {
            'base_url': 'https://uisp.example.com',  # Replace with actual URL for real testing
            'api_token': None,  # Replace with actual token for real testing
            'username': None,  # Replace with actual username for real testing
            'password': None   # Replace with actual password for real testing
        },
        'database': {
            'path': os.path.join(output_dir, 'test_frequency_data.db')
        },
        'output': {
            'directory': os.path.join(output_dir, 'test_output')
        },
        'dashboard': {
            'port': 8055  # Use different port for testing
        }
    }
    
    config_file = os.path.join(output_dir, 'test_config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Test configuration created at {config_file}")
    return config_file

def test_tool_initialization(config_file):
    """Test tool initialization"""
    try:
        tool = NYCMeshFrequencyTool(config_file=config_file)
        logger.info("Tool initialization successful")
        return tool
    except Exception as e:
        logger.error(f"Tool initialization failed: {str(e)}")
        return None

def test_visualization_generation(tool):
    """Test visualization generation"""
    try:
        visualization_files = tool.generate_visualizations()
        logger.info(f"Generated {len(visualization_files)} visualizations")
        
        for viz_type, file_path in visualization_files.items():
            if os.path.exists(file_path):
                logger.info(f"Visualization {viz_type} created successfully: {file_path}")
            else:
                logger.warning(f"Visualization {viz_type} file not found: {file_path}")
        
        return len(visualization_files) > 0
    except Exception as e:
        logger.error(f"Visualization generation failed: {str(e)}")
        return False

def test_interference_analysis(tool):
    """Test interference analysis"""
    try:
        report_file = tool.analyze_interference()
        
        if report_file and os.path.exists(report_file):
            logger.info(f"Interference analysis successful. Report saved to {report_file}")
            return True
        else:
            logger.warning("Interference analysis completed but report file not found")
            return False
    except Exception as e:
        logger.error(f"Interference analysis failed: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test NYC Mesh Frequency Management Tool Integration')
    parser.add_argument('--output', default='test', help='Output directory for test files')
    parser.add_argument('--dashboard', action='store_true', help='Run integrated dashboard after tests')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Create test configuration
    config_file = create_test_config(args.output)
    
    # Test tool initialization
    tool = test_tool_initialization(config_file)
    if not tool:
        print("Tool initialization test failed. Exiting.")
        sys.exit(1)
    
    # Test visualization generation
    viz_success = test_visualization_generation(tool)
    if not viz_success:
        print("Visualization generation test failed.")
    else:
        print("Visualization generation test passed.")
    
    # Test interference analysis
    interference_success = test_interference_analysis(tool)
    if not interference_success:
        print("Interference analysis test failed.")
    else:
        print("Interference analysis test passed.")
    
    # Run dashboard if requested
    if args.dashboard:
        print("Starting integrated dashboard...")
        tool.run_integrated_dashboard(debug=True)
    
    # Print overall result
    if viz_success and interference_success:
        print("\nAll integration tests passed successfully!")
    else:
        print("\nSome integration tests failed. Check logs for details.")

if __name__ == "__main__":
    main()
