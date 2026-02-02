import numpy as np
import scipy.stats as stats

def calculate_or_ci(case_matches, control_matches, n_cases=48, n_controls=48):
    a = case_matches
    b = control_matches
    c = n_cases - a
    d = n_controls - b

    # Haldane-Anscombe correction if any cell is 0
    if a == 0 or b == 0 or c == 0 or d == 0:
        a += 0.5
        b += 0.5
        c += 0.5
        d += 0.5

    or_val = (a * d) / (b * c)
    se = np.sqrt(1/a + 1/b + 1/c + 1/d)
    
    ci_lower = np.exp(np.log(or_val) - 1.96 * se)
    ci_upper = np.exp(np.log(or_val) + 1.96 * se)
    
    return or_val, ci_lower, ci_upper, a, b

# Target configurations
targets = [
    {'Distance': 20, 'Days': 90, 'Label': 'Best Fit (90d/20km)'},
    {'Distance': 20, 'Days': 50, 'Label': 'Intermediate (50d/20km)'},
    {'Distance': 15, 'Days': 10, 'Label': 'Short Range (10d/15km)'}
]

results = []

for target in targets:
    # Get case matches
    case_row = df_cases[(df_cases['Distance'] == target['Distance']) & (df_cases['Days'] == target['Days'])]
    if not case_row.empty:
        case_matches = case_row.iloc[0]['Matches']
    else:
        case_matches = 0
        
    # Get control matches
    control_row = df_controls[(df_controls['Distance'] == target['Distance']) & (df_controls['Days'] == target['Days'])]
    if not control_row.empty:
        control_matches = control_row.iloc[0]['Matches']
    else:
        control_matches = 0
        
    or_val, ci_low, ci_high, a_final, b_final = calculate_or_ci(case_matches, control_matches)
    
    results.append({
        'Label': target['Label'],
        'Case_Matches': case_matches,
        'Control_Matches': control_matches,
        'OR': or_val,
        'CI_Lower': ci_low,
        'CI_Upper': ci_high
    })

print(pd.DataFrame(results))