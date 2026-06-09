Section 1: EPA API 
I used the EPA AQS API to pull all PM2.5 monitoring stations in California that were active between 2015-2025 and saved the data as california_aqs_monitors.csv

Section 2: Clean Data
I cleaned the data by converting lat/long and dates to the correct formats, filtering to only stations that were open during 2015-2025 and removing any rows that were missing coordinates.

Section 3: Plot EPA Stations:
I downloaded a California boundary outline and plotted all the stations as dots on a map to visually check that the data look right and saved it as california_aqs_monitor_map.png (page 3)

Section 4: Load and Plot MSA Boundaries
I loaded the Census Bureau’s MSA geodatabase, merged county shapes into full MSA polygons and filtered to California. I made this a colored map and saved it under california_msa_map.png (page 4)

Section 5: Spatial Join (EPA Stations → MSAs)
I converted the stations to a GeoDataFrame and ran a spatial join to check which MSA each station falls inside. This added msa_id and msa_name to each row and I saved it as california_stations_with_msa.csv and plotted a map saved as california_stations_msa_join.png (page 5)

Section 6: Load EJ Screen Data
I loaded the EJScreen CSV and filtered it to California's 9129 census tracts. I kept the relevant socioeconomic columns and converted them to numeric

Section 7: Download Census TIGER Shapefile
I downloaded the California census tract boundary shapefile and loaded it as a GeoDataFrame

Section 8: Spatial Join (EPA Stations → Census Tracts)
I took only the stations inside an MSA, dropped the leftover index_right column and ran a spatial join to add tract_geoid to each station row

Section 9: Merge EJScreen onto EPA Stations
I used tract_geoid to merge the EJScreen socioeconomic columns onto each station row and saved it under california_stations_final.csv

Section 10: Clean EPA CSV
I kept only the 10 columns that we wanted and renamed them to cleaner labels and saved it under california_stations_cleaned.csv

Section 11: Load PurpleAir Data
I loaded in the california_Purple_Air_sensors.csv. I dropped rows missing coordinated or PM2.5 readings and converted it to a GeoDataFrame

Section 12: Spatial Join (PurpleAir → MSAs)
I ran the same MSA spatial join to add msa_id and msa_name to each sensor row

Section 13: Spatial Join (PurpleAir → Census Tract)
I took only sensors inside an MSA and dropped index_right. I then ran the same census tract spatial join to add tract_geoid to each sensor row

Section 14: Merge EJScreen onto Purple Air
I used tract_geoid to merge EJScreen socioeconomic columns onto each sensor row and saved as california_purple_air_final.csv

Section 15: Clean PurpleAir CSV
I kept the same 10 columns as the EPA file and renamed them to match the cleaner versions. I saved it as purpleair_stations_cleaned.csv

