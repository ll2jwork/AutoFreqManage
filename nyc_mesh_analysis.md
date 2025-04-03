# NYC Mesh Sector Frequency Analysis

## Current Situation Analysis

Based on the provided conversation and images, I can identify the following issues:

1. Saratoga-north sector is experiencing high utilization (100%) periodically
2. Specific nodes (nn203 & nn206) are having connectivity problems
3. There appears to be frequency interference between sectors
4. The current frequency allocation shows potential conflicts

## Current Frequency Allocations (Saratoga 1340)

From the spreadsheet image:

| Sector | Center Frequency | Control Frequency | Channel Width | Start Range | End Range |
|--------|------------------|-------------------|--------------|-------------|-----------|
| east   | 5570             | 5560              | 40           | 5550        | 5590      |
| south  | 5810             | 5800              | 40           | 5790        | 5830      |
| west   | 5570             | 5560              | 40           | 5550        | 5590      |
| west1  | 5700             | 5710              | 40           | 5680        | 5720      |
| north  | 5700             | 5710              | 40           | 5680        | 5720      |
| north2 | 5755             | 5765              | 40           | 5735        | 5775      |
| west0  | 5825             | 5815              | 40           | 5805        | 5845      |
| west2  | 5825             | 5815              | 40           | 5805        | 5845      |
| west3  | 5825             | 5815              | 40           | 5805        | 5845      |

## Key Issues Identified

1. **Frequency Conflict**: north and west1 sectors are both operating on the same frequency (5700 MHz), which is causing interference between these sectors.

2. **High Utilization**: The utilization charts show periods of 100% utilization, indicating channel saturation.

3. **Retransmissions**: The conversation mentions "all the retransmits" which suggests packet loss requiring retransmission, further degrading performance.

4. **CPU Maxing Out**: "something is maxing cpu; no capacity at current frequency" indicates the hardware is struggling to handle the traffic load.

## Channel Utilization Analysis

From the utilization charts provided:

1. **Current Utilization Patterns**:
   - The first utilization chart shows high variability with peak utilization at 100%
   - Average utilization of 34% with current peaks of 89%
   - Regular patterns of extreme utilization occurring every couple of days

2. **After Frequency Change**:
   - The second utilization chart (likely after changing to 5495 MHz) shows:
   - Current utilization dropped to 30%
   - Average utilization of 83% (historical data before change)
   - Peak still at 100% (historical data before change)
   - Significant drop in utilization visible at the end of the chart

3. **AirMAGIC Visualization**:
   - First image shows the sector on 5700 MHz with 0 Mbps/MHz efficiency
   - Second image shows testing of 5495 MHz with 11 Mbps/MHz efficiency
   - The spectrum visualization shows less interference at 5495 MHz
   - Client signal strength appears to improve in the second image

The data strongly suggests that the frequency change from 5700 MHz to 5495 MHz has a positive impact on performance, reducing channel utilization and improving throughput.

## Optimal Frequency Changes

Based on the analysis of the frequency chart and utilization data, I recommend the following frequency changes:

1. **Primary Recommendation**:
   - Move Saratoga-north from 5700 MHz to 5495 MHz
   - This frequency appears to be clear of other sectors based on the spreadsheet and conversation
   - Testing shows significant improvement with 11 Mbps/MHz efficiency vs 0 Mbps/MHz
   - The frequency chart indicates 5495 MHz does not overlap with North2, East, West, or West1

2. **Secondary Recommendation**:
   - If interference persists after moving north to 5495 MHz, consider also moving west1 to a different frequency
   - Potential options for west1 would be 5600-5650 MHz range which appears to be unused in the chart
   - This would require additional verification to ensure no overlap with other sectors

3. **Frequency Separation Strategy**:
   - Maintain minimum 40 MHz separation between sectors that have overlapping coverage areas
   - Ensure that sectors pointing in similar directions use frequencies that are well-separated
   - Consider the physical placement of sectors on the roof to minimize interference

4. **Verification Process**:
   - After changing frequencies, monitor utilization charts for at least 48 hours
   - Check client signal strengths and capacities before and after changes
   - Perform speed tests to verify improved throughput
   - Monitor for any DFS radar events that might force frequency changes

## Implementation Plan

### Preparation Phase

1. **Schedule Maintenance Window**:
   - Schedule the frequency change during low traffic period (around midnight)
   - Check utilization graphs to confirm optimal timing
   - Notify team members via private channel before proceeding

