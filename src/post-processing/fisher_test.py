import scipy.stats as stats

table = [[11, 33], [37, 15]] # Wait, careful with the table orientation
# Cases: 11 match, 37 no match.
# Controls: 3 match, 45 no match.
# Table: [[Match_Case, Match_Control], [NoMatch_Case, NoMatch_Control]] ?
# Fisher exact takes [[a, b], [c, d]]
# Row 1: Match, Row 2: No Match
# Col 1: Case, Col 2: Control
contingency = [[11, 3], [37, 45]]
oddsr, p_two = stats.fisher_exact(contingency)
p_one = stats.fisher_exact(contingency, alternative='greater')[1]

print(f"Fisher Two-tailed: {p_two}")
print(f"Fisher One-tailed (Greater): {p_one}")

Code output