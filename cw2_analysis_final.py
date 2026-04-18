"""
COMP4037 Research Methods Coursework 2
Research Question:
Which categories of hospital admissions exhibit the greatest disparities amongst age groups?

This script loads NHS hospital admissions data from 2021–22 to 2023–24,
aggregates 3-character primary diagnosis categories, converts age-group counts
to within-category proportions, selects 18 diagnosis categories with strong
age-group concentration patterns, and generates the final matrix heatmap.
"""

import pandas as pd
import matplotlib.pyplot as plt

file_2021 = "hosp-epis-stat-admi-diag-2021-22-tab.xlsx"
file_2022 = "hosp-epis-stat-admi-diag-2022-23-tab_V2.xlsx"
file_2023 = "hosp-epis-stat-admi-diag-2023-24-tab.xlsx"

sheet_name = "Primary Diagnosis 3 Character"

def clean_column_name(col):
    if pd.isna(col):
        return col
    col = str(col)
    col = col.replace("\n", " ")
    col = " ".join(col.split())
    return col

def make_unique(columns):
    counts = {}
    new_cols = []
    for col in columns:
        if col not in counts:
            counts[col] = 0
            new_cols.append(col)
        else:
            counts[col] += 1
            new_cols.append(f"{col}.{counts[col]}")
    return new_cols

def standardize_columns(df):
    df.columns = [clean_column_name(c) for c in df.columns]

    rename_map = {
        "Primary diagnosis: 3 character code and description": "Diagnosis Code",
        "Unnamed: 1": "Diagnosis Description",
        "Finished consultant episodes": "FCE",
        "Finished Admission Episodes": "Admissions",
        "Male (FCE)": "Male",
        "Female (FCE)": "Female",
        "Gender Unknown (FCE)": "Gender Unknown",
        "Emergency (FAE)": "Emergency",
        "Waiting list (FAE)": "Waiting list",
        "Planned (FAE)": "Planned",
        "Other (FAE)": "Other",
        "Mean time waited (Days)": "Mean time waited",
        "Median time waited (Days)": "Median time waited",
        "Mean length of stay (Days)": "Mean length of stay",
        "Median length of stay (Days)": "Median length of stay",
        "Mean age (Years)": "Mean age",
        "Day case (FCE)": "Day case",
        "Elective (FAE)": "Elective"
    }

    for age in [
        "Age 0", "Age 1-4", "Age 5-9", "Age 10-14", "Age 15", "Age 16", "Age 17",
        "Age 18", "Age 19", "Age 20-24", "Age 25-29", "Age 30-34", "Age 35-39",
        "Age 40-44", "Age 45-49", "Age 50-54", "Age 55-59", "Age 60-64",
        "Age 65-69", "Age 70-74", "Age 75-79", "Age 80-84", "Age 85-89", "Age 90+"
    ]:
        rename_map[f"{age} (FCE)"] = age

    df = df.rename(columns=rename_map)

    # 关键：让重复列名唯一
    df.columns = make_unique(df.columns)

    return df

def load_year(file_path, year_label):
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=10)
    df = standardize_columns(df)
    df["year"] = year_label
    return df

df_2021 = load_year(file_2021, "2021-22")
df_2022 = load_year(file_2022, "2022-23")
df_2023 = load_year(file_2023, "2023-24")

df_all = pd.concat([df_2021, df_2022, df_2023], ignore_index=True)

df_all = df_all[df_all["Diagnosis Code"].notna()].copy()
df_all = df_all[df_all["Diagnosis Code"] != "Total"].copy()

age_cols = [
    "Age 0", "Age 1-4", "Age 5-9", "Age 10-14", "Age 15", "Age 16", "Age 17",
    "Age 18", "Age 19", "Age 20-24", "Age 25-29", "Age 30-34", "Age 35-39",
    "Age 40-44", "Age 45-49", "Age 50-54", "Age 55-59", "Age 60-64",
    "Age 65-69", "Age 70-74", "Age 75-79", "Age 80-84", "Age 85-89", "Age 90+"
]

keep_cols = ["Diagnosis Code", "Diagnosis Description", "FCE", "Admissions", "Mean age", "year"] + age_cols

df_core = df_all[keep_cols].copy()

numeric_cols = ["FCE", "Admissions", "Mean age"] + age_cols

for col in numeric_cols:
    df_core[col] = pd.to_numeric(df_core[col], errors="coerce")


group_cols = ["Diagnosis Code", "Diagnosis Description"]

avg_cols = ["FCE", "Admissions", "Mean age"] + age_cols

sum_cols = ["FCE", "Admissions"] + age_cols

# Aggregate counts across the three years so higher-volume years contribute proportionally.
df_sum = (
    df_core.groupby(group_cols, as_index=False)[sum_cols]
    .sum()
)

