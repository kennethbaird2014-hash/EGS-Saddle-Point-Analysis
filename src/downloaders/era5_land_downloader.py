import cdsapi
import os

# ================= CONFIGURATION =================
API_URL = "https://cds.climate.copernicus.eu/api"
API_KEY = "PASTE_YOUR_KEY_HERE"
OUTPUT_FOLDER = "era5_land_uk_2025"

# UK Bounding Box (Extended to include sea)
# Shetland is up to 61N. Let's go: North 62, West -12, South 49, East 2
AREA = [62, -12, 49, 2]

# Time range
YEAR = '2025'
MONTHS = [f"{m:02d}" for m in range(1, 13)]
# All days and hours
DAYS = [f"{d:02d}" for d in range(1, 32)]
TIMES = [f"{h:02d}:00" for h in range(24)]

# Variables to download
# We combine wind and thermal into one request per month to keep files organized
VARIABLES = [
    '10m_u_component_of_wind',
    '10m_v_component_of_wind',
    '2m_temperature',
    '2m_dewpoint_temperature',
    'surface_pressure',
    'total_precipitation'
]
# =================================================

def main():
    print("--- ERA5 2025 Downloader ---")

    if API_KEY == "PASTE_YOUR_KEY_HER":
        print("Error: Please paste your CDS API Key in the script.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    c = cdsapi.Client(url=API_URL, key=API_KEY)

    for month in MONTHS:
        filename = f"era5_uk_{YEAR}_{month}.nc"
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        if os.path.exists(filepath):
            print(f"[Skip] {filename} already exists.")
            continue

        print(f"Requesting {YEAR}-{month} (Wind, Temp, Dew, Press, Precip)...")
        print("This may take 10-20 minutes per file (queued on server).")

        try:
            c.retrieve(
                'reanalysis-era5-land',
                {
                    'format': 'netcdf',
                    'variable': VARIABLES,
                    'year': YEAR,
                    'month': month,
                    'day': DAYS,
                    'time': TIMES,
                    'area': AREA,
                },
                filepath)
            print(f"  [Success] Downloaded {filename}")

        except Exception as e:
            print(f"  [Error] Failed to download {month}: {e}")

if __name__ == "__main__":
    main()