import pandas as pd
import numpy as np
import xarray as xr
import os
import glob
import time
import warnings
from scipy import stats

# ================= CONFIGURATION =================
# Input Folders
FOLDER_LAND      = "era5_land_uk_2025"     # ERA5-Land
FOLDER_GLOBAL    = "era5_global_uk_2025"   # ERA5-Global
FOLDER_CAMS      = "cams_uk_2025"          # CAMS Data
CASES_FILE       = "EGS_cases_2025.csv"

# Output Files
OUTPUT_RATIO     = "ratio_analysis_results.csv"

# Suppress noisy warnings
warnings.filterwarnings("ignore")
# =================================================

def load_datasets():
    print("Indexing Weather & CAMS Data...")
    data_map = {}

    def scan(folder, tag):
        if not os.path.exists(folder): return
        files = glob.glob(os.path.join(folder, "*.nc"))
        for f in files:
            base = os.path.basename(f)
            parts = base.replace(".nc", "").split("_")
            key = None
            for i, p in enumerate(parts):
                if len(p)==4 and p.startswith("20") and p.isdigit():
                    if i+1 < len(parts) and parts[i+1].isdigit():
                        key = f"{p}-{parts[i+1]}"
                        break
            
            if key:
                if key not in data_map: data_map[key] = {}
                data_map[key][tag] = f

    scan(FOLDER_LAND, 'LAND')
    scan(FOLDER_GLOBAL, 'GLOBAL')
    scan(FOLDER_CAMS, 'CAMS')
    
    print(f"  Indexed {len(data_map)} months.")
    return data_map

def open_dataset(path):
    """
    Opens dataset and normalizes dimensions (valid_time/forecast_reference_time -> time).
    """
    try: ds = xr.open_dataset(path, engine='netcdf4')
    except: ds = xr.open_dataset(path, engine='scipy')

    renames = {}
    if 'lat' in ds.dims: renames['lat'] = 'latitude'
    if 'lon' in ds.dims: renames['lon'] = 'longitude'
    
    if 'time' not in ds.dims:
        if 'valid_time' in ds.dims: renames['valid_time'] = 'time'
        elif 'forecast_reference_time' in ds.dims: renames['forecast_reference_time'] = 'time'
            
    if renames: ds = ds.rename(renames)

    if 'forecast_period' in ds.dims:
        size = ds.sizes['forecast_period'] if hasattr(ds, 'sizes') else ds.dims['forecast_period']
        if size == 1: ds = ds.squeeze('forecast_period', drop=True)
        else: ds = ds.isel(forecast_period=0, drop=True)

    return ds

def detect_saddle_pattern(ds):
    u = ds['u10'] if 'u10' in ds else ds['10m_u_component_of_wind']
    v = ds['v10'] if 'v10' in ds else ds['10m_v_component_of_wind']
    degrees = (np.degrees(np.arctan2(v, u))) % 360
    speed = np.sqrt(u**2 + v**2)
    is_calm = speed <= 0.8 # Calm winds constraint

    d = 1
    deg_N, deg_S = degrees.shift(latitude=d), degrees.shift(latitude=-d)
    deg_E, deg_W = degrees.shift(longitude=-d), degrees.shift(longitude=d)
    deg_NE, deg_SW = degrees.shift(latitude=d, longitude=-d), degrees.shift(latitude=-d, longitude=d)
    deg_NW, deg_SE = degrees.shift(latitude=d, longitude=d), degrees.shift(latitude=-d, longitude=-d)

    def check_axis_flow(neigh1, angle_to_center1, neigh2, angle_to_center2, tol=90, opp_tol=45):
        def ang_dist(a, b): return np.abs((a - b + 180) % 360 - 180)
        n1_in = ang_dist(neigh1, angle_to_center1) <= tol
        n2_in = ang_dist(neigh2, angle_to_center2) <= tol
        deg_diff = ang_dist(neigh1, neigh2)
        is_opposing = np.abs(deg_diff - 180) <= opp_tol
        return (n1_in & n2_in & is_opposing)

    # Simplified detection for speed
    ns_conv = check_axis_flow(deg_N, 270, deg_S, 90)
    ew_conv = check_axis_flow(deg_E, 180, deg_W, 0)
    nesw_conv = check_axis_flow(deg_NE, 225, deg_SW, 45)
    nwse_conv = check_axis_flow(deg_NW, 315, deg_SE, 135)

    # Check for divergence on orthogonal axis implicitly or simplified saddle logic
    # For ratio analysis, we use the same events as before
    cardinal_saddle = (ns_conv) # Simplifying slightly to ensure we capture the convergence
    diagonal_saddle = (nesw_conv)

    return is_calm & (cardinal_saddle | diagonal_saddle)

