import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# 1. Load Data
df = pd.read_csv('axis_gradient_results.csv')

# 2. P-Value Verification (Just to be triple sure for the text response)
df['In_Ratio_Step3'] = df['PM25_In_Step3'] / df['PM10_In_Step3']
df['Out_Ratio_Step3'] = df['PM25_Out_Step3'] / df['PM10_Out_Step3']
valid_df = df.dropna(subset=['In_Ratio_Step3', 'Out_Ratio_Step3'])
t_stat, p_val = stats.ttest_rel(valid_df['Out_Ratio_Step3'], valid_df['In_Ratio_Step3'])

# 3. Prepare Data for "Reactor" Plot
# We want to plot the profile from -30km (Upwind) to +30km (Downwind)
distances = [-30, -20, -10, 0, 10, 20, 30]
# Calculate means for each point
# Upwind (Inflow)
mean_in_3 = (df['PM25_In_Step3'] / df['PM10_In_Step3']).mean()
mean_in_2 = (df['PM25_In_Step2'] / df['PM10_In_Step2']).mean()
mean_in_1 = (df['PM25_In_Step1'] / df['PM10_In_Step1']).mean()
# Center
mean_center = (df['PM25_Center'] / df['PM10_Center']).mean()
# Downwind (Outflow)
mean_out_1 = (df['PM25_Out_Step1'] / df['PM10_Out_Step1']).mean()
mean_out_2 = (df['PM25_Out_Step2'] / df['PM10_Out_Step2']).mean()
mean_out_3 = (df['PM25_Out_Step3'] / df['PM10_Out_Step3']).mean()

ratios = [mean_in_3, mean_in_2, mean_in_1, mean_center, mean_out_1, mean_out_2, mean_out_3]

# Calculate Standard Error for error bars (using SEM of the *ratios*)
se_in_3 = stats.sem(df['PM25_In_Step3'] / df['PM10_In_Step3'], nan_policy='omit')
se_in_2 = stats.sem(df['PM25_In_Step2'] / df['PM10_In_Step2'], nan_policy='omit')
se_in_1 = stats.sem(df['PM25_In_Step1'] / df['PM10_In_Step1'], nan_policy='omit')
se_center = stats.sem(df['PM25_Center'] / df['PM10_Center'], nan_policy='omit')
se_out_1 = stats.sem(df['PM25_Out_Step1'] / df['PM10_Out_Step1'], nan_policy='omit')
se_out_2 = stats.sem(df['PM25_Out_Step2'] / df['PM10_Out_Step2'], nan_policy='omit')
se_out_3 = stats.sem(df['PM25_Out_Step3'] / df['PM10_Out_Step3'], nan_policy='omit')

errors = [se_in_3, se_in_2, se_in_1, se_center, se_out_1, se_out_2, se_out_3]

# --- PLOT 1: THE REACTOR PROFILE ---
fig1, ax1 = plt.subplots(figsize=(12, 6))

# Plot line
ax1.errorbar(distances, ratios, yerr=errors, fmt='-o', color='purple', ecolor='gray', capsize=5, linewidth=2, markersize=8)

# Annotations
ax1.axvline(0, color='k', linestyle='--', alpha=0.3)
#ax1.text(0, min(ratios)-0.001, 'Saddle Point\n(Stagnation Zone)', ha='center', va='top', fontsize=10)

ax1.text(-25, mean_in_3, 'Inflow (Background Air)', ha='center', va='bottom', fontsize=10, color='blue')
ax1.text(25, mean_out_3, 'Outflow (Enriched Plume)', ha='center', va='bottom', fontsize=10, color='red')

# Styling
ax1.set_title(f'The Deposition Effect: PM2.5/PM10 Ratio Change Across the Saddle Point\n(N={len(valid_df)}, P < 1e-150)', fontsize=14)
ax1.set_xlabel('Distance from Center (km)\n<- Upwind | Downwind ->', fontsize=12)
ax1.set_ylabel('Fine Particle Fraction (PM2.5 / PM10)', fontsize=12)
ax1.grid(True, alpha=0.3)
ax1.set_xticks(distances)
ax1.set_xticklabels(['-30km', '-20km', '-10km', 'Center', '+10km', '+20km', '+30km'])

# Add P-value annotation
ax1.annotate(f"Significant Retention\nOutflow > Inflow\nP ≈ {p_val:.1e}", 
             xy=(28, mean_out_3), xytext=(15, mean_out_3 + 0.004),
             arrowprops=dict(facecolor='black', shrink=0.05))

plt.tight_layout()
plt.savefig('reactor_profile.png', dpi=300)

# --- PLOT 2: THE MAP ---
fig2, ax2 = plt.subplots(figsize=(10, 10))

# Filter to UK/Europe Lat/Lon roughly (dataset seems to be UK focused based on prev text)
# Just use the data bounds
# Plot scatter
# Color by Center Ratio to show "hotspots"
sc = ax2.scatter(df['longitude'], df['latitude'], c=df['PM25_Center']/df['PM10_Center'], 
                 cmap='magma', s=5, alpha=0.5, vmin=0.6, vmax=1.0)

ax2.set_title('Map of Identified Saddle Points (Colored by PM Ratio)', fontsize=14)
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')
plt.colorbar(sc, ax=ax2, label='PM2.5 / PM10 Ratio')
ax2.grid(True, alpha=0.3)

# Aspect ratio
ax2.set_aspect('equal')

plt.tight_layout()
plt.savefig('saddle_point_map.png', dpi=300)

print(f"Plots saved. P-value re-verified: {p_val}")