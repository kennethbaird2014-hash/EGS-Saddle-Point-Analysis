import cdsapi
import os

# ================= CONFIGURATION =================
API_URL = "https://cds.climate.copernicus.eu/api"
API_KEY = "PASTE_YOUR_KEY_HERE"
OUTPUT_FOLDER = "weather_data_marine"

# UK Bounding Box (Extended to include sea)
# Shetland is up to 61N. Let's go: North 62, West -9, South 49, East 3
AREA = [62, -9, 49, 3]

YEAR = '2025'
MONTHS = [f"{m:02d}" for m in range(1, 13)]
# =================================================

def main():
    print("--- ERA5 Marine (Global) Downloader ---")

    if API_KEY == "PASTE_YOUR_KEY_HERE":
        print("Error: Paste your API Key.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    c = cdsapi.Client(url=API_URL, key=API_KEY)

    for month in MONTHS:
        filename = f"era5_marine_{YEAR}_{month}.nc"
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        if os.path.exists(filepath):
            print(f"[Skip] {filename} exists.")
            continue

        print(f"Requesting {YEAR}-{month} (Marine/Global)...")

        try:
            # Note: Different dataset name! 'reanalysis-era5-single-levels'
            c.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'format': 'netcdf',
                    'variable': [
                        '10m_u_component_of_wind',
                        '10m_v_component_of_wind',
                        '2m_temperature',
                        '2m_dewpoint_temperature',
                        'surface_pressure'
                    ],
                    'year': YEAR,
                    'month': month,
                    'day': [f"{d:02d}" for d in range(1, 32)],
                    'time': [f"{h:02d}:00" for h in range(24)],
                    'area': AREA,
                },
                filepath)
            print(f"  [Success] {filename}")

        except Exception as e:
            print(f"  [Error] {month}: {e}")

if __name__ == "__main__":
    main()