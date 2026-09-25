## Summary

Implemented correlation and relationship analysis for churn prediction data.

## Analysis

- Computed Pearson correlations
- Computed Spearman correlations
- Compared correlations with churn
- Generated Pearson correlation heatmap
- Identified strong relationships using |r| > 0.7
- Documented correlation versus causation
- Performed correlation-based feature selection

## Business Interpretation

Support ticket correlation with churn is treated as an investigative signal rather than proof of causation. Possible explanations include reverse causation and customer pain acting as a confounding factor.

## Outputs

- `output/correlation_heatmap.png`
- `output/churn_correlation_comparison.csv`
- `output/strong_correlations.csv`
- `output/business_correlation_analysis.json`
- `data/processed/selected_churn_features.csv`
