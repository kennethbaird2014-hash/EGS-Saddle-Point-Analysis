# Atmospheric ‘Saddle Point Deposition’ and Equine Grass Sickness

**Author:** Kenneth Baird MEng (Open)  
**Status:** Submitted to *Equine Veterinary Journal* (2026)

## Overview
This repository contains the source code and processed data supporting the study *"Atmospheric ‘Saddle Point Deposition’ and Equine Grass Sickness: Stagnation and Particulate Matter Sedimentation as Potential Risk Factors."*

The study investigates the correlation between atmospheric stagnation points ("Saddle Points") and the onset of Equine Grass Sickness (EGS) in the UK.

## Repository Structure

### 1. Source Code (`/src`)
* `saddle_point_detection.py`: The algorithm used to identify hyperbolic stagnation points in ERA5 wind fields.
* `particulate_analysis.py`: Scripts for processing CAMS PM2.5/PM10 fractionation data.
* `statistical_grid_search.py`: The brute-force grid search used to calculate Odds Ratios across spatiotemporal windows.

### 2. Data (`/data`)
* `stats_filtered_26JAN.csv`: Aggregated meteorological stats for Case vs. Control events.
* `grid_search_filtered.csv`: The raw output of the Fisher's Exact Test grid search.
* *Note: Raw ERA5/CAMS binary files are not included due to size but can be downloaded from the Copernicus Climate Data Store (CDS).*

## Dependencies
To reproduce this analysis, you will need:
* Python 3.8+
* Pandas
* NumPy
* SciPy (for Fisher's Exact Test)
* CDSAPI (for Copernicus data retrieval)

## Citation
If you use this code or data, please cite the accompanying paper:
> Baird, K. (2026). Atmospheric ‘Saddle Point Deposition’ and Equine Grass Sickness. *Equine Veterinary Journal*. [In Press]

## License
This project is licensed under the MIT License - see the LICENSE file for details.