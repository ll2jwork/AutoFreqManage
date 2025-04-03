#!/usr/bin/env python3
"""
Interference Detection Algorithm for NYC Mesh Frequency Management Tool
This module provides advanced algorithms for detecting and analyzing frequency interference.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import math
import geopy.distance
from dataclasses import dataclass
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import pdist, squareform

from frequency_database import FrequencyDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('interference_detection')

@dataclass
class Device:
    """Data class for device information"""
    id: str
    name: str
    type: str
    model: str
    site_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    frequency: Optional[float] = None
    channel_width: Optional[float] = None
    tx_power: Optional[float] = None
    freq_min: Optional[float] = None
    freq_max: Optional[float] = None
    direction: Optional[str] = None
    beam_width: Optional[float] = None

@dataclass
class InterferenceResult:
    """Data class for interference detection results"""
    device1: Device
    device2: Device
    frequency_overlap: float
    distance: Optional[float] = None
    spatial_overlap: Optional[float] = None
    interference_score: float = 0.0
    recommendation: str = ""

class InterferenceDetector:
    """Detects and analyzes frequency interference between devices"""
    
    def __init__(self, database: FrequencyDatabase):
        """
        Initialize the interference detector
        
        Args:
            database: Initialized frequency database
        """
        self.database = database
        self.devices = []
        self.interference_results = []
        self.load_devices()
    
    def load_devices(self):
        """Load device data from database"""
        # Get data from database
        db_devices = self.database.get_devices()
        sites = self.database.get_sites()
        wireless_configs = self.database.get_wireless_configs()
        
        # Create site lookup
        site_map = {}
        for site in sites:
            site_id = site.get('id')
            if site_id:
                site_map[site_id] = site
        
        # Create wireless config lookup
        wireless_map = {}
        for config in wireless_configs:
            device_id = config.get('deviceId')
            if device_id:
                wireless_map[device_id] = config
        
        # Process devices
        for db_device in db_devices:
            device_id = db_device.get('id')
            if not device_id:
                continue
            
            # Get site information
            site_id = db_device.get('siteId')
            site = site_map.get(site_id, {})
            
            # Get wireless configuration
            wireless_config = wireless_map.get(device_id, {})
            
            # Extract frequency information
            frequency = wireless_config.get('frequency')
            channel_width = wireless_config.get('channelWidth')
            tx_power = wireless_config.get('txPower')
            
            # Calculate frequency range if available
            freq_min = None
            freq_max = None
            if frequency is not None and channel_width is not None:
                freq_min = frequency - (channel_width / 2)
                freq_max = frequency + (channel_width / 2)
            
            # Determine direction from device name
            direction = None
            beam_width = None
            name_lower = db_device.get('name', '').lower()
            
            if 'north' in name_lower:
                direction = 'north'
                beam_width = 90  # degrees
            elif 'east' in name_lower:
                direction = 'east'
                beam_width = 90
            elif 'south' in name_lower:
                direction = 'south'
                beam_width = 90
            elif 'west' in name_lower:
                direction = 'west'
                beam_width = 90
            
            # Create device object
            device = Device(
                id=device_id,
                name=db_device.get('name', 'Unknown'),
                type=db_device.get('type', 'Unknown'),
                model=db_device.get('model', 'Unknown'),
                site_id=site_id,
                latitude=site.get('latitude'),
                longitude=site.get('longitude'),
                frequency=frequency,
                channel_width=channel_width,
                tx_power=tx_power,
                freq_min=freq_min,
                freq_max=freq_max,
                direction=direction,
                beam_width=beam_width
            )
            
            self.devices.append(device)
        
        logger.info(f"Loaded {len(self.devices)} devices from database")
    
    def detect_frequency_interference(self):
        """
        Detect frequency interference between devices
        
        Returns:
            List of interference results
        """
        self.interference_results = []
        
        # Filter devices with frequency information
        freq_devices = [d for d in self.devices if d.frequency is not None and d.channel_width is not None]
        
        if len(freq_devices) < 2:
            logger.warning("Not enough devices with frequency information for interference detection")
            return self.interference_results
        
        # Check each pair of devices for frequency overlap
        for i in range(len(freq_devices)):
            for j in range(i+1, len(freq_devices)):
                device1 = freq_devices[i]
                device2 = freq_devices[j]
                
                # Skip if devices are on the same site (co-located)
                if device1.site_id == device2.site_id:
                    continue
                
                # Calculate frequency overlap
                if device1.freq_min is None or device1.freq_max is None or \
                   device2.freq_min is None or device2.freq_max is None:
                    continue
                
                # Check if frequency ranges overlap
                if device1.freq_min <= device2.freq_max and device1.freq_max >= device2.freq_min:
                    # Calculate overlap amount
                    overlap = min(device1.freq_max, device2.freq_max) - max(device1.freq_min, device2.freq_min)
                    
                    # Calculate distance if coordinates are available
                    distance = None
                    if (device1.latitude is not None and device1.longitude is not None and
                        device2.latitude is not None and device2.longitude is not None):
                        try:
                            distance = geopy.distance.distance(
                                (device1.latitude, device1.longitude),
                                (device2.latitude, device2.longitude)
                            ).meters
                        except Exception as e:
                            logger.warning(f"Error calculating distance: {str(e)}")
                    
                    # Calculate spatial overlap based on direction and beam width
                    spatial_overlap = self._calculate_spatial_overlap(device1, device2)
                    
                    # Calculate interference score
                    interference_score = self._calculate_interference_score(
                        overlap, distance, spatial_overlap, device1, device2
                    )
                    
                    # Generate recommendation
                    recommendation = self._generate_recommendation(
                        device1, device2, overlap, distance, interference_score
                    )
                    
                    # Create interference result
                    result = InterferenceResult(
                        device1=device1,
                        device2=device2,
                        frequency_overlap=overlap,
                        distance=distance,
                        spatial_overlap=spatial_overlap,
                        interference_score=interference_score,
                        recommendation=recommendation
                    )
                    
                    self.interference_results.append(result)
        
        # Sort results by interference score (descending)
        self.interference_results.sort(key=lambda x: x.interference_score, reverse=True)
        
        logger.info(f"Detected {len(self.interference_results)} potential interference issues")
        return self.interference_results
    
    def _calculate_spatial_overlap(self, device1: Device, device2: Device) -> Optional[float]:
        """
        Calculate spatial overlap between two devices based on direction and beam width
        
        Args:
            device1: First device
            device2: Second device
            
        Returns:
            Spatial overlap as a value between 0 and 1, or None if not applicable
        """
        # Skip if missing coordinates or direction information
        if (device1.latitude is None or device1.longitude is None or
            device2.latitude is None or device2.longitude is None or
            device1.direction is None or device2.direction is None or
            device1.beam_width is None or device2.beam_width is None):
            return None
        
        try:
            # Calculate bearing between devices
            bearing1to2 = geopy.distance.geodesic(
                (device1.latitude, device1.longitude),
                (device2.latitude, device2.longitude)
            ).bearing
            
            bearing2to1 = (bearing1to2 + 180) % 360
            
            # Convert direction to bearing
            dir_to_bearing = {
                'north': 0,
                'east': 90,
                'south': 180,
                'west': 270
            }
            
            bearing1 = dir_to_bearing.get(device1.direction)
            bearing2 = dir_to_bearing.get(device2.direction)
            
            if bearing1 is None or bearing2 is None:
                return None
            
            # Calculate angular difference between device direction and bearing to other device
            angle_diff1 = abs((bearing1 - bearing1to2 + 180) % 360 - 180)
            angle_diff2 = abs((bearing2 - bearing2to1 + 180) % 360 - 180)
            
            # Check if devices are facing each other
            half_beam1 = device1.beam_width / 2
            half_beam2 = device2.beam_width / 2
            
            # Calculate overlap percentage
            if angle_diff1 <= half_beam1 and angle_diff2 <= half_beam2:
                # Both devices are facing each other
                overlap1 = 1 - (angle_diff1 / half_beam1)
                overlap2 = 1 - (angle_diff2 / half_beam2)
                return (overlap1 + overlap2) / 2
            elif angle_diff1 <= half_beam1:
                # Only device1 is facing device2
                return 0.5 * (1 - (angle_diff1 / half_beam1))
            elif angle_diff2 <= half_beam2:
                # Only device2 is facing device1
                return 0.5 * (1 - (angle_diff2 / half_beam2))
            else:
                # Neither device is facing the other
                return 0.0
        except Exception as e:
            logger.warning(f"Error calculating spatial overlap: {str(e)}")
            return None
    
    def _calculate_interference_score(
        self, 
        frequency_overlap: float, 
        distance: Optional[float], 
        spatial_overlap: Optional[float],
        device1: Device,
        device2: Device
    ) -> float:
        """
        Calculate interference score based on frequency overlap, distance, and spatial overlap
        
        Args:
            frequency_overlap: Frequency overlap in MHz
            distance: Distance between devices in meters
            spatial_overlap: Spatial overlap between devices (0-1)
            device1: First device
            device2: Second device
            
        Returns:
            Interference score (higher means more severe)
        """
        # Base score from frequency overlap
        # Normalize by the smaller channel width to get a percentage
        min_channel_width = min(device1.channel_width or 20, device2.channel_width or 20)
        freq_score = (frequency_overlap / min_channel_width) * 100
        
        # Distance factor (if available)
        distance_factor = 1.0
        if distance is not None:
            # Inverse relationship with distance
            # Closer devices have higher interference potential
            # Use a sigmoid function to scale between 0.1 and 1.0
            # 5000m or more -> 0.1, 1000m -> ~0.5, 100m or less -> 1.0
            distance_factor = 0.1 + (0.9 / (1 + math.exp((math.log10(distance) - 3) * 2)))
        
        # Spatial overlap factor (if available)
        spatial_factor = 1.0
        if spatial_overlap is not None:
            # Direct relationship with spatial overlap
            # Higher overlap means higher interference potential
            spatial_factor = 0.2 + (0.8 * spatial_overlap)
        
        # Transmit power factor
        tx_power_factor = 1.0
        if device1.tx_power is not None and device2.tx_power is not None:
            # Higher power means higher interference potential
            # Normalize to a range of 0.5 to 1.5
            avg_power = (device1.tx_power + device2.tx_power) / 2
            tx_power_factor = 0.5 + (avg_power / 20)  # Assuming max power is ~20 dBm
        
        # Calculate final score
        score = freq_score * distance_factor * spatial_factor * tx_power_factor
        
        return score
    
    def _generate_recommendation(
        self, 
        device1: Device, 
        device2: Device, 
        overlap: float,
        distance: Optional[float],
        score: float
    ) -> str:
        """
        Generate recommendation for resolving interference
        
        Args:
            device1: First device
            device2: Second device
            overlap: Frequency overlap in MHz
            distance: Distance between devices in meters
            score: Interference score
            
        Returns:
            Recommendation string
        """
        if score < 20:
            return "Low interference risk. No action needed."
        
        recommendations = []
        
        # Find alternative frequencies
        alt_freq = self._find_alternative_frequency(device1, device2)
        if alt_freq:
            device_to_change = device1 if device1.frequency == alt_freq[0] else device2
            recommendations.append(
                f"Change {device_to_change.name} frequency from {device_to_change.frequency} MHz "
                f"to {alt_freq[1]} MHz."
            )
        
        # Suggest power reduction for high-power devices
        if device1.tx_power is not None and device1.tx_power > 15:
            recommendations.append(f"Reduce transmit power of {device1.name} from {device1.tx_power} dBm to {device1.tx_power - 3} dBm.")
        
        if device2.tx_power is not None and device2.tx_power > 15:
            recommendations.append(f"Reduce transmit power of {device2.name} from {device2.tx_power} dBm to {device2.tx_power - 3} dBm.")
        
        # Suggest adjusting antenna direction if applicable
        if device1.direction is not None and device2.direction is not None:
            recommendations.append(f"Adjust antenna direction of {device1.name} or {device2.name} to reduce overlap.")
        
        if not recommendations:
            recommendations.append("Consider changing frequency of one device to a different band.")
        
        severity = "High" if score > 70 else "Medium" if score > 40 else "Low"
        
        return f"Interference Severity: {severity}. " + " ".join(recommendations)
    
    def _find_alternative_frequency(self, device1: Device, device2: Device) -> Optional[tuple]:
        """
        Find alternative frequency for one of the devices
        
        Args:
            device1: First device
            device2: Second device
            
        Returns:
            Tuple of (current_frequency, alternative_frequency) or None if not found
        """
        # Get all frequencies in use
        used_frequencies = set()
        for device in self.devices:
            if device.frequency is not None:
                used_frequencies.add(device.frequency)
        
        # Define potential frequencies in 5GHz band
        # These are common center frequencies for 5GHz WiFi
        potential_frequencies = [
            5180, 5200, 5220, 5240, 5260, 5280, 5300, 5320,  # UNII-1 and UNII-2
            5500, 5520, 5540, 5560, 5580, 5600, 5620, 5640, 5660, 5680, 5700,  # UNII-2e
            5745, 5765, 5785, 5805, 5825  # UNII-3
        ]
        
        # Find frequencies not in use
        available_frequencies = [f for f in potential_frequencies if f not in used_frequencies]
        
        if not available_frequencies:
            return None
        
        # Find the best alternative frequency
        # For simplicity, just pick the first available frequency
        # In a real implementation, would need to consider more factors
        if device1.frequency in potential_frequencies:
            return (device1.frequency, available_frequencies[0])
        elif device2.frequency in potential_frequencies:
            return (device2.frequency, available_frequencies[0])
        
        return None
    
    def cluster_interference_issues(self, eps=30, min_samples=2):
        """
        Cluster interference issues to identify patterns
        
        Args:
            eps: Maximum distance between samples for clustering
            min_samples: Minimum number of samples in a cluster
            
        Returns:
            Dictionary with cluster information
        """
        if not self.interference_results:
            logger.warning("No interference results available for clustering")
            return {}
        
        # Extract features for clustering
        features = []
        for result in self.interference_results:
            # Use frequency and score as features
            features.append([
                result.device1.frequency or 0,
                result.device2.frequency or 0,
                result.interference_score
            ])
        
        # Convert to numpy array
        X = np.array(features)
        
        # Normalize features
        X_norm = (X - X.mean(axis=0)) / X.std(axis=0)
        
        # Perform clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X_norm)
        
        # Get cluster labels
        labels = clustering.labels_
        
        # Count number of clusters (excluding noise with label -1)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        # Group results by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:
                # Skip noise
                continue
            
            if label not in clusters:
                clusters[label] = []
            
            clusters[label].append(self.interference_results[i])
        
        # Calculate cluster statistics
        cluster_stats = {}
        for label, results in clusters.items():
            # Calculate average score
            avg_score = sum(r.interference_score for r in results) / len(results)
            
            # Find most common devices
            devices = []
            for r in results:
                devices.append(r.device1.name)
                devices.append(r.device2.name)
            
            device_counts = {}
            for device in devices:
                if device not in device_counts:
                    device_counts[device] = 0
                device_counts[device] += 1
            
            # Sort by count (descending)
            common_devices = sorted(device_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Find most common frequencies
            frequencies = []
            for r in results:
                frequencies.append(r.device1.frequency)
                frequencies.append(r.device2.frequency)
            
            freq_counts = {}
            for freq in frequencies:
                if freq not in freq_counts:
                    freq_counts[freq] = 0
                freq_counts[freq] += 1
            
            # Sort by count (descending)
            common_frequencies = sorted(freq_counts.items(), key=lambda x: x[1], reverse=True)
            
            cluster_stats[label] = {
                'size': len(results),
                'avg_score': avg_score,
                'common_devices': common_devices[:3],  # Top 3
                'common_frequencies': common_frequencies[:3],  # Top 3
                'results': results
            }
        
        return {
            'n_clusters': n_clusters,
            'clusters': cluster_stats
        }
    
    def generate_interference_report(self, output_file: Optional[str] = None) -> Dict:
        """
        Generate comprehensive interference report
        
        Args:
            output_file: Optional file path to save the report
            
        Returns:
            Report dictionary
        """
        # Ensure we have interference results
        if not self.interference_results:
            self.detect_frequency_interference()
        
        # Cluster interference issues
        clusters = self.cluster_interference_issues()
        
        # Prepare report data
        report = {
            'summary': {
                'total_devices': len(self.devices),
                'devices_with_frequency': sum(1 for d in self.devices if d.frequency is not None),
                'total_interference_issues': len(self.interference_results),
                'high_severity_issues': sum(1 for r in self.interference_results if r.interference_score > 70),
                'medium_severity_issues': sum(1 for r in self.interference_results if 40 < r.interference_score <= 70),
                'low_severity_issues': sum(1 for r in self.interference_results if r.interference_score <= 40),
                'clusters': clusters.get('n_clusters', 0)
            },
            'top_issues': [],
            'clusters': clusters.get('clusters', {}),
            'all_issues': []
        }
        
        # Add top issues (up to 10)
        for i, result in enumerate(self.interference_results[:10]):
            report['top_issues'].append({
                'rank': i + 1,
                'device1': {
                    'id': result.device1.id,
                    'name': result.device1.name,
                    'frequency': result.device1.frequency,
                    'channel_width': result.device1.channel_width
                },
                'device2': {
                    'id': result.device2.id,
                    'name': result.device2.name,
                    'frequency': result.device2.frequency,
                    'channel_width': result.device2.channel_width
                },
                'frequency_overlap': result.frequency_overlap,
                'distance': result.distance,
                'interference_score': result.interference_score,
                'recommendation': result.recommendation
            })
        
        # Add all issues
        for result in self.interference_results:
            report['all_issues'].append({
                'device1': {
                    'id': result.device1.id,
                    'name': result.device1.name,
                    'frequency': result.device1.frequency,
                    'channel_width': result.device1.channel_width
                },
                'device2': {
                    'id': result.device2.id,
                    'name': result.device2.name,
                    'frequency': result.device2.frequency,
                    'channel_width': result.device2.channel_width
                },
                'frequency_overlap': result.frequency_overlap,
                'distance': result.distance,
                'interference_score': result.interference_score,
                'recommendation': result.recommendation
            })
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Interference report saved to {output_file}")
        
        return report


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NYC Mesh Interference Detection')
    parser.add_argument('--db', default='frequency_data.db', help='Database file path')
    parser.add_argument('--output', default='interference_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        sys.exit(1)
    
    # Initialize database
    database = FrequencyDatabase(args.db)
    
    # Initialize interference detector
    detector = InterferenceDetector(database)
    
    # Detect interference
    results = detector.detect_frequency_interference()
    
    # Generate report
    report = detector.generate_interference_report(args.output)
    
    # Print summary
    print("\nInterference Detection Summary:")
    print(f"Total devices analyzed: {report['summary']['total_devices']}")
    print(f"Devices with frequency data: {report['summary']['devices_with_frequency']}")
    print(f"Total interference issues detected: {report['summary']['total_interference_issues']}")
    print(f"Severity breakdown:")
    print(f"  High: {report['summary']['high_severity_issues']}")
    print(f"  Medium: {report['summary']['medium_severity_issues']}")
    print(f"  Low: {report['summary']['low_severity_issues']}")
    print(f"Interference clusters identified: {report['summary']['clusters']}")
    
    if report['top_issues']:
        print("\nTop Interference Issues:")
        for i, issue in enumerate(report['top_issues'][:5]):  # Show top 5
            print(f"{i+1}. {issue['device1']['name']} and {issue['device2']['name']}")
            print(f"   Score: {issue['interference_score']:.1f}, Overlap: {issue['frequency_overlap']:.1f} MHz")
            print(f"   Recommendation: {issue['recommendation']}")
    
    print(f"\nDetailed report saved to {args.output}")

if __name__ == "__main__":
    main()
