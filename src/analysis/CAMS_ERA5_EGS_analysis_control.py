
import pandas as pd
import numpy as np
import xarray as xr
import os
import glob
import time
import warnings

# ================= CONFIGURATION =================
# Input Folders
FOLDER_LAND      = "era5_land_uk_2025"     # ERA5-Land
FOLDER_GLOBAL    = "era5_global_uk_2025"   # ERA5-Global
FOLDER_CAMS      = "cams_uk_2025"          # CAMS Data
CASES_FILE       = "EGS_cases_2025_control.csv"

# Output Files
OUTPUT_CORR      = "correlations_filtered_control.csv"
OUTPUT_GRID      = "grid_search_filtered_control.csv"
OUTPUT_STATS     = "stats_filtered_control.csv"

# Grid Search Ranges
DISTANCE_RANGE = range(5, 51, 5)
DAYS_RANGE     = range(5, 91, 5)

# Fixed Constraints for Final Output
FINAL_MAX_DIST = 50
FINAL_DAYS_MAX = 90
# =================================================

# Suppress noisy warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

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
    
    # 1. Normalize Latitude/Longitude
    if 'lat' in ds.dims: renames['lat'] = 'latitude'
    if 'lon' in ds.dims: renames['lon'] = 'longitude'
    
    # 2. Normalize Time
    if 'time' not in ds.dims:
        if 'valid_time' in ds.dims:
            renames['valid_time'] = 'time'
        elif 'forecast_reference_time' in ds.dims:
            renames['forecast_reference_time'] = 'time'
            
    if renames: ds = ds.rename(renames)

    # 3. Handle 'forecast_period' if it exists
    if 'forecast_period' in ds.dims:
        # Check size safely
        size = ds.sizes['forecast_period'] if hasattr(ds, 'sizes') else ds.dims['forecast_period']
        if size == 1:
            ds = ds.squeeze('forecast_period', drop=True)
        else:
            ds = ds.isel(forecast_period=0, drop=True)

    return ds

def detect_saddle_pattern(ds):
    u = ds['u10'] if 'u10' in ds else ds['10m_u_component_of_wind']
    v = ds['v10'] if 'v10' in ds else ds['10m_v_component_of_wind']
    
    degrees = (np.degrees(np.arctan2(v, u))) % 360
    speed = np.sqrt(u**2 + v**2)
    is_calm = speed <= 0.8

    d = 1
    deg_N = degrees.shift(latitude=d)
    deg_S = degrees.shift(latitude=-d)
    deg_E = degrees.shift(longitude=-d)
    deg_W = degrees.shift(longitude=d)
    
    deg_NE = degrees.shift(latitude=d, longitude=-d)
    deg_SW = degrees.shift(latitude=-d, longitude=d)
    deg_NW = degrees.shift(latitude=d, longitude=d)
    deg_SE = degrees.shift(latitude=-d, longitude=-d)

    def check_axis_flow(neigh1, angle_to_center1, neigh2, angle_to_center2, tol=90, opp_tol=45):
        def ang_dist(a, b):
            return np.abs((a - b + 180) % 360 - 180)

        n1_in = ang_dist(neigh1, angle_to_center1) <= tol
        n2_in = ang_dist(neigh2, angle_to_center2) <= tol
        n1_out = ang_dist(neigh1, angle_to_center1 + 180) <= tol
        n2_out = ang_dist(neigh2, angle_to_center2 + 180) <= tol

        deg_diff = ang_dist(neigh1, neigh2)
        is_opposing = np.abs(deg_diff - 180) <= opp_tol

        is_conv = n1_in & n2_in & is_opposing
        is_div  = n1_out & n2_out & is_opposing
        return is_conv, is_div

    ns_conv, ns_div = check_axis_flow(deg_N, 270, deg_S, 90)
    ew_conv, ew_div = check_axis_flow(deg_E, 180, deg_W, 0)
    nesw_conv, nesw_div = check_axis_flow(deg_NE, 225, deg_SW, 45)
    nwse_conv, nwse_div = check_axis_flow(deg_NW, 315, deg_SE, 135)

    cardinal_saddle = (ns_conv & ew_div) | (ns_div & ew_conv)
    diagonal_saddle = (nesw_conv & nwse_div) | (nesw_div & nwse_conv)

    return is_calm & (cardinal_saddle | diagonal_saddle)

