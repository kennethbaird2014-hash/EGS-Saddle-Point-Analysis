import cdsapi
import os
import calendar

# ================= CONFIGURATION =================
API_KEY = "PASTE_YOUR_KEY_HERE" 
API_URL = "https://ads.atmosphere.copernicus.eu/api"
OUTPUT_FOLDER = "cams_uk_2025"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# UK Bounding Box (Extended to include sea)
# Shetland is up to 61N. Let's go: North 62, West -12, South 49, East 2
AREA = [62, -12, 49, 2]

YEAR = '2025'
# Define months here so they are accessible
MONTHS = [f"{m:02d}" for m in range(1, 13)]
# =================================================

def download_cams_uk(year):
    print("--- Downloading from CAMS Global Near-Real-Time (NRT) dataset ---")

    if API_KEY == "PASTE_YOUR_KEY_HERE":
        print("Error: Please paste your CDS API Key in the script.")
        return

    c = cdsapi.Client(url=API_URL, key=API_KEY)
    
    for month in MONTHS:
        last_day = calendar.monthrange(int(year), int(month))[1]
        
        filename = f"CAMS_{year}_{month}.nc"
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        if os.path.exists(filepath):
            print(f"[Skip] {filename} already exists.")
            continue

        print(f"Requesting {year}-{month}...")
    
        try:
            # This block MUST be indented to be part of the 'for' loop
            c.retrieve(
                'cams-global-atmospheric-composition-forecasts',
                {
                    'date': f'{year}-{month}-01/{year}-{month}-{last_day}',
                    'type': 'analysis', 
                    'format': 'netcdf',
                    'area': AREA,
                    'time': ['00:00', '12:00'],
                    'leadtime_hour': '0',
                    'variable': [
                        # Weather
                        'mean_sea_level_pressure',
                        '10m_u_component_of_wind', 
                        '10m_v_component_of_wind',
                        '2m_dewpoint_temperature', 
                        '2m_temperature',
                        'surface_pressure',
                        'boundary_layer_height',
                        'total_precipitation',
                        # Particulate Matter
                        'particulate_matter_10um', 
                        'particulate_matter_2.5um', 
                        'particulate_matter_1um',
                        # Total Column
                        'total_column_nitric_acid',
                        'total_column_nitrogen_dioxide',
                        'total_column_nitrogen_monoxide',
                        'total_column_nitrate',
                        'total_column_organic_nitrates',
                        'total_column_nitrate_radical',
                        'total_column_methane',
                        'total_column_ozone',
                        'total_column_amine',
                        'total_column_ammonia',
                        'total_column_ammonium',
                        'total_column_lead'
                        # Variables commented out to reduce size
                        # # Sources
                        # 'total_column_source_of_ammonium_aerosol',
                        # 'total_column_source_of_coarse_mode_nitrate_aerosol',
                        # 'total_column_source_of_fine_mode_nitrate_aerosol',
                        # 'total_column_source_of_dust_aerosol_0.03-0.55um',
                        # 'total_column_source_of_dust_aerosol_0.55-9um',
                        # 'total_column_source_of_dust_aerosol_9-20um',
                        # 'total_column_source_of_hydrophilic_organic_matter_aerosol',
                        # 'total_column_source_of_hydrophobic_organic_matter_aerosol',
                        # # Dry Deposition
                        # 'dry_deposition_of_ammonium_aerosol',
                        # 'dry_deposition_of_coarse_mode_nitrate_aerosol',
                        # 'dry_deposition_of_fine_mode_nitrate_aerosol',
                        # 'dry_deposition_of_dust_aerosol_0.03-0.55um',
                        # 'dry_deposition_of_dust_aerosol_0.55-9um',
                        # 'dry_deposition_of_dust_aerosol_9-20um',
                        # 'dry_deposition_of_hydrophilic_organic_matter_aerosol',
                        # 'dry_deposition_of_hydrophobic_organic_matter_aerosol',
                        # # Wet Deposition (Convective Only)
                        # 'wet_deposition_of_ammonium_aerosol_by_convective_precipitation',
                        # 'wet_deposition_of_coarse_mode_nitrate_aerosol_by_convective_precipitation',
                        # 'wet_deposition_of_fine_mode_nitrate_aerosol_by_convective_precipitation',
                        # 'wet_deposition_of_dust_aerosol_0.03-0.55um_by_convective_precipitation',
                        # 'wet_deposition_of_dust_aerosol_0.55-9um_by_convective_precipitation',
                        # 'wet_deposition_of_dust_aerosol_9-20um_by_convective_precipitation',
                        # 'wet_deposition_of_hydrophilic_organic_matter_aerosol_by_convective_precipitation',
                        # 'wet_deposition_of_hydrophobic_organic_matter_aerosol_by_convective_precipitation',
                        # # Sedimentation
                        # 'sedimentation_of_ammonium_aerosol',
                        # 'sedimentation_of_coarse_mode_nitrate_aerosol',
                        # 'sedimentation_of_fine_mode_nitrate_aerosol',
                        # 'sedimentation_of_dust_aerosol_0.03-0.55um',
                        # 'sedimentation_of_dust_aerosol_0.55-9um',
                        # 'sedimentation_of_dust_aerosol_9-20um',
                        # 'sedimentation_of_hydrophilic_organic_matter_aerosol',
                        # 'sedimentation_of_hydrophobic_organic_matter_aerosol',
                        # # Optical Depth
                        # 'nitrate_aerosol_optical_depth_550nm',
                        # 'organic_matter_aerosol_optical_depth_550nm',
                        # 'ammonium_aerosol_optical_depth_550nm',
                        # 'dust_aerosol_optical_depth_550nm'
                    ],
                },
                filepath) # Use filepath to save inside the folder
            print(f"Successfully saved {filename}")
            
        except Exception as e:
            print(f"Failed to download {year}-{month}: {e}")

# Call the function once; the loop inside the function handles the months
download_cams_uk(YEAR)