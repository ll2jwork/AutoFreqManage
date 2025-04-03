#!/usr/bin/env python3
"""
Test Script for Interference Detection Algorithm
This script tests the interference detection functionality.
"""

import os
import sys
import json
import logging
import argparse
from frequency_database import FrequencyDatabase
from interference_detection import InterferenceDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('interference_detection_test')

def test_interference_detection(database_path, output_dir):
    """Test interference detection functionality"""
    try:
        # Initialize database
        database = FrequencyDatabase(database_path)
        
        # Initialize interference detector
        detector = InterferenceDetector(database)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Detect interference
        results = detector.detect_frequency_interference()
        logger.info(f"Detected {len(results)} potential interference issues")
        
        # Generate report
        report_file = os.path.join(output_dir, 'interference_report.json')
        report = detector.generate_interference_report(report_file)
        logger.info(f"Interference report saved to {report_file}")
        
        # Generate cluster analysis
        clusters = detector.cluster_interference_issues()
        cluster_file = os.path.join(output_dir, 'interference_clusters.json')
        with open(cluster_file, 'w') as f:
            json.dump(clusters, f, indent=2)
        logger.info(f"Cluster analysis saved to {cluster_file}")
        
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
        
        logger.info(f"Recommendations summary saved to {recommendations_file}")
        
        return True
    except Exception as e:
        logger.error(f"Interference detection test failed: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Interference Detection')
    parser.add_argument('--db', required=True, help='Database file path')
    parser.add_argument('--output', default='interference_results', help='Output directory')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        sys.exit(1)
    
    # Test interference detection
    success = test_interference_detection(args.db, args.output)
    
    if success:
        print("\nInterference detection test completed successfully!")
        print(f"Results saved to {args.output}/")
    else:
        print("\nInterference detection test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
