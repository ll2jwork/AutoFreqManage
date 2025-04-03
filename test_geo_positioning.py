#!/usr/bin/env python3
"""
Test Script for Geographical Positioning Module
This script tests the geographical positioning functionality.
"""

import os
import sys
import logging
import argparse
from frequency_database import FrequencyDatabase
from geographical_positioning import GeoPositioningVisualizer, GeoDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('geo_positioning_test')

def test_static_maps(database_path, output_dir):
    """Test static map generation"""
    try:
        # Initialize database
        database = FrequencyDatabase(database_path)
        
        # Initialize visualizer
        visualizer = GeoPositioningVisualizer(database)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate device map
        device_map_file = os.path.join(output_dir, 'device_map.html')
        visualizer.create_device_map(output_file=device_map_file)
        logger.info(f"Device map saved to {device_map_file}")
        
        # Generate sector coverage map
        sector_map_file = os.path.join(output_dir, 'sector_coverage_map.html')
        visualizer.create_sector_coverage_map(output_file=sector_map_file)
        logger.info(f"Sector coverage map saved to {sector_map_file}")
        
        # Generate interference zone map
        interference_map_file = os.path.join(output_dir, 'interference_zone_map.html')
        visualizer.create_interference_zone_map(output_file=interference_map_file)
        logger.info(f"Interference zone map saved to {interference_map_file}")
        
        # Generate frequency heatmap
        heatmap_file = os.path.join(output_dir, 'frequency_heatmap.html')
        visualizer.create_frequency_heatmap(output_file=heatmap_file)
        logger.info(f"Frequency heatmap saved to {heatmap_file}")
        
        return True
    except Exception as e:
        logger.error(f"Static map generation test failed: {str(e)}")
        return False

def run_dashboard(database_path, port):
    """Run the interactive dashboard"""
    try:
        # Initialize database
        database = FrequencyDatabase(database_path)
        
        # Initialize dashboard
        dashboard = GeoDashboard(database)
        
        # Run dashboard
        logger.info(f"Starting geographical dashboard on http://localhost:{port}")
        dashboard.run_server(debug=True, port=port)
        
        return True
    except Exception as e:
        logger.error(f"Dashboard startup failed: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Geographical Positioning')
    parser.add_argument('--db', required=True, help='Database file path')
    parser.add_argument('--output', default='maps', help='Output directory for static maps')
    parser.add_argument('--dashboard', action='store_true', help='Run interactive dashboard')
    parser.add_argument('--port', type=int, default=8051, help='Dashboard port')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        sys.exit(1)
    
    # Test static map generation
    if not args.dashboard:
        success = test_static_maps(args.db, args.output)
        
        if success:
            print("\nStatic map generation test completed successfully!")
            print(f"Maps saved to {args.output}/")
        else:
            print("\nStatic map generation test failed.")
            sys.exit(1)
    else:
        # Run dashboard
        run_dashboard(args.db, args.port)

if __name__ == "__main__":
    main()