def extract_events_and_stats(ds, mask, source_name, cams_ds=None):
    if mask is None: return None, None
    events = mask.where(mask).stack(z=('time', 'latitude', 'longitude')).dropna(dim='z')
    if len(events) == 0: return None, None

    df = events.to_dataframe(name='Star_Event')
    for c in ['time', 'latitude', 'longitude']:
        if c in df.columns: df = df.drop(columns=[c])
    df = df.reset_index()
    df['Source_Dataset'] = source_name

    # Extract Temp/Dew/Press
    t_var = 't2m' if 't2m' in ds else '2m_temperature'
    d_var = 'd2m' if 'd2m' in ds else '2m_dewpoint_temperature'
    p_var = 'sp' if 'sp' in ds else 'surface_pressure'

    stats_bg = {'Temp': [], 'Dew': [], 'Press': [], 'PM25': []}

    def get_bg(dset, var_name, is_kelvin=False, is_pa=False):
        if var_name not in dset: return []
        vals = dset[var_name].values.flatten()
        vals = vals[~np.isnan(vals)]
        if len(vals) > 500: np.random.shuffle(vals)
        subset = vals[:500]
        if is_kelvin: subset = subset - 273.15
        if is_pa: subset = subset / 100.0
        return subset

    if t_var in ds:
        vals = ds[t_var].where(mask).stack(z=('time', 'latitude', 'longitude')).dropna(dim='z').values - 273.15
        df['Temp'] = vals
        stats_bg['Temp'] = get_bg(ds, t_var, is_kelvin=True)
    else: df['Temp'] = np.nan

    if d_var in ds:
        vals = ds[d_var].where(mask).stack(z=('time', 'latitude', 'longitude')).dropna(dim='z').values - 273.15
        df['Dew'] = vals
        stats_bg['Dew'] = get_bg(ds, d_var, is_kelvin=True)
    else: df['Dew'] = np.nan

    if p_var in ds:
        vals = ds[p_var].where(mask).stack(z=('time', 'latitude', 'longitude')).dropna(dim='z').values / 100.0
        df['Press'] = vals
        stats_bg['Press'] = get_bg(ds, p_var, is_pa=True)
    else: df['Press'] = np.nan

    # --- CAMS PM2.5 Extraction ---
    if cams_ds is not None:
        pm_var = None
        for v in ['pm2p5', 'particulate_matter_2.5um', 'pm25']:
            if v in cams_ds:
                pm_var = v
                break
        
        if pm_var:
            stats_bg['PM25'] = get_bg(cams_ds, pm_var)
            
            try:
                # Ensure coordinates are float64 for interpolation safety
                tgt_x = xr.DataArray(df['longitude'].values.astype(np.float64), dims="z")
                tgt_y = xr.DataArray(df['latitude'].values.astype(np.float64), dims="z")
                tgt_t = xr.DataArray(df['time'].values, dims="z")
                
                # Perform Interpolation - REMOVED EXTRAPOLATE KWARG
                pm_vals = cams_ds[pm_var].interp(
                    time=tgt_t, 
                    latitude=tgt_y, 
                    longitude=tgt_x, 
                    method='linear'
                ).values
                
                df['PM25'] = pm_vals
            except Exception as e:
                print(f"Warning: PM2.5 interp failed for {source_name}: {e}")
                df['PM25'] = np.nan
        else:
            df['PM25'] = np.nan
    else:
        df['PM25'] = np.nan

    return df, stats_bg

def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def run_grid_search(all_events, cases):
    print(f"\n--- Starting Grid Search ({len(DISTANCE_RANGE) * len(DAYS_RANGE)} combinations) ---")
    results = []
    for max_dist in DISTANCE_RANGE:
        for max_days in DAYS_RANGE:
            match_count = 0
            for _, case in cases.iterrows():
                start = case['Date'] - pd.Timedelta(days=max_days)
                end = case['Date'] - pd.Timedelta(days=1)
                subset = all_events[(all_events['time'] >= start) & (all_events['time'] <= end)]
                if subset.empty: continue
                dists = haversine_np(case['Latitude'], case['Longitude'], subset['latitude'].values, subset['longitude'].values)
                if np.any(dists <= max_dist): match_count += 1
            pct = (match_count / len(cases)) * 100
            print(f"{max_dist:<5}km | {max_days:<3}d | {pct:.1f}%")
            results.append({'Distance': max_dist, 'Days': max_days, 'Matches': match_count, 'Percent': pct})
    pd.DataFrame(results).to_csv(OUTPUT_GRID, index=False)

def generate_detailed_matches(all_events, cases, max_dist, max_days):
    print(f"\n--- Generating Detailed Matches ({max_dist}km, {max_days} days) ---")
    matches = []
    for i, case in cases.iterrows():
        start = case['Date'] - pd.Timedelta(days=max_days)
        end = case['Date'] - pd.Timedelta(days=1)
        subset = all_events[(all_events['time'] >= start) & (all_events['time'] <= end)]
        if subset.empty: continue
        dists = haversine_np(case['Latitude'], case['Longitude'], subset['latitude'].values, subset['longitude'].values)
        valid_indices = np.where(dists <= max_dist)[0]
        if len(valid_indices) > 0:
            valid_events = subset.iloc[valid_indices].copy()
            valid_events['Case_ID'] = i
            valid_events['Case_Date'] = case['Date']
            valid_events['Days_Prior'] = (case['Date'] - valid_events['time']).dt.days
            valid_events['Distance_km'] = dists[valid_indices]
            matches.append(valid_events)

    if matches:
        final_corr = pd.concat(matches)
        if 'lat_round' in final_corr.columns: final_corr = final_corr.drop(columns=['lat_round', 'lon_round'])
        final_corr.to_csv(OUTPUT_CORR, index=False)
        return final_corr
    return None

