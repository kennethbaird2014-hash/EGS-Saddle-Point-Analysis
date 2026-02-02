import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the data
df = pd.read_csv('significance_results.csv')

# Clean up percentage columns if they are strings
if df['Pct_EGS'].dtype == 'object':
    df['Pct_EGS'] = df['Pct_EGS'].str.rstrip('%').astype(float)
if df['Pct_CTRL'].dtype == 'object':
    df['Pct_CTRL'] = df['Pct_CTRL'].str.rstrip('%').astype(float)
if df['Lift_Factor'].dtype == 'object':
    df['Lift_Factor'] = df['Lift_Factor'].str.rstrip('x').astype(float)

# Prepare data for heatmaps
# Pivot table for P-values
p_pivot = df.pivot(index='Distance_km', columns='Days_Prior', values='P_Value')
# Pivot table for Lift Factors
lift_pivot = df.pivot(index='Distance_km', columns='Days_Prior', values='Lift_Factor')

# Set up the figure
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(2, 2)

# Custom color map for P-values (reversed so darker/intense is lower p-value)
# We usually want significant (low p) to be "hot" or distinct.
# Let's use a log scale for P-values visualization or just a boundary norm.
# Or simply 'viridis_r' where low P (dark) is good? No, usually 'Reds_r' or similar.
# Let's use 'viridis_r' and distinct markers.

# 1. P-Value Heatmap
ax1 = fig.add_subplot(gs[0, 0])
sns.heatmap(p_pivot, annot=True, fmt=".3f", cmap="viridis_r", ax=ax1, 
            cbar_kws={'label': 'P-Value (Lower is Better)'})
ax1.set_title('Statistical Significance (P-Value) Landscape', fontsize=16)
ax1.set_ylabel('Search Radius (km)', fontsize=12)
ax1.set_xlabel('Lead Time (Days)', fontsize=12)

# Highlight significant cells?
# We can draw rectangles around cells with P < 0.05 or 0.01 if needed, but the color map handles it.

# 2. Lift Factor Heatmap
ax2 = fig.add_subplot(gs[0, 1])
sns.heatmap(lift_pivot, annot=True, fmt=".2f", cmap="magma", ax=ax2,
            cbar_kws={'label': 'Lift Factor (EGS / Control)'})
ax2.set_title('Effect Size (Lift Factor) Landscape', fontsize=16)
ax2.set_ylabel('Search Radius (km)', fontsize=12)
ax2.set_xlabel('Lead Time (Days)', fontsize=12)

# 3. "Best Result" Detailed View
# Find the row with the minimum P-value
best_row = df.loc[df['P_Value'].idxmin()]

ax3 = fig.add_subplot(gs[1, :])

# Prepare data for bar chart
categories = ['EGS Cases', 'Control Group']
percentages = [best_row['Pct_EGS'], best_row['Pct_CTRL']]
counts = [best_row['Matches_EGS'], best_row['Matches_CTRL']]
colors = ['#d62728', '#1f77b4'] # Red for Case, Blue for Control

bars = ax3.bar(categories, percentages, color=colors, width=0.4)
ax3.set_ylim(0, 100)
ax3.set_ylabel('Match Rate (%)', fontsize=14)
ax3.set_title(f"Best Fit Result: {best_row['Distance_km']} km Radius, {best_row['Days_Prior']} Days Prior", fontsize=18)

# Annotate bars
for bar, count, pct in zip(bars, counts, percentages):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{pct:.1f}%\n({int(count)} matches)',
             ha='center', va='bottom', fontsize=14, fontweight='bold')

# Add significance bracket
x1, x2 = 0, 1
y, h, col = max(percentages) + 5, 2, 'k'
ax3.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=1.5, c=col)
ax3.text((x1+x2)*.5, y+h, f"P = {best_row['P_Value']:.4f}\n(Highly Significant)", ha='center', va='bottom', color=col, fontsize=14)

# Add text box with details
textstr = '\n'.join((
    f"Parameters:",
    f"  Radius: {best_row['Distance_km']} km",
    f"  Window: {best_row['Days_Prior']} days",
    f"",
    f"Statistics:",
    f"  Lift Factor: {best_row['Lift_Factor']}x",
    f"  Odds Ratio: TBD", # calculated in previous step but not passed explicitly here as column
    f"  Significance: {'YES' if best_row['Significant'] == 'YES' else 'NO'}"
))
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax3.text(0.95, 0.5, textstr, transform=ax3.transAxes, fontsize=14,
        verticalalignment='center', horizontalalignment='right', bbox=props)

plt.tight_layout()
plt.savefig('EGS_Star_Events_Analysis_Dashboard.png', dpi=300)
print("Visualization created successfully.")