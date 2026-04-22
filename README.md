# ⚡ Prescriptive Analytics for EV Infrastructure Placement
**An End-to-End Data Science, Spatial Analysis, & Prescriptive AI Pipeline for the US East Coast**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial_Data-success.svg)](https://geopandas.org/)
[![PuLP](https://img.shields.io/badge/PuLP-Linear_Programming-orange.svg)](https://coin-or.github.io/pulp/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live_App-FF4B4B.svg)](https://streamlit.io/)

## 📖 Executive Summary
As the transition to Electric Vehicles (EVs) accelerates, federal and state governments face a critical infrastructure challenge: **How do we deploy a limited budget of EV chargers to maximize commuter coverage while strictly enforcing social equity mandates?**

This project is a full-stack data science initiative that answers this question. Spanning from raw demographic and road network data extraction to the final mathematical deployment, this engine analyzes spatial data across the US East Coast to output mathematically proven, deployment-ready infrastructure portfolios.

## 🎯 The Business Problem
An independent audit of the current East Coast EV market, completed via dynamic Exploratory Data Analysis (EDA), revealed a severe spatial bias:
* **Total Existing Stations:** ~10,900
* **Equity Compliance:** Only ~17.2% of stations are located in low-income/Justice40 tracts.

Relying on the free market leaves millions of commuters and underserved communities behind. This project systematically maps the gaps and deploys **Prescriptive AI** to generate equitable, optimized solutions.

---

## 🚀 Project Architecture & Lifecycle

### Phase 1 & 2: Data Engineering & Feature Extraction
* **Data Ingestion:** Processed multi-modal datasets, including US Census demographic data (ACS), highway/road networks, and existing EV charging station coordinates.
* **Spatial Preprocessing:** Utilized `GeoPandas` to project data into consistent Coordinate Reference Systems (EPSG:5070 for Euclidean distance mathematics, EPSG:4326 for web mapping).
* **Feature Engineering:** Calculated distance-to-highway metrics, aggregated daily commuter volumes, and flagged Justice40 equity tracts per the federal mandate.

### Phase 3 & 4: Exploratory Data Analysis & Baseline Inspection
* Developed scripts for baseline inspection of data to identify existing spatial distributions and service deserts.
* Built dynamic filtering logic to isolate viable candidate tracts based on specific threshold criteria for commuter traffic, interstate proximity, and median income.

### Phase 5: Mutually Exclusive Suitability Dashboard
* **Web Deployment:** Developed a full-stack spatial web application using `Streamlit` and `Folium`.
* **Interactive UI:** Engineered a dynamic map that allows stakeholders to visually overlay unserved "Corridor Gaps" and Mutually Exclusive Deployment Portfolios (Market-Only, Equity-Only, Dual-Benefit) based on parameter sliders.
* **Performance:** Implemented marker clustering to render tens of thousands of geographic polygons and existing chargers flawlessly.

### Phase 6: Operations Research & Optimization AI
Translated policy constraints into systems of linear equations using Linear Programming (`PuLP`) and the IBM CBC MILP solver.

#### Model A: Capacitated MCLP (Prescriptive Deployment)
*The "Efficiency" Strategy: Maximize reach under strict budget and policy constraints.*
* **Objective:** Maximize commuters covered within 5 miles.
* **Hardware Constraints:** Implemented a unique hardware constraint where a single hub can support up to 5 multi-charger units, each catering to 5,000 commuters (5,000 Capacity per Charger).
* **Results:** With a micro-budget of only 100 units, the algorithm successfully forced equity compliance up to **40.0%** (meeting the Justice40 mandate) and strategically placed the 100 hubs to bring **9.76 Million unserved commuters** into the coverage network.

#### Model B: Set Covering Problem (Blanket Strategy)
*The "Zero-Gap Baseline" Strategy: Minimum viable infrastructure required to end range anxiety.*
* **Objective:** Minimize the total number of chargers built.
* **Constraints:** 100% of all unserved, highway-adjacent tracts must have at least one charger nearby.
* **Results:** Mathematically proved that a comprehensive, zero-gap network requires exactly **1,714 strategically placed hubs**.

---

## 🗂️ Repository Structure

```text
├── src/                                  # Application Logic & Scripts
│   ├── app.py                            # Streamlit dashboard & Folium mapping UI
│   ├── MCLP.py                           # 100-charger integer optimization script
│   ├── SCLP.py                           # 100% blanket coverage optimization script
│   ├── Validation.py                     # Independent spatial audit & metrics reporting
│   ├── Data_Cleaning.py                  # Raw data cleaning pipeline
│   ├── Data_merge.py                     # Merging demographic, traffic, and spatial data
│   └── EDA.py                            # Exploratory Data Analysis logic
├── data/                                 # Raw & Processed Datasets
│   ├── East_Coast_Model_Ready.geojson.zip # Compressed base spatial/census matrix
│   ├── East_Coast_Highways_Visual.gpkg.zip # Highway routing visual layer
│   ├── East_Coast_Data_Inspection.csv    # Post-EDA summary statistics
│   ├── alt_fuel_stations*.xlsx           # Raw charging station data
│   └── ev-registration-counts*.xlsx      # Raw EV registration data
├── outputs/                              # Mathematical Optimization Results
│   ├── Optimized_Phase6_Network.geojson  # Final MCLP (100 Hubs) output
│   └── Optimized_SCLP_Blanket.geojson    # Final SCLP (1,714 Hubs) output
├── README.md
└── requirements.txt                      # Project dependencies
```

## 🚀 How to Run Locally

To run the prescriptive dashboard on your machine, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Sarfarazzzzz/Optimizing-EV-Charging-Station-Placement.git](https://github.com/yourusername/Optimizing-EV-Charging-Station-Placement.git)
   cd Optimizing-EV-Charging-Station-Placement ```


2. **Install the required dependencies:**
  *This project requires Python 3.9 or higher. Install the necessary libraries by running:*
   ```bash
   pip install -r requirements.txt
   ```
*(Alternatively: pip install geopandas pandas pulp streamlit folium streamlit-folium pyarrow openpyxl)*

3. **Boot up the interactive dashboard:**
  *Launch the Streamlit server from the root directory:*
   ```bash
   streamlit run src/app.py
   ```

## 🌐 Live Application
The complete, interactive spatial dashboard is deployed and hosted via Streamlit Community Cloud. You can dynamically toggle between the Phase 5 base suitability analysis and the mathematically validated Phase 6 Optimization models (MCLP & SCLP) directly in your browser without installing any dependencies.

👉 [Access the Live Dashboard Here](https://optimizing-ev-charging-station-placement-using-data-driven.streamlit.app/)

Developed by Mohammed Ismail Sarfaraz Shaik | M.S. Data Science, The George Washington University
   
