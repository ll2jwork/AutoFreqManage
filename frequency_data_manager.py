#!/usr/bin/env python3
"""
Data Collection Integration Module for NYC Mesh Frequency Management Tool
This module integrates the API client and database components.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from uisp_api_client import UISPAPIClient, FrequencyDataCollector
from frequency_database import FrequencyDatabase, create_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_collection_integration')

class FrequencyDataManager:
    """
    Manages the collection and storage of frequency data
    """
    
    def __init__(self, api_client: UISPAPIClient, database: FrequencyDatabase):
        """
        Initialize the frequency data manager
        
        Args:
            api_client: Initialized UISP API client
            database: Initialized frequency database
        """
        self.api_client = api_client
        self.database = database
        self.collector = FrequencyDataCollector(api_client)
    
    def collect_and_store_data(self, force_refresh: bool = False) -> int:
        """
        Collect data from API and store in database
        
        Args:
            force_refresh: Force refresh from API ignoring cache
            
        Returns:
            ID of the stored frequency scan
        """
        # Collect device data
        logger.info("Collecting device data from UISP API")
        devices = self.collector.get_devices(force_refresh)
        self.database.store_devices(devices)
        
        # Collect site data
        logger.info("Collecting site data from UISP API")
        sites = self.collector.get_sites(force_refresh)
        self.database.store_sites(sites)
        
        # Collect wireless configuration data
        logger.info("Collecting wireless configuration data from UISP API")
        wireless_configs = self.collector.get_wireless_configuration(force_refresh)
        self.database.store_wireless_configs(wireless_configs)
        
        # Collect and store complete frequency scan
        logger.info("Processing and storing complete frequency scan")
        frequency_data = self.collector.get_frequency_data()
        scan_id = self.database.store_frequency_scan(frequency_data)
        
        logger.info(f"Data collection and storage completed. Scan ID: {scan_id}")
        return scan_id
    
    def export_latest_scan(self, output_file: str) -> bool:
        """
        Export the latest frequency scan to a JSON file
        
        Args:
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get latest scan
            scan_data = self.database.get_latest_frequency_scan()
            
            if not scan_data:
                logger.error("No frequency scan data found in database")
                return False
            
            # Write to file
            with open(output_file, 'w') as f:
                json.dump(scan_data, f, indent=2)
            
            logger.info(f"Latest frequency scan exported to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export frequency scan: {str(e)}")
            return False
    
    def analyze_frequency_conflicts(self) -> List[Dict]:
        """
        Analyze and identify frequency conflicts
        
        Returns:
            List of conflict dictionaries
        """
        conflicts = self.database.get_frequency_conflicts()
        logger.info(f"Identified {len(conflicts)} potential frequency conflicts")
        return conflicts
    
    def generate_frequency_report(self, output_file: str) -> bool:
        """
        Generate a comprehensive frequency report
        
        Args:
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get latest data
            devices = self.database.get_devices()
            sites = self.database.get_sites()
            wireless_configs = self.database.get_wireless_configs()
            conflicts = self.database.get_frequency_conflicts()
            
            # Prepare report data
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_devices': len(devices),
                    'total_sites': len(sites),
                    'total_wireless_configs': len(wireless_configs),
                    'total_conflicts': len(conflicts)
                },
                'conflicts': conflicts,
                'frequency_allocation': {},
                'sites': {}
            }
            
            # Process wireless configs by frequency
            for config in wireless_configs:
                frequency = config.get('frequency')
                if not frequency:
                    continue
                
                if frequency not in report['frequency_allocation']:
                    report['frequency_allocation'][frequency] = []
                
                device_id = config.get('deviceId')
                if not device_id:
                    continue
                
                # Find device info
                device_info = None
                for device in devices:
                    if device.get('id') == device_id:
                        device_info = {
                            'id': device.get('id'),
                            'name': device.get('name', 'Unknown'),
                            'model': device.get('model', 'Unknown'),
                            'site_id': device.get('siteId')
                        }
                        break
                
                if device_info:
                    report['frequency_allocation'][frequency].append({
                        'device': device_info,
                        'ssid': config.get('ssid'),
                        'channel_width': config.get('channelWidth'),
                        'tx_power': config.get('txPower')
                    })
            
            # Process sites with devices
            for site in sites:
                site_id = site.get('id')
                if not site_id:
                    continue
                
                site_devices = []
                for device in devices:
                    if device.get('siteId') == site_id:
                        site_devices.append({
                            'id': device.get('id'),
                            'name': device.get('name', 'Unknown'),
                            'model': device.get('model', 'Unknown')
                        })
                
                report['sites'][site_id] = {
                    'id': site_id,
                    'name': site.get('name', 'Unknown'),
                    'location': {
                        'latitude': site.get('latitude'),
                        'longitude': site.get('longitude'),
                        'elevation': site.get('elevation')
                    },
                    'devices': site_devices
                }
            
            # Write report to file
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Frequency report generated and saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate frequency report: {str(e)}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='NYC Mesh Frequency Data Collection')
    parser.add_argument('--url', required=True, help='UISP base URL')
    parser.add_argument('--token', help='API token for authentication')
    parser.add_argument('--username', help='Username for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--db', default='frequency_data.db', help='Database file path')
    parser.add_argument('--output', default='frequency_report.json', help='Output report file')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh from API')
    
    args = parser.parse_args()
    
    # Validate authentication parameters
    if not args.token and not (args.username and args.password):
        parser.error("Either --token or both --username and --password must be provided")
    
    try:
        # Initialize API client
        client = UISPAPIClient(
            base_url=args.url,
            api_token=args.token,
            username=args.username,
            password=args.password
        )
        
        # Initialize database
        database = create_database(args.db)
        
        # Initialize data manager
        manager = FrequencyDataManager(client, database)
        
        # Collect and store data
        scan_id = manager.collect_and_store_data(args.force_refresh)
        
        # Generate frequency report
        manager.generate_frequency_report(args.output)
        
        # Analyze conflicts
        conflicts = manager.analyze_frequency_conflicts()
        
        # Print summary
        print("\nData Collection Summary:")
        print(f"Scan ID: {scan_id}")
        print(f"Database: {args.db}")
        print(f"Report: {args.output}")
        print(f"Conflicts detected: {len(conflicts)}")
        
        if conflicts:
            print("\nPotential Frequency Conflicts:")
            for i, conflict in enumerate(conflicts[:5], 1):  # Show first 5 conflicts
                print(f"{i}. {conflict['device1']['name']} and {conflict['device2']['name']} at {conflict['frequency']} MHz")
            
            if len(conflicts) > 5:
                print(f"... and {len(conflicts) - 5} more conflicts (see report for details)")
        
        print(f"\nFrequency report generated successfully: {args.output}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
