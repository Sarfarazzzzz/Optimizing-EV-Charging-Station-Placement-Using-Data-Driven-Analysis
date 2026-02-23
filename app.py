import zipfile
import tempfile
import streamlit as st
import geopandas as gpd
import folium
from folium import plugins
import streamlit.components.v1 as components
import os

st.set_page_config(layout="wide", page_title="EV Suitability Analysis")

st.title("⚡ Phase 5: Multi-Criteria Suitability Analysis")
st.markdown("Analyzing Base Layers and Mutually Exclusive Deployment Portfolios.")


@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = tempfile.gettempdir()  # Streamlit's safe temporary folder

    tracts_zip = os.path.join(base_dir, "East_Coast_Model_Ready.zip")
    hwy_zip = os.path.join(base_dir, "East_Coast_Highways_Visual.zip")

    # HELPER: Unzips the file safely, ignores __MACOSX, and returns the physical file path
    def extract_target_file(zip_path, extension):
        if not os.path.exists(zip_path):
            return None
        with zipfile.ZipFile(zip_path, 'r') as z:
            for file_name in z.namelist():
                # Find our file and ignore Apple's hidden folders
                if file_name.endswith(extension) and '__MACOSX' not in file_name:
                    z.extract(file_name, temp_dir)
                    return os.path.join(temp_dir, file_name)
        return None

    # 1. Extract and Read Tracts
    tracts_file = extract_target_file(tracts_zip, '.geojson')
    if not tracts_file:
        st.error("Error: Could not extract the tracts .geojson file from the zip archive.")
        st.stop()

    gdf = gpd.read_file(tracts_file)
    if gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

    # 2. Extract and Read Highways
    hwy_gdf = None
    hwy_file = extract_target_file(hwy_zip, '.gpkg')

    if hwy_file:
        try:
            hwy_gdf = gpd.read_file(hwy_file, layer='edges')
            if hwy_gdf.crs.to_string() != "EPSG:4326":
                hwy_gdf = hwy_gdf.to_crs(epsg=4326)
            hwy_gdf['geometry'] = hwy_gdf['geometry'].simplify(tolerance=0.005)
            if 'ref' not in hwy_gdf.columns:
                hwy_gdf['ref'] = "Hwy"
        except Exception as e:
            print(f"Skipping highways for now: {e}")

    return gdf, hwy_gdf

with st.spinner("Loading spatial data and highway networks..."):
    gdf, hwy_gdf = load_data()

# --- SIDEBAR: CONTROLS & TOGGLES ---
st.sidebar.header("🎯 Target Thresholds")
max_dist = st.sidebar.slider("Corridor (Max Miles to Hwy)", 0.5, 5.0, 1.0, step=0.5)
max_inc = st.sidebar.slider("Equity (Max Median Income)", 20000, 100000, 50000, step=5000)
min_commuters = st.sidebar.slider("Demand (Min Daily Commuters)", 0, 5000, 1000, step=250)

st.sidebar.markdown("### 🛠️ Analysis Layers (Base Data)")
show_corridor = st.sidebar.checkbox("Show All Corridor Gaps (Red)", value=False)
show_equity = st.sidebar.checkbox("Show All Equity Tracts (Blue)", value=False)
show_demand = st.sidebar.checkbox("Show All High Demand (Yellow)", value=False)

st.sidebar.markdown("### 🚀 Deployment Portfolios")
show_market = st.sidebar.checkbox("Show Market Only (Orange)", value=True)
show_equity_port = st.sidebar.checkbox("Show Equity Only (Purple)", value=True)
show_dual = st.sidebar.checkbox("Show Dual-Benefit (Teal)", value=True)

st.sidebar.markdown("### 🛣️ Infrastructure Layers")
show_highways = st.sidebar.checkbox("Show Highways & Labels", value=True)
show_chargers = st.sidebar.checkbox("Show Existing DC Fast Chargers", value=True)

# --- LAYER MATH ---
unserved = gdf[gdf['charger_count'] == 0]

mask_corridor = unserved['dist_to_hwy_miles'] <= max_dist
mask_equity = unserved['median_income'] <= max_inc
mask_demand = unserved['commuters_total'] >= min_commuters

# 1. Base Analysis Groups
base_corridor = unserved[mask_corridor]
base_equity = unserved[mask_equity]
base_demand = unserved[mask_demand]

# 2. Mutually Exclusive Portfolios (Fixes the color blending)
market_only = unserved[mask_corridor & mask_demand & ~mask_equity]
equity_only = unserved[mask_corridor & mask_equity & ~mask_demand]
dual_targets = unserved[mask_corridor & mask_demand & mask_equity]

