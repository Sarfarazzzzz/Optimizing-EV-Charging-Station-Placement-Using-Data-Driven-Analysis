import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

print("--- STEP 1: LOAD RAW DATA ---")

# 1. Load the Census Tracts (The file you created earlier)
# Make sure "East_Coast_Tracts_Robust.geojson" is in the folder!
tracts_filename = "East_Coast_Tracts_Robust.geojson"
if os.path.exists(tracts_filename):
    print(f"Loading {tracts_filename}...")
    tracts_gdf = gpd.read_file(tracts_filename)
    # Project to Albers Equal Area (Meters) for accurate math
    tracts_gdf = tracts_gdf.to_crs("EPSG:5070")
else:
    print(f"CRITICAL ERROR: Could not find '{tracts_filename}'.")
    print("You must run the 'Phase 2: Census Data' script first!")
    exit()

# 2. Load Your Charger Excel File
# UPDATE THIS FILENAME to match your actual .xlsx file
charger_filename = "alt_fuel_stations (Jan 26 2026).xlsx"  # <--- CHECK THIS NAME

if os.path.exists(charger_filename):
    print(f"Loading {charger_filename}...")
    # Read Excel file
    chargers_df = pd.read_excel(charger_filename)

    # Filter for active stations only (Status Code 'E' = Available)
    # We also check that Lat/Lon exists
    chargers_df = chargers_df[
        (chargers_df['Status Code'] == 'E') &
        (chargers_df['Latitude'].notna()) &
        (chargers_df['Longitude'].notna())
        ]
else:
    print(f"CRITICAL ERROR: Could not find '{charger_filename}'.")
    print("Please paste your .xlsx file in this folder and update the filename in the code.")
    exit()

print("--- STEP 2: SPATIAL JOIN (Mapping Chargers to Tracts) ---")

# Convert DataFrame to GeoDataFrame (Points)
geometry = [Point(xy) for xy in zip(chargers_df['Longitude'], chargers_df['Latitude'])]
chargers_gdf = gpd.GeoDataFrame(chargers_df, geometry=geometry)

# Set initial CRS to Lat/Lon (EPSG:4326), then convert to Meters (EPSG:5070)
chargers_gdf.set_crs("EPSG:4326", inplace=True)
chargers_gdf = chargers_gdf.to_crs("EPSG:5070")

# Perform the Spatial Join (This links every charger to a census tract)
joined = gpd.sjoin(chargers_gdf, tracts_gdf, how="inner", predicate="within")

print("--- STEP 3: AGGREGATE COUNTS ---")

# Count Slow (Level 2) vs Fast (DC Fast) chargers per Tract
# We group by 'GEOID' (the unique ID for every census tract)
supply_metrics = joined.groupby('GEOID')[['EV Level2 EVSE Num', 'EV DC Fast Count']].sum().reset_index()

# Merge these counts back into the main map (Tracts)
final_map = tracts_gdf.merge(supply_metrics, on='GEOID', how='left')

# Fill NaNs with 0 (Tracts that have NO chargers)
cols_to_fix = ['EV Level2 EVSE Num', 'EV DC Fast Count']
final_map[cols_to_fix] = final_map[cols_to_fix].fillna(0)

# Create a "Total" column
final_map['charger_count'] = final_map['EV Level2 EVSE Num'] + final_map['EV DC Fast Count']

print("--- STEP 4: SAVE THE FILE ---")

output_filename = "East_Coast_Supply_Analyzed.geojson"
final_map.to_file(output_filename, driver='GeoJSON')

print(f"SUCCESS! Created '{output_filename}'.")
print("Now you can run the EDA/Stress Test script.")