import geopandas as gpd
import pandas as pd
import pulp
import time

print("⚡ PHASE 6.2: SET COVERING LOCATION PROBLEM (Blanket) ⚡\n")
start_time = time.time()


print("Loading East Coast Dataset...")
gdf = gpd.read_file("East_Coast_Model_Ready.geojson")
gdf = gdf.to_crs("EPSG:5070")

candidates = gdf[(gdf['charger_count'] == 0) & (gdf['dist_to_hwy_miles'] <= 1.0)].copy()

# BUILD COVERAGE MATRIX
print("Building Spatial Coverage Matrix (5-Mile Radius)...")
COVERAGE_RADIUS_METERS = 8046.72
candidates['geometry_centroid'] = candidates.geometry.centroid
buffers = candidates.copy()
buffers['geometry'] = buffers['geometry_centroid'].buffer(COVERAGE_RADIUS_METERS)
candidates = candidates.set_geometry('geometry_centroid')

coverage_join = gpd.sjoin(candidates, buffers, how="inner", predicate="within", rsuffix="buffer")
coverage_map = coverage_join.groupby('GEOID_left')['GEOID_buffer'].apply(list).to_dict()

tracts = {}
for idx, row in candidates.iterrows():
    tracts[row['GEOID']] = {
        'geometry': row['geometry']
    }

candidates = candidates.set_geometry('geometry')

print("\nSolving SCLP for 100% Coverage...")
sclp = pulp.LpProblem("Blanket_SCLP", pulp.LpMinimize)

build_vars_s = pulp.LpVariable.dicts("Build_SCLP", tracts.keys(), cat='Binary')

# Objective: Minimize chargers built
sclp += pulp.lpSum([build_vars_s[i] for i in tracts.keys()])

# Constraint: Every single tract must have at least 1 charger nearby
for i in tracts.keys():
    potential_builders = coverage_map.get(i, [i])
    sclp += pulp.lpSum([build_vars_s[j] for j in potential_builders]) >= 1

sclp.solve(pulp.PULP_CBC_CMD(msg=0))

sclp_geoids = [i for i in tracts.keys() if build_vars_s[i].varValue == 1.0]
sclp_gdf = candidates[candidates['GEOID'].isin(sclp_geoids)].copy()

# Drop the centroid column before saving to GeoJSON
if 'geometry_centroid' in sclp_gdf.columns:
    sclp_gdf = sclp_gdf.drop(columns=['geometry_centroid'])

sclp_gdf = sclp_gdf.to_crs("EPSG:4326")
sclp_gdf.to_file("Optimized_SCLP_Blanket.geojson", driver="GeoJSON")

print(f"✅ Requires {len(sclp_geoids)} minimum stations to achieve 100% coverage.")
print(f"✅ Saved 'Optimized_SCLP_Blanket.geojson' in {time.time() - start_time:.2f}s")