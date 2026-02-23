import geopandas as gpd
import pandas as pd
import numpy as np
import folium
import os

print("--- DIAGNOSTIC & REPAIR: FIXING THE SOUTH & NEGATIVES ---")

# 1. LOAD DATA
file_path = "East_Coast_Model_Ready.geojson"
if not os.path.exists(file_path):
    print("ERROR: File not found.")
    exit()

gdf = gpd.read_file(file_path)

# --- DIAGNOSIS 1: WHERE DID THE CHARGERS GO? ---
print("\n1. INVESTIGATING MISSING CHARGERS...")
# Group by State and sum the charger counts
state_stats = gdf.groupby('state_abbr')['charger_count'].sum().sort_values(ascending=False)
print("Total Chargers per State (Check if South is 0):")
print(state_stats)

# IF THE SOUTH IS 0, WE NEED TO RE-MERGE (Simulated Fix)
# (Since we can't go back to Phase 3 easily, we will try to recover data if available,
# or flag this as a critical data entry error).
if state_stats.get('FL', 0) == 0:
    print("\nCRITICAL ALERT: Florida has 0 chargers. The South was lost in the merge.")
    print("Attempting to fix using raw columns if available...")
    # Check if raw columns exist
    if 'EV DC Fast Count' in gdf.columns:
        gdf['charger_count'] = gdf['EV DC Fast Count'].fillna(0) + gdf['EV Level2 EVSE Num'].fillna(0)
        print("-> Re-calculated charger_count from raw columns.")
        # Re-check
        print(gdf.groupby('state_abbr')['charger_count'].sum().head())

# --- DIAGNOSIS 2: FIXING NEGATIVE INCOME ---
print("\n2. FIXING NEGATIVE INCOME...")
# Check before
min_inc_before = gdf['median_income'].min()
print(f"Minimum Income BEFORE fix: ${min_inc_before:,.0f}")

# Force numeric
gdf['median_income'] = pd.to_numeric(gdf['median_income'], errors='coerce')

# Apply Fix: Set negatives to NaN, then Impute
gdf.loc[gdf['median_income'] < 0, 'median_income'] = np.nan
gdf['median_income'] = gdf.groupby('state_abbr')['median_income'].transform(lambda x: x.fillna(x.median()))

# Check after
min_inc_after = gdf['median_income'].min()
print(f"Minimum Income AFTER fix:  ${min_inc_after:,.0f}")

# --- 3. RE-MAPPING WITH SKELETON ---
print("\n3. RE-GENERATING MAP WITH HIGHWAY SKELETON...")

m = folium.Map(location=[34.0, -80.0], zoom_start=6, tiles="CartoDB positron") # Centered on South

# LAYER A: THE HIGHWAY SKELETON (Black Lines)
# We load the highway file specifically to draw the lines
if os.path.exists("East_Coast_Highways_Visual.gpkg"):
    print("   - Adding Highway Network lines...")
    # Load and simplify for performance
    highways = gpd.read_file("East_Coast_Highways_Visual.gpkg", layer='edges')
    # Filter for major highways only to keep map fast
    # (Assuming simple load for visualization)
    folium.GeoJson(
        highways[['geometry']],
        name="Interstate Network",
        style_function=lambda x: {'color': 'black', 'weight': 2, 'opacity': 0.6}
    ).add_to(m)

# LAYER B: CORRIDOR GAPS (Red)
# Gap = <1 mile from Hwy AND 0 Chargers
gaps = gdf[(gdf['dist_to_hwy_miles'] < 1.0) & (gdf['charger_count'] == 0)]
folium.GeoJson(
    gaps[['geometry']].simplify(0.01),
    name="Gaps (Needs Chargers)",
    style_function=lambda x: {'color': 'red', 'weight': 0, 'fillOpacity': 0.6},
    tooltip="Corridor Gap"
).add_to(m)

# LAYER C: EXISTING CHARGERS (Green)
served = gdf[gdf['charger_count'] > 0]
# Add markers
served_points = served.copy().to_crs(epsg=4326)
for idx, row in served_points.iterrows():
    folium.CircleMarker(
        location=[row.geometry.centroid.y, row.geometry.centroid.x],
        radius=3,
        color='green', # Bright Green
        fill=True,
        fill_opacity=1
    ).add_to(m)

folium.LayerControl().add_to(m)
m.save("Fixed_South_Map.html")
print("\nSUCCESS! Saved 'Fixed_South_Map.html'.")
print("Check the Console Output above to see if Florida/Virginia have chargers now.")


#%%

import geopandas as gpd
import pandas as pd
import folium
from folium import plugins
import os

# --- CONFIGURATION ---
TRACTS_FILE = "East_Coast_Model_Ready.geojson"
HIGHWAY_FILE = "East_Coast_Highways_Visual.gpkg"  # From Phase 4
OUTPUT_MAP = "East_Coast_Phase5_MasterMap.html"

print("--- PHASE 5 VISUALIZATION: MASTER LAYERS ---")

# 1. LOAD CENSUS TRACTS (The Base)
if not os.path.exists(TRACTS_FILE):
    print(f"CRITICAL ERROR: {TRACTS_FILE} not found.")
    exit()

