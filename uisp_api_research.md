# UISP API Research for Frequency Management Tool

## API Endpoints Discovered

### Device Management
- `/v2.1/devices` - List of all devices in network
- `/v2.1/devices/id` - Device status overview
- `/v2.1/devices/id/statistics` - Device statistics

### Wireless Configuration
- `/v2.1/devices/aps/profiles` - List of all access points connection profiles
- `/v2.1/devices/ssids` - Get devices wireless configuration
  - Contains frequency settings and wireless parameters
  - Essential for retrieving current frequency allocations

### Site Management
- `/v2.1/sites` - List of all sites in network
- `/v2.1/sites/id` - Return a site's detail
  - Contains geographical positioning data
  - Needed for visualizing sector locations

## Authentication
- Authentication is done via x-auth-token header
- Token can be obtained via `/user/login` endpoint
- API keys can be generated in UISP under Settings => Security => App keys

## Data Structure
Based on the API documentation, we can retrieve:
1. Device information including model, type, and status
2. Wireless configuration including frequency, channel width, and power settings
3. Site information including geographical coordinates
4. Connection profiles and SSIDs

## Integration Approach
1. Use the UISP API to retrieve device and wireless configuration data
2. Extract frequency settings from wireless configuration
3. Map devices to sites for geographical positioning
4. Process data to identify potential frequency conflicts
5. Visualize frequency allocations and potential interference

## Limitations
- The API documentation doesn't explicitly show the format of frequency data
- We may need to test actual API responses to understand the exact data structure
- Some geographical data might need to be supplemented manually if not complete in the API

## Next Steps
1. Design the tool architecture based on these API capabilities
2. Plan the data collection module to interface with these endpoints
3. Design the frequency visualization component
4. Plan the geographical positioning features
5. Design the interference detection algorithm
