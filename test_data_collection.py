#!/usr/bin/env python3
"""
Data Collection Module Test Script for NYC Mesh Frequency Management Tool
This script tests the UISP API client and data collection functionality.
"""

import os
import sys
import json
import logging
from datetime import datetime
from uisp_api_client import UISPAPIClient, FrequencyDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_collection_test')

def test_api_connection(base_url, api_token=None, username=None, password=None):
    """Test connection to UISP API"""
    try:
        client = UISPAPIClient(
            base_url=base_url,
            api_token=api_token,
            username=username,
            password=password
        )
        
        # Test getting devices
        devices = client.get_devices()
        logger.info(f"Successfully connected to UISP API. Found {len(devices)} devices.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to UISP API: {str(e)}")
        return None

def test_data_collection(client):
    """Test data collection functionality"""
    try:
        collector = FrequencyDataCollector(client)
        
        # Test getting devices
        devices = collector.get_devices(force_refresh=True)
        logger.info(f"Retrieved {len(devices)} devices from UISP API")
        
        # Test getting sites
        sites = collector.get_sites(force_refresh=True)
        logger.info(f"Retrieved {len(sites)} sites from UISP API")
        
        # Test getting wireless configuration
        wireless_config = collector.get_wireless_configuration(force_refresh=True)
        logger.info(f"Retrieved {len(wireless_config)} wireless configurations from UISP API")
        
        # Test getting AP profiles
        ap_profiles = collector.get_ap_profiles(force_refresh=True)
        logger.info(f"Retrieved {len(ap_profiles)} AP profiles from UISP API")
        
        # Test getting frequency data
        frequency_data = collector.get_frequency_data()
        logger.info("Successfully collected and processed frequency data")
        
        # Export data to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"frequency_data_{timestamp}.json"
        collector.export_data_to_json(output_file)
        logger.info(f"Exported frequency data to {output_file}")
        
        # Print summary
        print("\nData Collection Summary:")
        print(f"Devices: {len(devices)}")
        print(f"Sites: {len(sites)}")
        print(f"Wireless Configurations: {len(wireless_config)}")
        print(f"AP Profiles: {len(ap_profiles)}")
        print(f"Output File: {output_file}")
        
        return True
    except Exception as e:
        logger.error(f"Data collection test failed: {str(e)}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test UISP API Data Collection')
    parser.add_argument('--url', required=True, help='UISP base URL')
    parser.add_argument('--token', help='API token for authentication')
    parser.add_argument('--username', help='Username for authentication')
    parser.add_argument('--password', help='Password for authentication')
    
    args = parser.parse_args()
    
    # Validate authentication parameters
    if not args.token and not (args.username and args.password):
        parser.error("Either --token or both --username and --password must be provided")
    
    # Test API connection
    client = test_api_connection(
        base_url=args.url,
        api_token=args.token,
        username=args.username,
        password=args.password
    )
    
    if not client:
        print("Failed to connect to UISP API. Exiting.")
        sys.exit(1)
    
    # Test data collection
    success = test_data_collection(client)
    
    if success:
        print("\nData collection test completed successfully!")
    else:
        print("\nData collection test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
