# COMP4037 Coursework 2

Research Question:
Which categories of hospital admissions exhibit the greatest disparities amongst age groups?

Contents:
- `cw2_analysis_final.py`: final Python analysis and visualization script
- `cw2_heatmap_final.png`: final matrix heatmap used in the report

Method summary:
The script loads NHS hospital admissions data from 2021–22 to 2023–24, aggregates 3-character primary diagnosis categories across the three years, computes an admissions-weighted mean age, converts age-group counts into within-category proportions for the final non-Age-0 heatmap analysis, selects 18 diagnosis categories with strong age-group concentration patterns, and generates the final heatmap.