def main():
    print("--- STEP 1: Event Detection with PM2.5 Filter (V9 - Clean) ---")
    data_map = load_datasets()

    try: cases = pd.read_csv(CASES_FILE)
    except: cases = pd.read_csv(CASES_FILE, encoding='latin1')
    
    col_map = {'date': 'Date', 'presented': 'Date', 'lat': 'Latitude', 'lon': 'Longitude'}
    new_cols = {}
    for c in cases.columns:
        if c.lower() in col_map: new_cols[c] = col_map[c.lower()]
    cases.rename(columns=new_cols, inplace=True)
    cases['Date'] = pd.to_datetime(cases['Date'], dayfirst=True, errors='coerce', format='mixed')
    cases = cases.dropna(subset=['Date', 'Latitude', 'Longitude'])
    print(f"Loaded {len(cases)} valid cases.")

    all_events_list = []
    bg_stats_list = {'Temp': [], 'Dew': [], 'Press': [], 'PM25': []}

    for key in sorted(data_map.keys()):
        sources = data_map[key]
        print(f"Processing {key}...", end="\r")
        
        # Load CAMS
        ds_cams = None
        if 'CAMS' in sources:
            ds_cams = open_dataset(sources['CAMS'])
        
        month_dfs = []
        if 'LAND' in sources:
            ds = open_dataset(sources['LAND'])
            df, stats = extract_events_and_stats(ds, detect_saddle_pattern(ds), 'LAND', ds_cams)
            if df is not None:
                month_dfs.append(df)
                for k, v in stats.items(): bg_stats_list[k].extend(v)
        
        if 'GLOBAL' in sources:
            ds = open_dataset(sources['GLOBAL'])
            df, stats = extract_events_and_stats(ds, detect_saddle_pattern(ds), 'GLOBAL', ds_cams)
            if df is not None: month_dfs.append(df)

        if month_dfs:
            full_df = pd.concat(month_dfs)
            full_df['lat_round'] = full_df['latitude'].round(1)
            full_df['lon_round'] = full_df['longitude'].round(1)
            full_df = full_df.sort_values(by='Source_Dataset')
            full_df = full_df.drop_duplicates(subset=['time', 'lat_round', 'lon_round'], keep='first')
            all_events_list.append(full_df)

    if not all_events_list:
        print("\nNo events found.")
        return

    master_events = pd.concat(all_events_list)
    print(f"\nTotal Detected Star Patterns (Raw): {len(master_events)}")

    # --- FILTERING BY PM2.5 ---
    if len(bg_stats_list['PM25']) > 0:
        pm_mean = np.mean(bg_stats_list['PM25'])
        pm_std = np.std(bg_stats_list['PM25'])
        print(f"\nPM2.5 Statistics (Background): Mean={pm_mean:.4e}, Std={pm_std:.4e}")
        
        before_count = len(master_events)
        
        # Drop rows where PM25 is NaN (failed interp) before filtering
        valid_pm = master_events.dropna(subset=['PM25'])
        
        # Apply Filter (Keep only High PM2.5 Events)
        master_events = valid_pm[valid_pm['PM25'] > pm_mean]
        after_count = len(master_events)
        
        print(f"Filter Applied: Removed {before_count - after_count} events (Low PM2.5 or Missing Data).")
        print(f"Remaining Events: {after_count}")
    else:
        print("\nWarning: No PM2.5 data found to filter with. Proceeding with raw events.")

    if len(master_events) == 0:
        print("No events left after filtering.")
        return

    # 2. GRID SEARCH
    run_grid_search(master_events, cases)

    # 3. DETAILED OUTPUT
    final_corr = generate_detailed_matches(master_events, cases, FINAL_MAX_DIST, FINAL_DAYS_MAX)

    # 4. STATS
    print("\n--- STEP 4: Bio-Reactor Stats ---")
    if final_corr is not None:
        stats_rows = []
        for var in ['Temp', 'Dew', 'Press', 'PM25']:
            ev_vals = final_corr[var].dropna()
            bg_vals = bg_stats_list[var]
            if len(ev_vals) > 0 and len(bg_vals) > 0:
                stats_rows.append({'Variable': var, 'Group': 'Filtered Events', 'Mean': np.mean(ev_vals), 'StdDev': np.std(ev_vals)})
                stats_rows.append({'Variable': var, 'Group': 'Background', 'Mean': np.mean(bg_vals), 'StdDev': np.std(bg_vals)})
        pd.DataFrame(stats_rows).to_csv(OUTPUT_STATS, index=False)
        print(pd.DataFrame(stats_rows))

if __name__ == "__main__":
    main()