import geopandas as gpd
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION ---

EV_FILE_NAME = "ev-registration-counts-by-state_9-06-24.xlsx"

# Check if file exists before crashing
if not os.path.exists(EV_FILE_NAME):
    print(f"\n[ERROR] Could not find '{EV_FILE_NAME}'")
    print(f"Python is looking in: {os.getcwd()}")
    print("FIX: Please copy the .xlsx file into this exact folder.")
    exit()

# --- 1. LOAD DATA ---

print("Loading Map Data...")
# This file must exist from Phase 3
map_file = "East_Coast_Supply_Analyzed.geojson"
if not os.path.exists(map_file):
    print(f"[ERROR] Could not find '{map_file}'. Did you run the Phase 3 script?")
    exit()

gdf = gpd.read_file(map_file)

print(f"Loading EV Registrations from {EV_FILE_NAME}...")
# Read Excel directly. header=2 means the 3rd row is the header.
ev_df = pd.read_excel(EV_FILE_NAME, header=2, engine='openpyxl')

# --- 2. CLEAN DATA ---

# The file likely has empty columns or footnotes.
# We explicitly select column 1 (State) and column 2 (Count).
# (Index 0 is usually the empty 'A' column in these formatted reports)
ev_df = ev_df.iloc[:, [1, 2]]
ev_df.columns = ['state_name', 'total_evs']

# Drop empty rows (e.g. at the end of the file)
ev_df = ev_df.dropna(subset=['state_name'])

# Dictionary to convert Full Names -> Abbreviations
us_state_to_abbrev = {
    "Alabama": "AL", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "New Hampshire": "NH", "New Jersey": "NJ", "New York": "NY", "North Carolina": "NC",
    "Ohio": "OH", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "Tennessee": "TN", "Vermont": "VT", "Virginia": "VA", "West Virginia": "WV"
}

# Create 'state_abbr' column
ev_df['state_abbr'] = ev_df['state_name'].map(us_state_to_abbrev)
# Drop states that aren't on your list (e.g., California)
ev_df = ev_df.dropna(subset=['state_abbr'])

print(f"Successfully loaded data for {len(ev_df)} East Coast states.")

# --- 3. THE ANALYSIS (Stress Ratio) ---

# Aggregate Chargers by State from your Map
state_supply = gdf.groupby('state_abbr')[['EV DC Fast Count', 'EV Level2 EVSE Num']].sum().reset_index()

# Merge Supply + Demand
stress_df = state_supply.merge(ev_df, on='state_abbr', how='inner')

# Calculate Metric: EVs per Fast Charger
stress_df['EVs_per_Fast_Charger'] = stress_df['total_evs'] / stress_df['EV DC Fast Count']
stress_df['EVs_per_Fast_Charger'] = stress_df['EVs_per_Fast_Charger'].replace([float('inf'), -float('inf')], 0)

# Print the Ranking
print("\n--- INFRASTRUCTURE STRESS RANKING (Higher is Worse) ---")
print(stress_df[['state_name', 'total_evs', 'EV DC Fast Count', 'EVs_per_Fast_Charger']]
      .sort_values(by='EVs_per_Fast_Charger', ascending=False)
      .to_string(index=False))

# --- 4. VISUALIZATION ---

plt.figure(figsize=(12, 6))
sns.barplot(
    x='state_abbr',
    y='EVs_per_Fast_Charger',
    data=stress_df.sort_values('EVs_per_Fast_Charger', ascending=False),
    palette='Reds_r'
)

plt.axhline(50, color='blue', linestyle='--', linewidth=2, label='Target Ratio (50:1)')
plt.title("Grid Stress: EVs per Fast Charger", fontsize=14)
plt.ylabel("EVs per Fast Charger")
plt.xlabel("State")
plt.legend()
plt.tight_layout()
plt.show()

#%%

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind

print("--- PHASE 5.9: EQUITY AUDIT (REFINED) ---")

# 1. LOAD DATA
print("1. Loading Data...")
tracts = gpd.read_file("East_Coast_Model_Ready.geojson")

# 2. STATISTICAL PROOF (Console Output)
print("\n--- THE HARD NUMBERS ---")

