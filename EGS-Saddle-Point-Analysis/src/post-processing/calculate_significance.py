import pandas as pd
import scipy.stats as stats
import os

# ================= CONFIGURATION =================
# Set these to your actual filenames if you don't want to type them in
FILE_EGS       = "grid_search_filtered_26JAN.csv"  # Your Real Data
FILE_CONTROL   = "grid_search_filtered_26JANcon.csv"         # Your Control/Random Data

# IMPORTANT: How many total cases were in each study?
# (e.g., if you had 48 EGS cases and 48 Control cases)
TOTAL_EGS      = 48 
TOTAL_CONTROL  = 48
# =================================================

def calculate_p_value(matches_egs, total_egs, matches_ctrl, total_ctrl):
    # Construct a 2x2 Contingency Table
    #              | Match | No Match |
    # ---------------------------------
    # EGS Group    |   A   |    B     |
    # Control Group|   C   |    D     |
    
    a = matches_egs
    b = total_egs - matches_egs
    c = matches_ctrl
    d = total_ctrl - matches_ctrl
    
    # Fisher's Exact Test is more accurate than Chi-Square for smaller sample sizes (<1000)
    # 'alternative="greater"' tests if EGS matches > Control matches
    odds_ratio, p_value = stats.fisher_exact([[a, b], [c, d]], alternative='greater')
    return p_value

def main():
    print("--- Significance Tester (Fisher's Exact Test) ---")
    
    # 1. Load Data
    try:
        df_egs = pd.read_csv(FILE_EGS)
        df_ctrl = pd.read_csv(FILE_CONTROL)
    except FileNotFoundError as e:
        print(f"Error: Could not find file. {e}")
        print("Please check the filenames in the CONFIGURATION section.")
        return

    # 2. Merge Tables on Distance and Days
    # We only want to compare rows that exist in both files (same parameters)
    merged = pd.merge(df_egs, df_ctrl, on=['Distance', 'Days'], suffixes=('_EGS', '_CTRL'))
    
    print(f"Comparing {len(merged)} parameter combinations...")
    
    results = []

    # 3. Iterate and Calculate P-Value
    for index, row in merged.iterrows():
        matches_egs = row['Matches_EGS']
        matches_ctrl = row['Matches_CTRL']
        
        p = calculate_p_value(matches_egs, TOTAL_EGS, matches_ctrl, TOTAL_CONTROL)
        
        # Calculate the "Lift" (How many times better is EGS?)
        # Avoid division by zero
        rate_egs = (matches_egs / TOTAL_EGS) * 100
        rate_ctrl = (matches_ctrl / TOTAL_CONTROL) * 100
        lift = rate_egs / rate_ctrl if rate_ctrl > 0 else 0
        
        results.append({
            'Distance_km': row['Distance'],
            'Days_Prior': row['Days'],
            'Matches_EGS': matches_egs,
            'Matches_CTRL': matches_ctrl,
            'Pct_EGS': f"{rate_egs:.1f}%",
            'Pct_CTRL': f"{rate_ctrl:.1f}%",
            'Lift_Factor': f"{lift:.2f}x",
            'P_Value': p,
            'Significant': "YES" if p < 0.05 else "NO"
        })

    # 4. Save and Sort
    final_df = pd.DataFrame(results)
    
    # Sort by lowest P-Value (Most Significant first)
    final_df = final_df.sort_values(by='P_Value', ascending=True)
    
    output_filename = "significance_results.csv"
    final_df.to_csv(output_filename, index=False)
    
    print("\n--- TOP 5 MOST SIGNIFICANT RESULTS ---")
    print(final_df.head(5).to_string(index=False))
    print("-" * 60)
    print(f"Full results saved to {output_filename}")
    
    # Check for "Gold Standard" significance
    best_p = final_df.iloc[0]['P_Value']
    if best_p < 0.01:
        print(f"\nResult: HIGHLY SIGNIFICANT (p < 0.01). The correlation is likely real.")
    elif best_p < 0.05:
        print(f"\nResult: SIGNIFICANT (p < 0.05).")
    else:
        print(f"\nResult: Not Significant (p > 0.05). Indistinguishable from random chance.")

if __name__ == "__main__":
    main()