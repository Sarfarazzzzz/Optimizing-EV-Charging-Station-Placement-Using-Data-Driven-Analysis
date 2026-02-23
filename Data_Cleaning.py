import geopandas as gpd
import pandas as pd
import numpy as np
import os

print("--- MASTER FIX & INSPECT: FINALIZING DATASET ---")

# 1. LOAD DATA
file_path = "East_Coast_Model_Ready.geojson"
if not os.path.exists(file_path):
    print("ERROR: File not found. Please ensure 'East_Coast_Model_Ready.geojson' is in this folder.")
    exit()

print("Loading data...")
gdf = gpd.read_file(file_path)

# 2. FIX DATA TYPES & NEGATIVE VALUES (The "Repair")
print("Repairing data values...")
cols_numeric = ['median_income', 'population', 'commuters_total', 'dist_to_hwy_miles']

for col in cols_numeric:
    if col in gdf.columns:
        # Force numeric
        gdf[col] = pd.to_numeric(gdf[col], errors='coerce')

# Fix Negatives (Census Errors like -666666)
if 'median_income' in gdf.columns:
    gdf.loc[gdf['median_income'] < 0, 'median_income'] = np.nan
    # Impute missing income with State Median
    gdf['median_income'] = gdf.groupby('state_abbr')['median_income'].transform(lambda x: x.fillna(x.median()))

if 'population' in gdf.columns:
    gdf.loc[gdf['population'] < 0, 'population'] = 0

# 3. REGENERATE MISSING COLUMNS (The "KeyError" Fix)
print("Regenerating missing columns...")

# Ensure dist_to_hwy_miles exists (if not, we can't do much without running the geometry script again)
if 'dist_to_hwy_miles' not in gdf.columns:
    print("WARNING: 'dist_to_hwy_miles' missing. Setting to 999 (Far).")
    gdf['dist_to_hwy_miles'] = 999.0

# Re-create 'is_candidate'
# Rule: Pop > 100 OR Distance < 1 mile
gdf['is_candidate'] = (gdf['population'] > 100) | (gdf['dist_to_hwy_miles'] < 1.0)

# Re-create 'charger_count' (if missing)
if 'charger_count' not in gdf.columns:
    # Try to sum specific cols if they exist
    c1 = gdf['EV DC Fast Count'] if 'EV DC Fast Count' in gdf.columns else 0
    c2 = gdf['EV Level2 EVSE Num'] if 'EV Level2 EVSE Num' in gdf.columns else 0
    gdf['charger_count'] = c1 + c2

# 4. INSPECT THE DATA (What you wanted to see)
print("\n--- DATA SNAPSHOT (First 5 Rows) ---")
cols_to_show = ['state_abbr', 'median_income', 'population', 'dist_to_hwy_miles', 'charger_count', 'is_candidate']
# Only show columns that actually exist
valid_cols = [c for c in cols_to_show if c in gdf.columns]
df_view = pd.DataFrame(gdf.drop(columns='geometry'))
print(df_view[valid_cols].head().to_string(index=False))

print("\n--- STATISTICS (The Facts) ---")
print(f"Total Tracts:     {len(gdf)}")
print(f"Richness Range:   ${gdf['median_income'].min():,.0f} - ${gdf['median_income'].max():,.0f}")
print(f"Avg Dist to Hwy:  {gdf['dist_to_hwy_miles'].mean():.2f} miles")
print(f"Candidates Found: {gdf['is_candidate'].sum()}")

# 5. SAVE THE CLEANED FILE
gdf.to_file("East_Coast_Model_Ready.geojson", driver='GeoJSON')
print("\nSUCCESS! Saved corrected file. You are ready for Optimization.")

#%%

import geopandas as gpd
import pandas as pd
import os

print("--- DATA INSPECTION: OPENING THE BLACK BOX ---")

# 1. Load the file
file_path = "East_Coast_Model_Ready.geojson"
if not os.path.exists(file_path):
    print("ERROR: File not found.")
    exit()

print("Loading data...")
gdf = gpd.read_file(file_path)

# 2. Drop the 'geometry' column (The map shapes) so we can look at just the numbers
# We create a simple DataFrame (Table)
df = pd.DataFrame(gdf.drop(columns='geometry'))

# 3. PRINT THE ACTUAL DATA (First 5 Rows)
print("\n--- SAMPLE DATA (First 5 Census Tracts) ---")
# We select the most important columns to show you
cols_to_show = ['state_abbr', 'median_income', 'population', 'commuters_total', 'dist_to_hwy_miles', 'charger_count', 'is_candidate']
print(df[cols_to_show].head().to_string(index=False))

# 4. PRINT THE "EXTREMES" (Best vs Worst)
print("\n\n--- THE EXTREMES (Data Range) ---")
print(f"Richest Tract:   ${df['median_income'].max():,.0f} (Income)")
print(f"Poorest Tract:   ${df['median_income'].min():,.0f} (Income)")
print(f"Most Crowded:    {df['population'].max():,.0f} people")
print(f"Closest to Hwy:  {df['dist_to_hwy_miles'].min():.2f} miles")
print(f"Farthest fr Hwy: {df['dist_to_hwy_miles'].max():.2f} miles")

# 5. SAVE TO CSV (So you can open in Excel)
csv_filename = "East_Coast_Data_Inspection.csv"
df.to_csv(csv_filename, index=False)
print(f"\n\nSUCCESS! Saved full dataset to '{csv_filename}'.")
print("-> Open this file in Excel to see every single row of data we collected.")

