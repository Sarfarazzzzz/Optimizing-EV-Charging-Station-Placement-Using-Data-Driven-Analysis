import geopandas as gpd
import pandas as pd
import pulp
import time

print("⚡ PHASE 6: MAXIMAL COVERING LOCATION PROBLEM (MCLP) ⚡\n")
start_time = time.time()

print("1. Loading East Coast Dataset...")
gdf = gpd.read_file("East_Coast_Model_Ready.geojson")

# Project to Albers Equal Area (Meters) for accurate distance math
gdf = gdf.to_crs("EPSG:5070")

# Filter for Unserved Candidates to save processing power
candidates = gdf[(gdf['charger_count'] == 0) & (gdf['dist_to_hwy_miles'] <= 1.0)].copy()

print(f" -> Found {len(candidates)} viable candidate tracts.")

# BUILD THE COVERAGE MATRIX
print("\n2. Building Spatial Coverage Matrix (5-Mile Radius)...")
# 5 miles = 8046.72 meters
COVERAGE_RADIUS_METERS = 8046.72

# Convert polygons to center points
candidates['geometry'] = candidates.geometry.centroid

# Buffer every point by 5 miles
buffers = candidates.copy()
buffers['geometry'] = buffers.geometry.buffer(COVERAGE_RADIUS_METERS)

# Intersect the buffers with the original points to see who covers who
coverage_join = gpd.sjoin(candidates, buffers, how="inner", predicate="within", rsuffix="buffer")

# Build the dictionary mapping: Tract ID -> [List of covered Tract IDs]
coverage_map = coverage_join.groupby('GEOID_left')['GEOID_buffer'].apply(list).to_dict()

print(" -> Matrix built successfully.")

print("\n3. Initializing Linear Programming Engine...")

# Create the tract data dictionary
tracts = {}
for idx, row in candidates.iterrows():
    tracts[row['GEOID']] = {
        'demand': row['commuters_total'],
        'is_equity': True if row['median_income'] <= 50000 else False,
        'geometry': row['geometry']
    }

# POLICY CONSTRAINTS HERE
BUDGET_MAX_CHARGERS = 100
JUSTICE40_PERCENT = 0.40  # 40% must be equity
MIN_EQUITY_CHARGERS = int(BUDGET_MAX_CHARGERS * JUSTICE40_PERCENT)

# Set a capacity limit per charger
CAPACITY_PER_CHARGER = 5000

print(f" -> Constraint 1: Build exactly {BUDGET_MAX_CHARGERS} chargers.")
print(f" -> Constraint 2: At least {MIN_EQUITY_CHARGERS} must be in Equity Priority tracts.")

print("\n4. Solving for Absolute Maximum Coverage...")

model = pulp.LpProblem("East_Coast_EV_MCLP", pulp.LpMaximize)

# Variables are Integers (up to 5) instead of Binary
build_vars = pulp.LpVariable.dicts("Build", tracts.keys(), lowBound=0, upBound=5, cat='Integer')
covered_vars = pulp.LpVariable.dicts("Covered", tracts.keys(), cat='Binary')

# Objective: Maximize Commuters
model += pulp.lpSum([tracts[i]['demand'] * covered_vars[i] for i in tracts.keys()]), "Maximize_Commuters"

# Constraint 1: Budget Limit
model += pulp.lpSum([build_vars[i] for i in tracts.keys()]) == BUDGET_MAX_CHARGERS, "Budget_Limit"

# Constraint 2: Equity Mandate
equity_tracts = [i for i, data in tracts.items() if data['is_equity']]
model += pulp.lpSum([build_vars[i] for i in equity_tracts]) >= MIN_EQUITY_CHARGERS, "Equity_Mandate"

# Constraint 3: Coverage Logic
for i in tracts.keys():
    # If a tract has no neighbors in the matrix, it can only cover itself
    potential_builders = coverage_map.get(i, [i])
    model += tracts[i]['demand'] * covered_vars[i] <= CAPACITY_PER_CHARGER * pulp.lpSum([build_vars[j] for j in potential_builders]), f"Cov_Logic_{i}"

# Run the solver (Zero timers added)
model.solve(pulp.PULP_CBC_CMD(msg=0))

print(f" -> Algorithm Status: {pulp.LpStatus[model.status]}")

print("\n5. Extracting Optimized Network...")

# Create a dictionary that actually saves the specific number of chargers built
charger_counts = {i: int(build_vars[i].varValue) for i in tracts.keys() if build_vars[i].varValue is not None and build_vars[i].varValue > 0}

# Filter the original candidates to just the winners
optimized_gdf = candidates[candidates['GEOID'].isin(charger_counts.keys())].copy()

#  Map those counts directly into a new column so Streamlit can read it
optimized_gdf['chargers_assigned'] = optimized_gdf['GEOID'].map(charger_counts)

# Calculate totals for the report
total_demand_met = sum(tracts[i]['demand'] for i in tracts.keys() if covered_vars[i].varValue == 1.0)
equity_built = sum(build_vars[i].varValue for i in charger_counts.keys() if tracts[i]['is_equity'])

print("\n OPTIMIZATION RESULTS")
print(f"Unique Hub Locations: {len(charger_counts)}")
print(f"Equity Targets Hit:   {int(equity_built)} ({(equity_built/BUDGET_MAX_CHARGERS)*100:.1f}%)")
print(f"Commuters Covered:    {total_demand_met:,.0f} people")
print(f"Processing Time:      {time.time() - start_time:.2f} seconds")

optimized_gdf = optimized_gdf.to_crs("EPSG:4326")
optimized_gdf.to_file("Optimized_Phase6_Network.geojson", driver="GeoJSON")

print("\nSUCCESS: Saved 'Optimized_Phase6_Network.geojson' with capacity counts!")