def extract_events_and_ratios(ds, mask, source_name, cams_ds=None):
    if mask is None: return None, None
    events = mask.where(mask).stack(z=('time', 'latitude', 'longitude')).dropna(dim='z')
    if len(events) == 0: return None, None

    df = events.to_dataframe(name='Star_Event')
    for c in ['time', 'latitude', 'longitude']:
        if c in df.columns: df = df.drop(columns=[c])
    df = df.reset_index()
    
    # Store background samples
    bg_samples = {'PM25': [], 'PM10': []}

    # Extract CAMS Data (PM2.5 AND PM10)
    if cams_ds is not None:
        # Identify Variable Names
        pm25_var = next((v for v in ['pm2p5', 'particulate_matter_2.5um', 'pm25'] if v in cams_ds), None)
        pm10_var = next((v for v in ['pm10', 'particulate_matter_10um'] if v in cams_ds), None)
        
        if pm25_var and pm10_var:
            # 1. Get Background Samples (Random shuffling)
            v25 = cams_ds[pm25_var].values.flatten()
            v10 = cams_ds[pm10_var].values.flatten()
            
            # Remove NaNs
            valid_mask = ~np.isnan(v25) & ~np.isnan(v10)
            v25 = v25[valid_mask]
            v10 = v10[valid_mask]
            
            if len(v25) > 500:
                indices = np.random.choice(len(v25), 500, replace=False)
                bg_samples['PM25'] = v25[indices]
                bg_samples['PM10'] = v10[indices]
            
            # 2. Interpolate for Events
            try:
                tgt_x = xr.DataArray(df['longitude'].values.astype(np.float64), dims="z")
                tgt_y = xr.DataArray(df['latitude'].values.astype(np.float64), dims="z")
                tgt_t = xr.DataArray(df['time'].values, dims="z")
                
                df['PM25'] = cams_ds[pm25_var].interp(time=tgt_t, latitude=tgt_y, longitude=tgt_x, method='linear').values
                df['PM10'] = cams_ds[pm10_var].interp(time=tgt_t, latitude=tgt_y, longitude=tgt_x, method='linear').values
                
            except Exception as e:
                df['PM25'] = np.nan
                df['PM10'] = np.nan
        else:
            df['PM25'] = np.nan
            df['PM10'] = np.nan
    else:
        df['PM25'] = np.nan
        df['PM10'] = np.nan

    return df, bg_samples

def main():
    print("--- STEP 1: Analyzing PM2.5 / PM10 Ratios ---")
    data_map = load_datasets()

    all_events_list = []
    all_bg_pm25 = []
    all_bg_pm10 = []

    for key in sorted(data_map.keys()):
        sources = data_map[key]
        print(f"Processing {key}...", end="\r")
        
        ds_cams = None
        if 'CAMS' in sources: ds_cams = open_dataset(sources['CAMS'])
        
        # Only processing LAND for speed/relevance as EGS is land-based
        if 'LAND' in sources:
            ds = open_dataset(sources['LAND'])
            df, bg = extract_events_and_ratios(ds, detect_saddle_pattern(ds), 'LAND', ds_cams)
            if df is not None:
                all_events_list.append(df)
                all_bg_pm25.extend(bg['PM25'])
                all_bg_pm10.extend(bg['PM10'])

    if not all_events_list:
        print("\nNo events found.")
        return

    # --- COMPILE DATA ---
    events_df = pd.concat(all_events_list)
    events_df = events_df.dropna(subset=['PM25', 'PM10'])
    
    # Filter 1: Remove trivial zeros to avoid div/0
    events_df = events_df[events_df['PM10'] > 1e-9] 
    
    # Filter 2: Apply the "High PM2.5" Filter (The "Filtered Events" set)
    # We calculate the global background mean first
    bg_pm25_array = np.array(all_bg_pm25)
    bg_pm10_array = np.array(all_bg_pm10)
    
    bg_mean_pm25 = np.mean(bg_pm25_array)
    print(f"\nBackground Mean PM2.5: {bg_mean_pm25:.4e}")
    
    # Keep only events > Background Mean
    filtered_events = events_df[events_df['PM25'] > bg_mean_pm25].copy()
    print(f"Filtered Events Count: {len(filtered_events)}")

    # --- CALCULATE RATIOS ---
    # 1. Event Ratios
    filtered_events['Ratio'] = filtered_events['PM25'] / filtered_events['PM10']
    
    # 2. Background Ratios
    # We calculate ratio element-wise for the background samples
    # (handling small denominators)
    valid_bg = (bg_pm10_array > 1e-9)
    bg_ratios = bg_pm25_array[valid_bg] / bg_pm10_array[valid_bg]

    # --- STATISTICS ---
    mean_event_ratio = filtered_events['Ratio'].mean()
    mean_bg_ratio = np.mean(bg_ratios)
    
    std_event = filtered_events['Ratio'].std()
    std_bg = np.std(bg_ratios)

    # T-Test
    t_stat, p_val = stats.ttest_ind(filtered_events['Ratio'], bg_ratios, equal_var=False)

    print("\n" + "="*40)
    print("      PM2.5 / PM10 RATIO ANALYSIS      ")
    print("="*40)
    print(f"{'Group':<20} | {'Mean Ratio':<10} | {'Std Dev':<10}")
    print("-" * 45)
    print(f"{'Filtered Events':<20} | {mean_event_ratio:.4f}     | {std_event:.4f}")
    print(f"{'Background (Avg)':<20} | {mean_bg_ratio:.4f}     | {std_bg:.4f}")
    print("-" * 45)
    print(f"T-Statistic: {t_stat:.4f}")
    print(f"P-Value:     {p_val:.4e}")
    
    if p_val < 0.05:
        direction = "HIGHER" if mean_event_ratio > mean_bg_ratio else "LOWER"
        print(f"\nRESULT: Significant Difference! Events have a {direction} ratio.")
        if direction == "HIGHER":
            print("Interpretation: Events are enriched in FINE particles (Combustion/Secondary).")
        else:
            print("Interpretation: Events are enriched in COARSE particles (Dust/Soil).")
    else:
        print("\nRESULT: No significant difference in particle composition.")

    # Save
    filtered_events.to_csv(OUTPUT_RATIO, index=False)
    print(f"\nDetailed ratio data saved to {OUTPUT_RATIO}")

if __name__ == "__main__":
    main()