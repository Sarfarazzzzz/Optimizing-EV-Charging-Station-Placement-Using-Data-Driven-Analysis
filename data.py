import pandas as pd
import geopandas as gpd
import requests
import os

# Define the "East Coast" using FIPS codes
east_coast_fips = {
    '23': 'ME', '33': 'NH', '25': 'MA', '44': 'RI', '09': 'CT',
    '36': 'NY', '34': 'NJ', '42': 'PA', '10': 'DE', '24': 'MD',
    '11': 'DC', '51': 'VA', '54': 'WV', '37': 'NC', '45': 'SC',
    '13': 'GA', '12': 'FL', '01': 'AL', '47': 'TN', '39': 'OH'
}

# Define Variables
variables = {
    'B01003_001E': 'population',
    'B19013_001E': 'median_income',
    'B08301_001E': 'commuters_total',
    'B08301_010E': 'commuters_public_transport',
    'B25044_001E': 'households_total',
    'B25044_003E': 'households_no_vehicle'
}

# Comma-separated string for the API URL
var_string = ",".join(variables.keys())

# api_key = "&key=YOUR_CENSUS_API_KEY"
api_key = ""

combined_data = []

print(f"Starting Robust Download for {len(east_coast_fips)} states...")

for fips, abbr in east_coast_fips.items():
    print(f"[{abbr}] Processing...")

    try:
        # Fetch the DATA
        url = f"https://api.census.gov/data/2022/acs/acs5?get={var_string}&for=tract:*&in=state:{fips}{api_key}"

        # Read JSON response directly into Pandas
        data_df = pd.read_json(url)


        data_df.columns = data_df.iloc[0]
        data_df = data_df[1:]

        # Create a clean GEOID to match the shapefile (State + County + Tract)
        data_df['GEOID'] = data_df['state'] + data_df['county'] + data_df['tract']

        #  Fetch the SHAPE
        # We download the "Cartographic Boundary" (cb) file directly. It's lighter and faster.
        # Format: cb_2022_{FIPS}_tract_500k.zip
        shape_url = f"https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_{fips}_tract_500k.zip"

        geo_df = gpd.read_file(shape_url)

        # Merge on GEOID
        merged = geo_df.merge(data_df, on='GEOID')

        # Rename columns to human names
        merged = merged.rename(columns=variables)

        # Add State Name for reference
        merged['state_abbr'] = abbr

        # Append to master list
        combined_data.append(merged)

        print(f"   -> Success: Got {len(merged)} tracts for {abbr}")

    except Exception as e:
        print(f"   -> FAILED {abbr}: {e}")

# Save Final File
if combined_data:
    print("Combining all states...")
    final_gdf = pd.concat(combined_data, ignore_index=True)

    output_filename = "East_Coast_Tracts_Robust.geojson"
    final_gdf.to_file(output_filename, driver='GeoJSON')
    print(f"DONE! Saved {len(final_gdf)} tracts to {output_filename}")
else:
    print("No data was downloaded. Check your internet or API limits.")

#%%

import osmnx as ox
import networkx as nx
import geopandas as gpd

# Configuration
ox.settings.use_cache = True
ox.settings.log_console = True

# Define Scope
states = [
    "Maine, USA", "New Hampshire, USA", "Massachusetts, USA", "Rhode Island, USA", "Connecticut, USA",
    "New York, USA", "New Jersey, USA", "Pennsylvania, USA", "Delaware, USA", "Maryland, USA",
    "District of Columbia, USA", "Virginia, USA", "West Virginia, USA", "North Carolina, USA",
    "South Carolina, USA", "Georgia, USA", "Florida, USA", "Alabama, USA", "Tennessee, USA",
    "Ohio, USA"
]

# 3. Define the Filter
highway_filter = '["highway"~"motorway|trunk"]'

print(f"Starting Highway Download for {len(states)} states...")
print("This focuses ONLY on major interstates to prevent memory crashes.")

combined_graph = None

# 4. Loop & Download
for place in states:
    try:
        print(f"Fetching highways for {place}...")

        # Download the graph for the state
        G = ox.graph_from_place(place, custom_filter=highway_filter, simplify=True)

        # Combine with the master graph
        if combined_graph is None:
            combined_graph = G
        else:
            # nx.compose merges them while keeping connections valid
            combined_graph = nx.compose(combined_graph, G)

    except Exception as e:
        print(f"   -> Error fetching {place}: {e}")

# 5. Save the Data
if combined_graph:
    print("Consolidating network...")

    combined_graph_proj = ox.project_graph(combined_graph, to_crs="EPSG:5070")

    # Save as GraphML
    ox.save_graphml(combined_graph_proj, "East_Coast_Highways_Network.graphml")

    # Save as GeoPackage
    ox.save_graph_geopackage(combined_graph_proj, filepath="East_Coast_Highways_Visual.gpkg")

    print("SUCCESS!")
    print("1. 'East_Coast_Highways_Network.graphml' -> Use for Math/Optimization")
    print("2. 'East_Coast_Highways_Visual.gpkg' -> Use for Map Visualization")

else:
    print("No data collected.")