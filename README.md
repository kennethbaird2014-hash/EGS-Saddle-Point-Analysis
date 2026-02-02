# Atmospheric ‘Saddle Point Deposition’ and Equine Grass Sickness

**Author:** Kenneth Baird MEng (Open)  
**Status:** Submitted to *Equine Veterinary Journal* (2026)

## Overview
This repository contains the source code and processed data supporting the study *"Atmospheric Stagnation and Particulate Sedimentation as Risk Factors for Equine Grass Sickness"*

The study investigates the correlation between atmospheric stagnation points ("Saddle Points") and the onset of Equine Grass Sickness (EGS) in the UK.

## Repository Structure
### 1. Source Code (`/src`)
	downloaders
		cams_downloader.py *Calls down air quality data
		era5_global_downloader.py *Calls down low res (30km) weather data
		era5_land_downloader.py *Calls down high res (10km) weather data over land only

	analysis
		CAMS_ERA5_EGS_analysis.py *Takes all era5 and cams data, detectings weather events and compares results to EGS case list
		CAMS_ERA5_EGS_analysis_control.py *A duplicate of CAMS_ERA5_EGS_analysis.py that compares weather data to control group instead
		analysis_axis_gradient.py *Alternate version of weather analysis used to generate heat maps
		PM25_PM10_ratio_analysis.py *checks PM2.5/PM10 ratio at events and background samples
	
	post-processing *If Ronseal did post-processing
		calculate_significance.py 
		CI_calculator.py
		fisher_test.py
		generate_reactor_plot.py
		heat_mapper.py
		reactor_map.py

### 2. Data (`/data`)
	**Initial case and control data**
	EGS_cases_2025.csv *List of 48 EGS cases
	EGS_cases_2025_control.csv *List of 48 random controls
	UK County Centroids.xlsx *List of UK County Centroids
	
	**Primary analysis results**
	correlations_filtered.csv *All event matches
	grid_search_filtered.csv *Percentage matches for each distance and time period (5km, 5 days steps)
	stats_filtered.csv *Mean and Std dev for common variables
	
	**Primary analysis results (control)**
	correlations_filtered_control.csv *All event matches
	grid_search_filtered_control.csv *Percentage matches for each distance and time period (5km, 5 days steps)
	stats_filtered_control.csv *Mean and Std dev for common variables
	
	**Additional post-processing checks and analysis**
	ratio_analysis_results.csv *PM2.5/PM10 ratio results
	significance_results.csv *Cases vs Control Lift factor and P values for each distance and time period (5km, 5 days steps)
	axis_gradient_results.csv *raw PM2.5/PM10 ratio data
	
	*Note: Raw ERA5/CAMS binary files are not included due to size but can be downloaded from the Copernicus Climate Data Store (CDS).*

## Dependencies
To reproduce this analysis, you will need:
* Python 3.8+
* Pandas
* NumPy
* SciPy (for Fisher's Exact Test)
* CDSAPI (for Copernicus data retrieval)

## Citation
If you use this code or data, please cite the accompanying paper:
> Baird, K. (2026). Atmospheric Stagnation and Particulate Sedimentation as Risk Factors for Equine Grass Sickness [Pre-print]

## License
This project is licensed under the MIT License - see the LICENSE file for details.