# --- METRICS UI ---
st.markdown("#### Database Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Tracts Examined", f"{len(gdf):,}")
c2.metric("Total Unserved (0 Chargers)", f"{len(unserved):,}")
c3.metric("Raw Equity Tracts", f"{len(base_equity):,}")
c4.metric("Raw Demand Tracts", f"{len(base_demand):,}")

st.markdown("#### Strategic Portfolios (Corridor + Criteria)")
c5, c6, c7 = st.columns(3)
c5.metric("📈 Market Only", f"{len(market_only):,}")
c6.metric("⚖️ Equity Only", f"{len(equity_only):,}")
c7.metric("⭐ Dual-Benefit", f"{len(dual_targets):,}")

# --- BUILD MAP ---
center_lat, center_lon = gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB positron", prefer_canvas=True)

cols_to_keep = ['dist_to_hwy_miles', 'median_income', 'commuters_total', 'geometry']

# A. Base Analysis Layers
if show_corridor and not base_corridor.empty:
    folium.GeoJson(base_corridor[cols_to_keep], name="All Corridor Gaps",
        style_function=lambda x: {'fillColor': '#FF0000', 'stroke': False, 'fillOpacity': 0.3},
        tooltip=folium.GeoJsonTooltip(fields=['dist_to_hwy_miles'], aliases=['Hwy Dist:'])).add_to(m)

if show_equity and not base_equity.empty:
    folium.GeoJson(base_equity[cols_to_keep], name="All Equity Tracts",
        style_function=lambda x: {'fillColor': '#0000FF', 'stroke': False, 'fillOpacity': 0.3},
        tooltip=folium.GeoJsonTooltip(fields=['median_income'], aliases=['Income:'])).add_to(m)

if show_demand and not base_demand.empty:
    folium.GeoJson(base_demand[cols_to_keep], name="All Demand Tracts",
        style_function=lambda x: {'fillColor': '#FFD700', 'stroke': False, 'fillOpacity': 0.3},
        tooltip=folium.GeoJsonTooltip(fields=['commuters_total'], aliases=['Commuters:'])).add_to(m)

# B. Mutually Exclusive Portfolios
if show_market and not market_only.empty:
    folium.GeoJson(market_only[cols_to_keep], name="Market Only",
        style_function=lambda x: {'fillColor': '#FF8C00', 'stroke': False, 'fillOpacity': 0.8},
        tooltip=folium.GeoJsonTooltip(fields=['dist_to_hwy_miles', 'commuters_total'], aliases=['Hwy Dist:', 'Commuters:'])).add_to(m)

if show_equity_port and not equity_only.empty:
    folium.GeoJson(equity_only[cols_to_keep], name="Equity Only",
        style_function=lambda x: {'fillColor': '#800080', 'stroke': False, 'fillOpacity': 0.8},
        tooltip=folium.GeoJsonTooltip(fields=['dist_to_hwy_miles', 'median_income'], aliases=['Hwy Dist:', 'Income:'])).add_to(m)

if show_dual and not dual_targets.empty:
    folium.GeoJson(dual_targets[cols_to_keep], name="Dual-Benefit",
        style_function=lambda x: {'fillColor': '#008080', 'stroke': False, 'fillOpacity': 0.8},
        tooltip=folium.GeoJsonTooltip(fields=['dist_to_hwy_miles', 'median_income', 'commuters_total'], aliases=['Hwy Dist:', 'Income:', 'Commuters:'])).add_to(m)

# C. Infrastructure Layers
if show_highways and hwy_gdf is not None:
    folium.GeoJson(hwy_gdf[['ref', 'geometry']], name="Interstates",
        style_function=lambda x: {'color': 'black', 'weight': 2, 'opacity': 0.6},
        tooltip=folium.GeoJsonTooltip(fields=['ref'], aliases=['Highway:'], sticky=True)).add_to(m)

if show_chargers:
    chargers = gdf[gdf['EV DC Fast Count'] > 0]
    mc = plugins.MarkerCluster(name="Existing DC Fast Chargers")
    for idx, row in chargers.iterrows():
        icon = folium.Icon(color='green', icon='bolt', prefix='fa')
        folium.Marker(
            location=[row.geometry.centroid.y, row.geometry.centroid.x],
            icon=icon, popup=f"Stations: {int(row['EV DC Fast Count'])}"
        ).add_to(mc)
    mc.add_to(m)

st.markdown("<br>", unsafe_allow_html=True)
components.html(m.get_root().render(), height=650)