print(f"1. Loading {TRACTS_FILE}...")
gdf = gpd.read_file(TRACTS_FILE)

# Reproject to EPSG:4326 (Lat/Lon) for Folium
if gdf.crs.to_string() != "EPSG:4326":
    print("   -> Reprojecting tracts to EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

# SIMPLIFICATION (The Crash Fix)
print("   -> Simplifying tract geometry (Tolerance: 0.001)...")
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)

# 2. INITIALIZE MAP
print("2. Initializing Map...")
# Center on the dataset
center_lat = gdf.geometry.centroid.y.mean()
center_lon = gdf.geometry.centroid.x.mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB positron")

# --- LAYER A: HIGHWAY SKELETON (Interactive) ---
print("3. Building Layer: Highway Network (with Labels)...")
if os.path.exists(HIGHWAY_FILE):
    # Load highway lines (edges)
    hwy_gdf = gpd.read_file(HIGHWAY_FILE, layer='edges')

    # Reproject
    if hwy_gdf.crs.to_string() != "EPSG:4326":
        hwy_gdf = hwy_gdf.to_crs(epsg=4326)

    # Clean missing names for the Tooltip
    if 'ref' not in hwy_gdf.columns:
        hwy_gdf['ref'] = "Hwy"  # Fallback if no name

    # Add to map
    folium.GeoJson(
        hwy_gdf,
        name="Interstate Skeleton",
        style_function=lambda x: {
            'color': 'black',
            'weight': 3,
            'opacity': 0.7
        },
        # THIS ENABLES THE HOVER LABEL
        tooltip=folium.GeoJsonTooltip(
            fields=['ref'],
            aliases=['Highway:'],
            sticky=True
        )
    ).add_to(m)
else:
    print(f"   [WARNING] {HIGHWAY_FILE} not found. Skipping highways.")

# --- LAYER B: DEMAND (Heatmap) ---
print("4. Building Layer: Demand (Population Heatmap)...")
# We use Population as a proxy for "Demand"
heat_data = []
# Filter for meaningful population to speed it up
pop_gdf = gdf[gdf['population'] > 100].copy()

for idx, row in pop_gdf.iterrows():
    lat = row.geometry.centroid.y
    lon = row.geometry.centroid.x
    weight = row['population']  # The "Heat" is the people
    heat_data.append([lat, lon, weight])

plugins.HeatMap(
    heat_data,
    name="Demand (Population Density)",
    radius=20,
    blur=15,
    gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'},
    overlay=True,
    control=True,
    show=False  # Default to OFF so map is clean on load
).add_to(m)

# --- LAYER C: CORRIDOR GAPS (Red Polygons) ---
print("5. Building Layer: Corridor Gaps (From Validation.py)...")
# Logic: < 1 mile from Hwy AND 0 Chargers
gaps_gdf = gdf[
    (gdf['dist_to_hwy_miles'] < 1.0) &
    (gdf['charger_count'] == 0)
    ]

folium.GeoJson(
    gaps_gdf,
    name="Corridor Gaps (Needs Chargers)",
    style_function=lambda x: {
        'fillColor': '#d32f2f',  # Dark Red
        'color': '#d32f2f',
        'weight': 1,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['dist_to_hwy_miles', 'population'],
        aliases=['Dist to Hwy (mi):', 'Population:'],
        localize=True
    )
).add_to(m)

# --- LAYER D: EQUITY PRIORITY (Blue Polygons) ---
print("6. Building Layer: Equity Priority...")
# Logic: Low Income (<$50k) AND 0 Chargers
equity_gdf = gdf[
    (gdf['median_income'] < 50000) &
    (gdf['charger_count'] == 0)
    ]

folium.GeoJson(
    equity_gdf,
    name="Equity Priority (Low Income)",
    style_function=lambda x: {
        'fillColor': '#1976D2',  # Blue
        'color': '#1976D2',
        'weight': 1,
        'fillOpacity': 0.5
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['median_income', 'population'],
        aliases=['Income ($):', 'Population:'],
        localize=True
    )
).add_to(m)

# --- LAYER E: EXISTING DC FAST CHARGERS (Points) ---
print("7. Building Layer: DC Fast Chargers...")
# Filter for tracts that actually have DC Fast chargers
fast_chargers = gdf[gdf['EV DC Fast Count'] > 0].copy()

# Create a FeatureGroup so we can toggle them on/off together
fg_chargers = folium.FeatureGroup(name="Existing DC Fast Chargers")

for idx, row in fast_chargers.iterrows():
    # We plot the centroid of the tract that contains the charger
    # (Since we joined points to polygons in Phase 3)
    folium.CircleMarker(
        location=[row.geometry.centroid.y, row.geometry.centroid.x],
        radius=4,
        color='green',
        fill=True,
        fill_color='#00E676',  # Bright Green
        fill_opacity=1.0,
        popup=f"DC Fast Count: {int(row['EV DC Fast Count'])}"
    ).add_to(fg_chargers)

fg_chargers.add_to(m)

# 8. SAVE
print("8. Saving Map...")
folium.LayerControl(collapsed=False).add_to(m)
m.save(OUTPUT_MAP)
print(f"SUCCESS! Map saved to {OUTPUT_MAP}")

