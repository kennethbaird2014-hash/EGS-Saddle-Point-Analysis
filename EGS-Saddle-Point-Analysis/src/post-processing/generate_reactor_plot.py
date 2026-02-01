import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load Data
df = pd.read_csv('axis_gradient_results.csv')

# 2. P-Value Verification
# Calculate ratios at Step 3
df['In_Ratio_Step3'] = df['PM25_In_Step3'] / df['PM10_In_Step3']
df['Out_Ratio_Step3'] = df['PM25_Out_Step3'] / df['PM10_Out_Step3']
valid_df = df.dropna(subset=['In_Ratio_Step3', 'Out_Ratio_Step3'])

# Paired T-Test
t_stat, p_val = stats.ttest_rel(valid_df['Out_Ratio_Step3'], valid_df['In_Ratio_Step3'])

# Calculate Effect Size (Cohen's d)
diff = valid_df['Out_Ratio_Step3'] - valid_df['In_Ratio_Step3']
mean_diff = diff.mean()
std_diff = diff.std()
cohens_d = mean_diff / std_diff

print(f"--- P-Value Verification ---")
print(f"N: {len(valid_df)}")
print(f"T-Statistic: {t_stat}")
print(f"P-Value: {p_val}")
print(f"Mean Difference: {mean_diff}")
print(f"Cohen's d: {cohens_d}")

# 3. Prepare Data for Reactor Plot
# We need means and Confidence Intervals (95%) for each step
steps = [0, 1, 2, 3]
distances = [0, 10, 20, 30] # Approx km

# Center Stats
center_ratio = (df['PM25_Center'] / df['PM10_Center'])
mean_center = center_ratio.mean()
ci_center = 1.96 * center_ratio.std() / np.sqrt(len(center_ratio))

means_in = [mean_center]
cis_in = [ci_center]
means_out = [mean_center]
cis_out = [ci_center]

for k in [1, 2, 3]:
    # Inflow
    r_in = df[f'PM25_In_Step{k}'] / df[f'PM10_In_Step{k}']
    means_in.append(r_in.mean())
    cis_in.append(1.96 * r_in.std() / np.sqrt(len(r_in)))
    
    # Outflow
    r_out = df[f'PM25_Out_Step{k}'] / df[f'PM10_Out_Step{k}']
    means_out.append(r_out.mean())
    cis_out.append(1.96 * r_out.std() / np.sqrt(len(r_out)))

# 4. Generate "Reactor" Plot
plt.figure(figsize=(10, 6))
plt.errorbar(distances, means_in, yerr=cis_in, fmt='-o', label='Inflow Axis (Upwind)', color='blue', capsize=5)
plt.errorbar(distances, means_out, yerr=cis_out, fmt='-o', label='Outflow Axis (Downwind)', color='red', capsize=5)

plt.title('The "Reactor Effect": PM2.5 Fractionation by Axis', fontsize=14)
plt.xlabel('Distance from Saddle Point Center (km)', fontsize=12)
plt.ylabel('PM2.5 / PM10 Ratio', fontsize=12)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('reactor_effect_plot.png', dpi=300)
plt.close()

# 5. Generate Map of Events
plt.figure(figsize=(10, 12))
# Filter bounds for UK (approx)
uk_df = df[(df['latitude'] >= 50) & (df['latitude'] <= 59) & (df['longitude'] >= -8) & (df['longitude'] <= 2)]

# Plot density or scatter
# Using hexbin for density visualization as 23k points is a lot
hb = plt.hexbin(uk_df['longitude'], uk_df['latitude'], gridsize=50, cmap='inferno', mincnt=1, bins='log')
cb = plt.colorbar(hb, label='Log10(Count of Events)')

plt.title('Density Map of Saddle Point Events (2025)', fontsize=16)
plt.xlabel('Longitude')
plt.ylabel('Latitude')

# Add basic coastline approximation if possible? 
# Without shapefiles, we rely on the data points outlining the landmass.
# Given these are ERA5-Land points, they should form the UK shape naturally.

plt.savefig('saddle_point_map.png', dpi=300)
plt.close()

print("Visualizations generated: reactor_effect_plot.png, saddle_point_map.png")