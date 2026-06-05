import pandas as pd

from snack_engine import (
    generate_snack_recommendations
)
import os


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RDA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "rda_table.csv"
)


NUTRIENT_COLUMNS = [
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
    "calcium_mg",
    "vitamin_b12_mcg",
    "vitamin_d_mcg",
    "zinc_mg",
    "sodium_mg",
    "potassium_mg",
    "magnesium_mg"
]


# --------------------------------------------------
# RDA Loading
# --------------------------------------------------

def load_rda_table():

    return pd.read_csv(
        RDA_PATH
    )


def get_rda_targets(
    sex,
    age
):
    """
    Returns NIH RDA targets
    for the user's age + sex.
    """

    rda_df = load_rda_table()

    match = rda_df[
        (rda_df["sex"] == sex)
        &
        (rda_df["age_min"] <= age)
        &
        (rda_df["age_max"] >= age)
    ]

    if match.empty:

        raise ValueError(
            f"No RDA match found for "
            f"{sex}, age {age}"
        )

    row = match.iloc[0]

    return {
        "protein_g": row["protein_g"],
        "fiber_g": row["fiber_g"],
        "iron_mg": row["iron_mg"],
        "calcium_mg": row["calcium_mg"],
        "vitamin_b12_mcg": row["vitamin_b12_mcg"],
        "vitamin_d_mcg": row["vitamin_d_mcg"],
        "zinc_mg": row["zinc_mg"],
        "potassium_mg": row["potassium_mg"],
        "magnesium_mg": row["magnesium_mg"]
    }


# --------------------------------------------------
# Daily Totals
# --------------------------------------------------

def calculate_daily_totals(
    plan_df
):

    if plan_df.empty:
        return pd.DataFrame()

    daily_totals = (
        plan_df.groupby("day")[NUTRIENT_COLUMNS]
        .sum()
        .reset_index()
    )

    return daily_totals


# --------------------------------------------------
# Diversity
# --------------------------------------------------

def calculate_diversity_score(
    plan_df
):

    if plan_df.empty:
        return 0

    total_meals = len(plan_df)

    unique_meals = (
        plan_df["meal_name"]
        .nunique()
    )

    unique_categories = (
        plan_df["category"]
        .nunique()
    )

    unique_cuisines = (
        plan_df["cuisine"]
        .nunique()
    )

    meal_score = (
        unique_meals
        / total_meals
    )

    category_score = (
        unique_categories
        / total_meals
    )

    cuisine_score = (
        unique_cuisines
        / total_meals
    )

    diversity_score = (
        meal_score * 0.6
        + category_score * 0.2
        + cuisine_score * 0.2
    )

    return round(
        diversity_score,
        2
    )


# --------------------------------------------------
# RDA Comparison
# --------------------------------------------------

def compare_to_rda(
    daily_totals_df,
    sex,
    age
):

    if daily_totals_df.empty:

        return (
            pd.DataFrame(),
            []
        )

    rda_targets = get_rda_targets(
        sex,
        age
    )

    comparison_rows = []

    warnings = []

    for _, row in daily_totals_df.iterrows():

        day = row["day"]

        comparison_row = {
            "day": day
        }

        for nutrient, target in (
            rda_targets.items()
        ):

            consumed = row.get(
                nutrient,
                0
            )

            percent_rda = (
                consumed
                / target
            ) * 100

            comparison_row[
                nutrient
            ] = round(
                percent_rda,
                1
            )

            if percent_rda < 80:

                warnings.append(
                    f"{day}: "
                    f"{nutrient.replace('_',' ')} "
                    f"below 80% RDA "
                    f"({percent_rda:.1f}%)"
                )

        comparison_rows.append(
            comparison_row
        )

    comparison_df = pd.DataFrame(
        comparison_rows
    )

    return (
        comparison_df,
        warnings
    )

def generate_deficiency_snacks(
    rda_warnings
):
    """
    Converts nutrient deficiency warnings
    into snack recommendations.
    """

    return generate_snack_recommendations(
        rda_warnings
    )