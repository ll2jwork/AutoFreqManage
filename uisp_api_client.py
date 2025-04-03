#!/usr/bin/env python3
"""
UISP API Client for NYC Mesh Frequency Management Tool
This module handles authentication and data retrieval from the UISP API.
"""

import requests
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('uisp_api_client')

class UISPAPIClient:
    """Client for interacting with the UISP API"""
    
    def __init__(self, base_url: str, api_token: str = None, username: str = None, password: str = None):
        """
        Initialize the UISP API client
        
        Args:
            base_url: Base URL of the UISP instance (e.g., https://uisp.example.com)
            api_token: API token for authentication (preferred method)
            username: Username for authentication (alternative method)
            password: Password for authentication (alternative method)
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.username = username
        self.password = password
        self.auth_token = None
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 0.5  # Delay between requests in seconds
        
        # Set up authentication
        if api_token:
            self.session.headers.update({'x-auth-token': api_token})
        elif username and password:
            self._login()
        else:
            raise ValueError("Either API token or username/password must be provided")
    
    def _login(self) -> None:
        """Authenticate with username and password to get auth token"""
        login_url = f"{self.base_url}/v2.1/user/login"
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            response = self.session.post(login_url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.auth_token = data.get('token')
            if not self.auth_token:
                raise ValueError("Authentication failed: No token received")
            
            self.session.headers.update({'x-auth-token': self.auth_token})
            logger.info("Successfully authenticated with UISP")
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to the UISP API with rate limiting
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body for POST/PUT requests
            
        Returns:
            Response data as dictionary
        """
        # Implement rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_request)
        
        url = f"{self.base_url}{endpoint}"
        self.last_request_time = time.time()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            )
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            if response.status_code == 401:
                logger.warning("Authentication token may have expired, attempting to re-authenticate")
                if self.username and self.password:
                    self._login()
                    # Retry the request
                    return self._make_request(method, endpoint, params, data)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def get_devices(self, params: Dict = None) -> List[Dict]:
        """
        Get list of all devices in the network
        
        Args:
            params: Optional query parameters
            
        Returns:
            List of device dictionaries
        """
        return self._make_request('GET', '/v2.1/devices', params)
    
    def get_device(self, device_id: str) -> Dict:
        """
        Get details for a specific device
        
        Args:
            device_id: Device ID
            
        Returns:
            Device details dictionary
        """
        return self._make_request('GET', f'/v2.1/devices/{device_id}')
    
    def get_device_statistics(self, device_id: str) -> Dict:
        """
        Get statistics for a specific device
        
        Args:
            device_id: Device ID
            
        Returns:
            Device statistics dictionary
        """
        return self._make_request('GET', f'/v2.1/devices/{device_id}/statistics')
    
    def get_ap_profiles(self) -> List[Dict]:
        """
        Get list of all access point connection profiles
        
        Returns:
            List of AP profile dictionaries
        """
        return self._make_request('GET', '/v2.1/devices/aps/profiles')
    
    def get_wireless_configuration(self) -> List[Dict]:
        """
        Get wireless configuration for all devices
        
        Returns:
            List of wireless configuration dictionaries
        """
        return self._make_request('GET', '/v2.1/devices/ssids')
    
    def get_sites(self, params: Dict = None) -> List[Dict]:
        """
        Get list of all sites in the network
        
        Args:
            params: Optional query parameters
            
        Returns:
            List of site dictionaries
        """
        return self._make_request('GET', '/v2.1/sites', params)
    
    def get_site(self, site_id: str) -> Dict:
        """
        Get details for a specific site
        
        Args:
            site_id: Site ID
            
        Returns:
            Site details dictionary
        """
        return self._make_request('GET', f'/v2.1/sites/{site_id}')