# Define Income Groups
tracts['Income_Group'] = pd.cut(
    tracts['median_income'],
    bins=[0, 40000, 80000, 120000, 10000000],
    labels=['Low (<40k)', 'Mid (40-80k)', 'High (80-120k)', 'Rich (>120k)']
)

# Calculate Stats
group_stats = tracts.groupby('Income_Group')['charger_count'].mean().reset_index()
print(group_stats.to_string(index=False))

# Calculate the "Wealth Gap" (Rich vs Low)
rich_avg = group_stats.iloc[3]['charger_count']
poor_avg = group_stats.iloc[0]['charger_count']
print(f"\nCONCLUSION: Wealthy areas have {rich_avg/poor_avg:.1f}x more chargers than poor areas.")

# 3. VISUALIZATION 1: THE BAR CHART (Infrastructure by Class)
print("\nOpening Chart 1: Infrastructure by Class...")
plt.figure(figsize=(10, 6))
sns.barplot(x='Income_Group', y='charger_count', data=group_stats, palette="viridis")
plt.title("Avg Chargers per Tract by Income", fontsize=14)
plt.ylabel("Average Number of Chargers")
plt.xlabel("Income Bracket")
plt.grid(axis='y', alpha=0.3)
plt.show() # This opens the window. Close it to continue.

# 4. VISUALIZATION 2: THE BOXPLOT (The Distribution)
print("Opening Chart 2: Income Distribution...")
plt.figure(figsize=(12, 6))
# Filter to 0-10 chargers to keep the chart readable
subset = tracts[tracts['charger_count'] <= 10]
sns.boxplot(x='charger_count', y='median_income', data=subset, palette="coolwarm")
plt.title("(Median Income vs Charger Count)", fontsize=14)
plt.xlabel("Number of Chargers in Tract")
plt.ylabel("Median Household Income ($)")
plt.grid(axis='y', alpha=0.3)
plt.show()


#%%

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

print("--- PHASE 5.9c: AVAILABLE EDA (NO DOWNLOADS) ---")

# 1. LOAD DATA
if not os.path.exists("East_Coast_Model_Ready.geojson"):
    print("ERROR: File not found.")
    exit()

print("1. Loading Census Tracts...")
tracts = gpd.read_file("East_Coast_Model_Ready.geojson")

# 2. GENERATE CHARTS
print("2. Generating Histograms...")
fig, ax = plt.subplots(1, 2, figsize=(18, 6))

# CHART A: INCOME HISTOGRAM (The Equity Reality)
# We filter out 0 or negative income for a clean chart
valid_income = tracts[tracts['median_income'] > 0]
sns.histplot(valid_income['median_income'], bins=50, kde=True, color='green', ax=ax[0])
ax[0].set_title("Income Distribution")
ax[0].set_xlabel("Median Household Income ($)")
# Add a vertical line for the average
avg_inc = valid_income['median_income'].mean()
ax[0].axvline(avg_inc, color='red', linestyle='--', label=f'Avg: ${avg_inc:,.0f}')
ax[0].legend()

# CHART B: HIGHWAY DISTANCE HISTOGRAM (The Corridor Reality)
# We limit to 20 miles to see the detail
sns.histplot(tracts['dist_to_hwy_miles'], bins=50, kde=True, color='blue', ax=ax[1])
ax[1].set_title("Distance to Interstate")
ax[1].set_xlabel("Distance (Miles)")
ax[1].set_xlim(0, 20)
# Add a line for our "1 Mile" threshold
ax[1].axvline(1.0, color='red', linestyle='--', label='Candidate Threshold (1 mi)')
ax[1].legend()

plt.tight_layout()
plt.show()

# 3. PRINT KEY STATS
print("\n--- KEY FINDINGS ---")
print(f"1. Average Income:       ${avg_inc:,.0f}")
print(f"2. Avg Dist to Highway:  {tracts['dist_to_hwy_miles'].mean():.1f} miles")
print(f"3. Corridor Candidates:  {len(tracts[tracts['dist_to_hwy_miles'] < 1.0])} tracts fit the '1-mile' rule.")
print("Done.")