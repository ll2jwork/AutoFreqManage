#!/usr/bin/env python3
"""
Visualization Test Script for NYC Mesh Frequency Management Tool
This script tests the frequency visualization functionality.
"""

import os
import sys
import logging
import argparse
from frequency_database import FrequencyDatabase
from frequency_visualization import FrequencyVisualizer, FrequencyDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('visualization_test')

def test_static_visualizations(database_path, output_dir):
    """Test static visualization generation"""
    try:
        # Initialize database
        database = FrequencyDatabase(database_path)
        
        # Initialize visualizer
        visualizer = FrequencyVisualizer(database)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate frequency allocation chart
        allocation_file = os.path.join(output_dir, 'frequency_allocation.html')
        visualizer.create_frequency_chart(output_file=allocation_file)
        logger.info(f"Frequency allocation chart saved to {allocation_file}")
        
        # Generate conflict matrix
        conflict_file = os.path.join(output_dir, 'frequency_conflicts.html')
        visualizer.create_conflict_matrix(output_file=conflict_file)
        logger.info(f"Conflict matrix saved to {conflict_file}")
        
        # Generate frequency spectrum
        spectrum_file = os.path.join(output_dir, 'frequency_spectrum.html')
        visualizer.create_frequency_spectrum(output_file=spectrum_file)
        logger.info(f"Frequency spectrum saved to {spectrum_file}")
        
        return True
    except Exception as e:
        logger.error(f"Static visualization test failed: {str(e)}")
        return False

def run_dashboard(database_path, port):
    """Run the interactive dashboard"""
    try:
        # Initialize database
        database = FrequencyDatabase(database_path)
        
        # Initialize dashboard
        dashboard = FrequencyDashboard(database)
        
        # Run dashboard
        logger.info(f"Starting dashboard on http://localhost:{port}")
        dashboard.run_server(debug=True, port=port)
        
        return True
    except Exception as e:
        logger.error(f"Dashboard startup failed: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Frequency Visualization')
    parser.add_argument('--db', required=True, help='Database file path')
    parser.add_argument('--output', default='visualizations', help='Output directory for static visualizations')
    parser.add_argument('--dashboard', action='store_true', help='Run interactive dashboard')
    parser.add_argument('--port', type=int, default=8050, help='Dashboard port')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        sys.exit(1)
    
    # Test static visualizations
    if not args.dashboard:
        success = test_static_visualizations(args.db, args.output)
        
        if success:
            print("\nStatic visualization test completed successfully!")
            print(f"Visualizations saved to {args.output}/")
        else:
            print("\nStatic visualization test failed.")
            sys.exit(1)
    else:
        # Run dashboard
        run_dashboard(args.db, args.port)

if __name__ == "__main__":
    main()