2. **Pre-Change Documentation**:
   - Update the frequency spreadsheet with current settings
   - Verify that 5495 MHz is indeed clear of other sectors
   - Ensure UISP access is available for the affected sectors

### Implementation Phase

1. **Before Change Documentation**:
   - Access the Saratoga-north sector in UISP
   - Take screenshots of all clients showing:
     - Current capacity values
     - Signal strength for each client
     - Total number of connected clients (should be around 12)
   - Document current utilization metrics

2. **Frequency Change Procedure for Saratoga-north**:
   - Navigate to the wireless tab in UISP
   - Select new center frequency: 5495 MHz
   - Set control frequency to 5500 MHz
   - Set channel width to 40 MHz
   - Maximize the Output Power slider (ensure at least 10dBm)
   - Save changes

3. **Wait Period**:
   - Allow 60 seconds for DFS wait period
   - Monitor for clients to reconnect (may take several minutes)
   - Do not interrupt the process during this time

4. **Verification**:
   - Once clients have reconnected, take "after" screenshots showing:
     - Updated capacity values
     - Signal strength for each client
     - Confirm all clients have reconnected
   - Check for any clients with poor signal strength (-70s and -80s are considered bad)
   - Perform speed tests to verify improved throughput

### Post-Implementation Phase

1. **Monitoring**:
   - Monitor utilization charts for 48 hours after the change
   - Check for any periods of high utilization
   - Verify that problem nodes (nn203 & nn206) have improved connectivity

2. **Documentation Update**:
   - Update the Google Spreadsheet with new frequency settings
   - Record the results of the change in team documentation
   - Share before/after screenshots with the team

3. **Contingency Plan**:
   - If performance does not improve, consider:
     - Trying another clear frequency
     - Moving west1 to a different frequency as well
     - Checking for physical interference or hardware issues

4. **Long-term Solution**:
   - Consider implementing the automated frequency chart generation tool mentioned by Willard
   - Develop a more systematic approach to frequency planning that accounts for geographical positioning
   - Establish regular maintenance schedule to check for frequency conflicts

## Additional Recommendations and Future Improvements

1. **Automated Frequency Management Tool**:
   - Develop the tool mentioned by Willard to automatically generate frequency charts
   - Include geographical positioning of sectors in the tool to better visualize potential interference
   - Integrate with UISP to automatically pull current frequency data rather than manual entry
   - Add visualization of sector coverage patterns to identify potential overlap areas

2. **Regular Frequency Audit Process**:
   - Establish a quarterly frequency audit process to identify and resolve conflicts
   - Document all frequency changes in a centralized system
   - Create alerts for when sectors are configured with overlapping frequencies

3. **Network Capacity Planning**:
   - Monitor client growth on each sector to anticipate capacity issues
   - Consider splitting busy sectors into multiple smaller sectors with different frequencies
   - Evaluate the need for additional hardware to handle high-traffic areas

4. **Signal Strength Optimization**:
   - Review antenna positioning and alignment for sectors with poor signal strength
   - Consider upgrading antennas or equipment for sectors with consistent issues
   - Document optimal signal strength ranges for different types of deployments

5. **DFS Considerations**:
   - Map areas with frequent DFS radar events to avoid those frequencies in affected locations
   - Develop a backup frequency plan for each sector in case of DFS events
   - Consider non-DFS frequencies for critical infrastructure where possible

6. **Client-Side Improvements**:
   - Audit client equipment to ensure compatibility with optimal frequencies
   - Provide guidelines for optimal client antenna positioning
   - Consider upgrading problematic client equipment

7. **Documentation and Knowledge Sharing**:
   - Create a comprehensive frequency management guide for the NYC Mesh team
   - Document best practices for frequency selection and change procedures
   - Establish a training program for new volunteers on frequency management

## Conclusion

The immediate solution to the Saratoga-north sector issues is to change its frequency from 5700 MHz to 5495 MHz, which testing has shown improves performance significantly. This change should resolve the interference with west1 sector which is also operating on 5700 MHz.

The implementation should be performed during low traffic hours following the detailed procedure outlined above. After implementation, thorough monitoring should be conducted to ensure the change has resolved the issues with nodes nn203 and nn206.

Long-term improvements to frequency management processes and tools will help prevent similar issues in the future and ensure optimal performance across the NYC Mesh network.
