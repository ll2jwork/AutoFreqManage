#!/usr/bin/env python3
"""
Database Module for NYC Mesh Frequency Management Tool
This module handles database operations for storing and retrieving frequency data.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('frequency_db')

class FrequencyDatabase:
    """Database handler for frequency management data"""
    
    def __init__(self, db_path: str):
        """
        Initialize the database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _initialize_db(self):
        """Initialize database schema if it doesn't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT,
            model TEXT,
            type TEXT,
            site_id TEXT,
            data JSON,
            last_updated TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id TEXT PRIMARY KEY,
            name TEXT,
            latitude REAL,
            longitude REAL,
            elevation REAL,
            data JSON,
            last_updated TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wireless_configs (
            id TEXT PRIMARY KEY,
            device_id TEXT,
            ssid TEXT,
            frequency INTEGER,
            channel_width INTEGER,
            tx_power REAL,
            data JSON,
            last_updated TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS frequency_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            data JSON
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def store_devices(self, devices: List[Dict]):
        """
        Store device data in database
        
        Args:
            devices: List of device dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        for device in devices:
            device_id = device.get('id')
            if not device_id:
                continue
                
            cursor.execute(
                '''
                INSERT OR REPLACE INTO devices 
                (id, name, model, type, site_id, data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    device_id,
                    device.get('name', 'Unknown'),
                    device.get('model', 'Unknown'),
                    device.get('type', 'Unknown'),
                    device.get('siteId'),
                    json.dumps(device),
                    timestamp
                )
            )
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(devices)} devices in database")
    
    def store_sites(self, sites: List[Dict]):
        """
        Store site data in database
        
        Args:
            sites: List of site dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        for site in sites:
            site_id = site.get('id')
            if not site_id:
                continue
                
            cursor.execute(
                '''
                INSERT OR REPLACE INTO sites 
                (id, name, latitude, longitude, elevation, data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    site_id,
                    site.get('name', 'Unknown'),
                    site.get('latitude'),
                    site.get('longitude'),
                    site.get('elevation'),
                    json.dumps(site),
                    timestamp
                )
            )
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(sites)} sites in database")
    
    def store_wireless_configs(self, configs: List[Dict]):
        """
        Store wireless configuration data in database
        
        Args:
            configs: List of wireless configuration dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        for config in configs:
            config_id = config.get('id')
            device_id = config.get('deviceId')
            if not config_id or not device_id:
                continue
                
            cursor.execute(
                '''
                INSERT OR REPLACE INTO wireless_configs 
                (id, device_id, ssid, frequency, channel_width, tx_power, data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    config_id,
                    device_id,
                    config.get('ssid'),
                    config.get('frequency'),
                    config.get('channelWidth'),
                    config.get('txPower'),
                    json.dumps(config),
                    timestamp
                )
            )
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(configs)} wireless configurations in database")
    
    def store_frequency_scan(self, scan_data: Dict):
        """
        Store a complete frequency scan in database
        
        Args:
            scan_data: Dictionary containing frequency scan data
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute(
            '''
            INSERT INTO frequency_scans 
            (timestamp, data)
            VALUES (?, ?)
            ''',
            (
                timestamp,
                json.dumps(scan_data)
            )
        )
        
        scan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Stored frequency scan with ID {scan_id} in database")
        return scan_id
    
    def get_devices(self):
        """
        Get all devices from database
        
        Returns:
            List of device dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM devices')
        rows = cursor.fetchall()
        
        devices = []
        for row in rows:
            devices.append(json.loads(row[0]))
        
        conn.close()
        return devices
    
    def get_sites(self):
        """
        Get all sites from database
        
        Returns:
            List of site dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM sites')
        rows = cursor.fetchall()
        
        sites = []
        for row in rows:
            sites.append(json.loads(row[0]))
        
        conn.close()
        return sites
    
    def get_wireless_configs(self):
        """
        Get all wireless configurations from database
        
        Returns:
            List of wireless configuration dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM wireless_configs')
        rows = cursor.fetchall()
        
        configs = []
        for row in rows:
            configs.append(json.loads(row[0]))
        
        conn.close()
        return configs
    
    def get_frequency_scan(self, scan_id: int):
        """
        Get a specific frequency scan from database
        
        Args:
            scan_id: ID of the frequency scan
            
        Returns:
            Dictionary containing frequency scan data
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM frequency_scans WHERE id = ?', (scan_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def get_latest_frequency_scan(self):
        """
        Get the latest frequency scan from database
        
        Returns:
            Dictionary containing frequency scan data
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM frequency_scans ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def get_frequency_data_for_device(self, device_id: str):
        """
        Get frequency data for a specific device
        
        Args:
            device_id: Device ID
            
        Returns:
            Dictionary containing device and its frequency data
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT d.data, w.data 
        FROM devices d
        LEFT JOIN wireless_configs w ON d.id = w.device_id
        WHERE d.id = ?
        ''', (device_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        device_data = json.loads(row[0])
        wireless_data = json.loads(row[1]) if row[1] else None
        
        return {
            'device': device_data,
            'wireless_config': wireless_data
        }
    
    def get_devices_by_site(self, site_id: str):
        """
        Get all devices for a specific site
        
        Args:
            site_id: Site ID
            
        Returns:
            List of device dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM devices WHERE site_id = ?', (site_id,))
        rows = cursor.fetchall()
        
        devices = []
        for row in rows:
            devices.append(json.loads(row[0]))
        
        conn.close()
        return devices
    
    def get_frequency_conflicts(self):
        """
        Identify potential frequency conflicts between devices
        
        Returns:
            List of conflict dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all wireless configs with frequency data
        cursor.execute('''
        SELECT d.id, d.name, d.site_id, w.frequency, w.channel_width
        FROM devices d
        JOIN wireless_configs w ON d.id = w.device_id
        WHERE w.frequency IS NOT NULL
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Group devices by frequency
        frequency_map = {}
        for row in rows:
            device_id, device_name, site_id, frequency, channel_width = row
            
            if not frequency:
                continue
                
            # Calculate frequency range
            half_width = (channel_width or 0) / 2
            freq_min = frequency - half_width
            freq_max = frequency + half_width
            
            device_info = {
                'id': device_id,
                'name': device_name,
                'site_id': site_id,
                'frequency': frequency,
                'channel_width': channel_width,
                'freq_min': freq_min,
                'freq_max': freq_max
            }
            
            if frequency not in frequency_map:
                frequency_map[frequency] = []
            
            frequency_map[frequency].append(device_info)
        
        # Identify conflicts
        conflicts = []
        for frequency, devices in frequency_map.items():
            if len(devices) < 2:
                continue
                
            # Check for overlaps
            for i in range(len(devices)):
                for j in range(i+1, len(devices)):
                    device1 = devices[i]
                    device2 = devices[j]
                    
                    # Check if frequency ranges overlap
                    if (device1['freq_min'] <= device2['freq_max'] and 
                        device1['freq_max'] >= device2['freq_min']):
                        
                        conflicts.append({
                            'device1': {
                                'id': device1['id'],
                                'name': device1['name'],
                                'site_id': device1['site_id']
                            },
                            'device2': {
                                'id': device2['id'],
                                'name': device2['name'],
                                'site_id': device2['site_id']
                            },
                            'frequency': frequency,
                            'overlap': min(device1['freq_max'], device2['freq_max']) - 
                                      max(device1['freq_min'], device2['freq_min'])
                        })
        
        return conflicts


def create_database(db_path: str = 'frequency_data.db'):
    """
    Create and initialize the frequency database
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Initialized FrequencyDatabase instance
    """
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    return FrequencyDatabase(db_path)


if __name__ == "__main__":
    # Example usage
    db = create_database('frequency_data.db')
    print(f"Database initialized at {db.db_path}")