# Compute an admissions-weighted mean age.
df_weighted_age = (
    df_core.assign(weighted_mean_age=df_core["Mean age"] * df_core["Admissions"])
    .groupby(group_cols, as_index=False)[["weighted_mean_age", "Admissions"]]
    .sum()
)

df_avg = df_sum.merge(df_weighted_age, on=group_cols, suffixes=("", "_weight"))
df_avg["Mean age"] = df_avg["weighted_mean_age"] / df_avg["Admissions_weight"]
df_avg = df_avg.drop(columns=["weighted_mean_age", "Admissions_weight"])


# Exclude Age 0 from the final disparity analysis to match the plotted heatmap columns.
analysis_age_cols = [col for col in age_cols if col != "Age 0"]

df_share = df_avg.copy()

df_share["Age Total"] = df_share[analysis_age_cols].sum(axis=1)

for col in analysis_age_cols:
    df_share[col] = df_share[col] / df_share["Age Total"]

df_share = df_share[df_share["Age Total"] > 0].copy()


df_ranked = df_share.copy()

df_ranked["max_age_share"] = df_ranked[analysis_age_cols].max(axis=1)
df_ranked["dominant_age_group"] = df_ranked[analysis_age_cols].idxmax(axis=1)

# Rank categories after excluding very small totals and Age 0 from the final analysis.
df_ranked_filtered = df_ranked[df_ranked["Age Total"] >= 100].copy()

selected_codes = [
    "F89", "Q54", "E30", "N44", "J05", "L05", "O21", "N98", "O48",
    "N95", "D25", "N70", "C61", "C34", "C45", "G30", "F01", "R54"
]

# Final 18 categories chosen after exploratory ranking, filtered to preserve life-course coverage and readability in the final heatmap.
selected_code_set = set(selected_codes)
df_final = df_ranked_filtered[df_ranked_filtered["Diagnosis Code"].isin(selected_code_set)].copy()


heatmap_cols = ["Diagnosis Code", "Diagnosis Description", "dominant_age_group"] + age_cols

df_heatmap = df_final[heatmap_cols].copy()

age_order = {
    "Age 1-4": 1,
    "Age 5-9": 2,
    "Age 10-14": 3,
    "Age 15": 4,
    "Age 16": 5,
    "Age 17": 6,
    "Age 18": 7,
    "Age 19": 8,
    "Age 20-24": 9,
    "Age 25-29": 10,
    "Age 30-34": 11,
    "Age 35-39": 12,
    "Age 40-44": 13,
    "Age 45-49": 14,
    "Age 50-54": 15,
    "Age 55-59": 16,
    "Age 60-64": 17,
    "Age 65-69": 18,
    "Age 70-74": 19,
    "Age 75-79": 20,
    "Age 80-84": 21,
    "Age 85-89": 22,
    "Age 90+": 23,
}

df_heatmap["age_order"] = df_heatmap["dominant_age_group"].map(age_order)

df_heatmap = df_heatmap.sort_values(
    ["age_order", "dominant_age_group", "Diagnosis Code"]
).copy()


short_label_map = {
    "F89": "F89 – Psych. development",
    "J05": "J05 – Croup/epiglottitis",
    "Q54": "Q54 – Hypospadias",
    "E30": "E30 – Puberty disorders",
    "N44": "N44 – Torsion of testis",
    "L05": "L05 – Pilonidal cyst",
    "O21": "O21 – Vomiting in pregnancy",
    "N98": "N98 – Assisted fertilization comp.",
    "O48": "O48 – Prolonged pregnancy",
    "N70": "N70 – Salpingitis/oophoritis",
    "D25": "D25 – Leiomyoma of uterus",
    "N95": "N95 – Perimenopausal disorders",
    "C34": "C34 – Lung cancer",
    "C61": "C61 – Prostate cancer",
    "C45": "C45 – Mesothelioma",
    "G30": "G30 – Alzheimer disease",
    "F01": "F01 – Vascular dementia",
    "R54": "R54 – Senility"
}

plot_df = df_heatmap.copy()
plot_df["y_label"] = plot_df["Diagnosis Code"].map(short_label_map)
plot_age_cols = analysis_age_cols
plot_df = plot_df.set_index("y_label")[plot_age_cols]

plt.figure(figsize=(15, 8.5))
plt.imshow(plot_df, aspect="auto")
plt.colorbar(label="Within-category age share")

plt.xticks(range(len(plot_age_cols)), plot_age_cols, rotation=45, ha="right")
plt.yticks(range(len(plot_df.index)), plot_df.index)

plt.title("Age-group disparities across selected hospital admission categories")
plt.xlabel("Age group")
plt.ylabel("Diagnosis category")

plt.tight_layout()
plt.savefig("cw2_heatmap_final.png", dpi=300, bbox_inches="tight")
plt.show()