class FrequencyDataCollector:
    """
    Collects and processes frequency data from UISP API
    """
    
    def __init__(self, api_client: UISPAPIClient):
        """
        Initialize the frequency data collector
        
        Args:
            api_client: Initialized UISP API client
        """
        self.api_client = api_client
        self.devices_cache = {}
        self.sites_cache = {}
        self.wireless_config_cache = {}
        self.ap_profiles_cache = {}
        self.last_update = {
            'devices': None,
            'sites': None,
            'wireless_config': None,
            'ap_profiles': None
        }
        self.cache_ttl = 300  # Cache time-to-live in seconds
    
    def _is_cache_valid(self, cache_type: str) -> bool:
        """
        Check if cache is still valid based on TTL
        
        Args:
            cache_type: Type of cache to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.last_update[cache_type]:
            return False
        
        elapsed = (datetime.now() - self.last_update[cache_type]).total_seconds()
        return elapsed < self.cache_ttl
    
    def get_devices(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all devices, using cache if available
        
        Args:
            force_refresh: Force refresh from API ignoring cache
            
        Returns:
            List of device dictionaries
        """
        if force_refresh or not self._is_cache_valid('devices'):
            logger.info("Fetching devices from UISP API")
            self.devices_cache = self.api_client.get_devices()
            self.last_update['devices'] = datetime.now()
        
        return self.devices_cache
    
    def get_sites(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all sites, using cache if available
        
        Args:
            force_refresh: Force refresh from API ignoring cache
            
        Returns:
            List of site dictionaries
        """
        if force_refresh or not self._is_cache_valid('sites'):
            logger.info("Fetching sites from UISP API")
            self.sites_cache = self.api_client.get_sites()
            self.last_update['sites'] = datetime.now()
        
        return self.sites_cache
    
    def get_wireless_configuration(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get wireless configuration, using cache if available
        
        Args:
            force_refresh: Force refresh from API ignoring cache
            
        Returns:
            List of wireless configuration dictionaries
        """
        if force_refresh or not self._is_cache_valid('wireless_config'):
            logger.info("Fetching wireless configuration from UISP API")
            self.wireless_config_cache = self.api_client.get_wireless_configuration()
            self.last_update['wireless_config'] = datetime.now()
        
        return self.wireless_config_cache
    
    def get_ap_profiles(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get AP profiles, using cache if available
        
        Args:
            force_refresh: Force refresh from API ignoring cache
            
        Returns:
            List of AP profile dictionaries
        """
        if force_refresh or not self._is_cache_valid('ap_profiles'):
            logger.info("Fetching AP profiles from UISP API")
            self.ap_profiles_cache = self.api_client.get_ap_profiles()
            self.last_update['ap_profiles'] = datetime.now()
        
        return self.ap_profiles_cache
    
    def get_frequency_data(self) -> Dict:
        """
        Collect and process all frequency-related data
        
        Returns:
            Dictionary containing processed frequency data
        """
        # Get all required data
        devices = self.get_devices()
        wireless_config = self.get_wireless_configuration()
        sites = self.get_sites()
        
        # Process and combine data
        frequency_data = {
            'devices': devices,
            'wireless_config': wireless_config,
            'sites': sites,
            'device_frequency_map': self._map_devices_to_frequencies(devices, wireless_config),
            'site_device_map': self._map_sites_to_devices(sites, devices),
            'timestamp': datetime.now().isoformat()
        }
        
        return frequency_data
    
    def _map_devices_to_frequencies(self, devices: List[Dict], wireless_config: List[Dict]) -> Dict:
        """
        Create mapping between devices and their frequency settings
        
        Args:
            devices: List of device dictionaries
            wireless_config: List of wireless configuration dictionaries
            
        Returns:
            Dictionary mapping device IDs to frequency data
        """
        device_map = {}
        
        # Create lookup by device ID
        for device in devices:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = {
                    'id': device_id,
                    'name': device.get('name', 'Unknown'),
                    'model': device.get('model', 'Unknown'),
                    'type': device.get('type', 'Unknown'),
                    'site_id': device.get('siteId'),
                    'frequency_data': None
                }
        
        # Add frequency data from wireless config
        for config in wireless_config:
            device_id = config.get('deviceId')
            if device_id and device_id in device_map:
                # Extract frequency information
                frequency_data = {
                    'ssid': config.get('ssid'),
                    'frequency': config.get('frequency'),
                    'channel_width': config.get('channelWidth'),
                    'tx_power': config.get('txPower')
                }
                device_map[device_id]['frequency_data'] = frequency_data
        
        return device_map
    
    def _map_sites_to_devices(self, sites: List[Dict], devices: List[Dict]) -> Dict:
        """
        Create mapping between sites and their devices
        
        Args:
            sites: List of site dictionaries
            devices: List of device dictionaries
            
        Returns:
            Dictionary mapping site IDs to lists of device IDs
        """
        site_map = {}
        
        # Initialize site map
        for site in sites:
            site_id = site.get('id')
            if site_id:
                site_map[site_id] = {
                    'id': site_id,
                    'name': site.get('name', 'Unknown'),
                    'location': {
                        'latitude': site.get('latitude'),
                        'longitude': site.get('longitude'),
                        'elevation': site.get('elevation')
                    },
                    'devices': []
                }
        
        # Add devices to sites
        for device in devices:
            site_id = device.get('siteId')
            device_id = device.get('id')
            if site_id and device_id and site_id in site_map:
                site_map[site_id]['devices'].append(device_id)
        
        return site_map
    
    def export_data_to_json(self, filename: str) -> None:
        """
        Export collected frequency data to JSON file
        
        Args:
            filename: Output filename
        """
        data = self.get_frequency_data()
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Data exported to {filename}")
        except IOError as e:
            logger.error(f"Failed to write data to {filename}: {str(e)}")
            raise


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='UISP API Client for NYC Mesh Frequency Management')
    parser.add_argument('--url', required=True, help='UISP base URL')
    parser.add_argument('--token', help='API token for authentication')
    parser.add_argument('--username', help='Username for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--output', default='frequency_data.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    try:
        # Initialize API client
        client = UISPAPIClient(
            base_url=args.url,
            api_token=args.token,
            username=args.username,
            password=args.password
        )
        
        # Initialize data collector
        collector = FrequencyDataCollector(client)
        
        # Export data
        collector.export_data_to_json(args.output)
        
        print(f"Frequency data collected and exported to {args.output}")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
