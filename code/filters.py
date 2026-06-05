import os
import pandas as pd


# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FODMAP_PATH = os.path.join(DATA_DIR, "fodmap_rules.csv")


# --------------------------------------------------
# Clinical condition rules
# --------------------------------------------------
GERD_TRIGGER_TERMS = [
    "tomato",
    "citrus",
    "orange",
    "lemon",
    "lime",
    "coffee",
    "chocolate",
    "fried",
    "spicy",
    "pepper",
    "hot sauce"
]

DIABETES_MAX_GI = 55
HYPERTENSION_MAX_SODIUM_PER_MEAL = 600


# --------------------------------------------------
# Allergy mapping
# --------------------------------------------------
ALLERGY_COLUMN_MAP = {
    "Gluten": "contains_gluten",
    "Dairy": "contains_dairy",
    "Tree Nuts": "contains_tree_nuts",
    "Soy": "contains_soy",
    "Shellfish": "contains_shellfish",
    "Eggs": "contains_eggs"
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def load_high_fodmap_terms():
    """
    Loads HIGH-FODMAP ingredients from data/fodmap_rules.csv.

    This replaces the earlier hardcoded IBS keyword list and makes
    IBS filtering data-driven.
    """

    if not os.path.exists(FODMAP_PATH):
        raise FileNotFoundError(
            "Could not find data/fodmap_rules.csv. "
            "Run scripts/build_fodmap_rules.py first."
        )

    fodmap_df = pd.read_csv(FODMAP_PATH)

    required_columns = {
        "ingredient",
        "fodmap_level",
        "fodmap_group",
        "category"
    }

    missing_columns = required_columns - set(fodmap_df.columns)

    if missing_columns:
        raise ValueError(
            f"fodmap_rules.csv is missing columns: {missing_columns}"
        )

    high_fodmap_terms = (
        fodmap_df[
            fodmap_df["fodmap_level"].str.upper() == "HIGH"
        ]["ingredient"]
        .dropna()
        .astype(str)
        .str.lower()
        .unique()
        .tolist()
    )

    return high_fodmap_terms


def text_contains_any(text, terms):
    """
    Checks whether any term appears in a text field.
    """

    if pd.isna(text):
        return False, []

    text_lower = str(text).lower()

    matched_terms = []

    for term in terms:
        term_lower = str(term).lower()

        if term_lower in text_lower:
            matched_terms.append(term_lower)

    return len(matched_terms) > 0, matched_terms


def add_exclusion(exclusion_log, meal_name, reason):
    """
    Adds an excluded meal and reason to the exclusion log.
    """

    exclusion_log.append(
        {
            "meal_name": meal_name,
            "reason": reason
        }
    )


# --------------------------------------------------
# Clinical filtering
# --------------------------------------------------
def apply_clinical_filters(meals_df, conditions):

    filtered_df = meals_df.copy()
    exclusion_log = []

    if not conditions:
        return filtered_df, exclusion_log

    # --------------------------------------------------
    # IBS / Low-FODMAP filtering
    # --------------------------------------------------
    if "IBS" in conditions:

        high_fodmap_terms = load_high_fodmap_terms()
        keep_rows = []

        for _, row in filtered_df.iterrows():

            ingredients = row.get("ingredients", "")
            meal_name = row.get("meal_name", "Unknown meal")

            has_high_fodmap, matched_terms = text_contains_any(
                ingredients,
                high_fodmap_terms
            )

            if has_high_fodmap:
                matched_display = ", ".join(sorted(set(matched_terms)))

                add_exclusion(
                    exclusion_log,
                    meal_name,
                    (
                        "Excluded for IBS: contains HIGH-FODMAP "
                        f"ingredient(s) from fodmap_rules.csv: {matched_display}."
                    )
                )

                keep_rows.append(False)

            else:
                keep_rows.append(True)

        filtered_df = filtered_df[keep_rows].copy()

    # --------------------------------------------------
    # GERD / Acid Reflux filtering
    # --------------------------------------------------
    if "GERD / Acid Reflux" in conditions:

        keep_rows = []

        for _, row in filtered_df.iterrows():

            ingredients = row.get("ingredients", "")
            meal_name = row.get("meal_name", "Unknown meal")

            has_trigger, matched_terms = text_contains_any(
                ingredients,
                GERD_TRIGGER_TERMS
            )

            if has_trigger:
                matched_display = ", ".join(sorted(set(matched_terms)))

                add_exclusion(
                    exclusion_log,
                    meal_name,
                    (
                        "Excluded for GERD: contains acid reflux "
                        f"trigger ingredient(s): {matched_display}."
                    )
                )

                keep_rows.append(False)

            else:
                keep_rows.append(True)

        filtered_df = filtered_df[keep_rows].copy()

    # --------------------------------------------------
    # Type 2 Diabetes / GI filtering
    # --------------------------------------------------
    if "Type 2 Diabetes" in conditions:

        keep_rows = []

        for _, row in filtered_df.iterrows():

            gi_score = row.get("gi_score", 100)
            meal_name = row.get("meal_name", "Unknown meal")

            if gi_score > DIABETES_MAX_GI:
                add_exclusion(
                    exclusion_log,
                    meal_name,
                    (
                        "Excluded for Type 2 Diabetes: "
                        f"GI score {gi_score} exceeds {DIABETES_MAX_GI}."
                    )
                )

                keep_rows.append(False)

            else:
                keep_rows.append(True)

        filtered_df = filtered_df[keep_rows].copy()

    # --------------------------------------------------
    # Hypertension / sodium filtering
    # --------------------------------------------------
    if "Hypertension" in conditions:

        keep_rows = []

        for _, row in filtered_df.iterrows():

            sodium = row.get("sodium_mg", 0)
            meal_name = row.get("meal_name", "Unknown meal")

            if sodium > HYPERTENSION_MAX_SODIUM_PER_MEAL:
                add_exclusion(
                    exclusion_log,
                    meal_name,
                    (
                        "Excluded for Hypertension: "
                        f"sodium {sodium} mg exceeds meal limit of "
                        f"{HYPERTENSION_MAX_SODIUM_PER_MEAL} mg."
                    )
                )

                keep_rows.append(False)

            else:
                keep_rows.append(True)

        filtered_df = filtered_df[keep_rows].copy()

    return filtered_df, exclusion_log


# --------------------------------------------------
# Allergy filtering
# --------------------------------------------------
def apply_allergy_filters(meals_df, allergies):

    filtered_df = meals_df.copy()
    exclusion_log = []

    if not allergies:
        return filtered_df, exclusion_log

    keep_rows = []

    for _, row in filtered_df.iterrows():

        meal_name = row.get("meal_name", "Unknown meal")
        remove_meal = False

        for allergy in allergies:

            column_name = ALLERGY_COLUMN_MAP.get(allergy)

            if column_name is None:
                continue

            contains_allergen = row.get(column_name, False)

            if contains_allergen:

                reason = (
                    f"Excluded for allergy: contains {allergy.lower()}."
                )

                if allergy == "Gluten":
                    reason += (
                        " Cross-contamination risk for gluten sensitivity."
                    )

                add_exclusion(
                    exclusion_log,
                    meal_name,
                    reason
                )

                remove_meal = True
                break

        keep_rows.append(not remove_meal)

    filtered_df = filtered_df[keep_rows].copy()

    return filtered_df, exclusion_log


# --------------------------------------------------
# Diet preference filtering
# --------------------------------------------------
def apply_diet_filters(meals_df, diet, notes=""):

    filtered_df = meals_df.copy()
    exclusion_log = []

    keep_rows = []

    notes_lower = str(notes).lower()

    for _, row in filtered_df.iterrows():

        meal_name = row.get("meal_name", "Unknown meal")

        contains_meat = row.get("contains_meat", False)
        contains_fish = row.get("contains_fish", False)
        contains_dairy = row.get("contains_dairy", False)
        contains_eggs = row.get("contains_eggs", False)
        contains_pork = row.get("contains_pork", False)

        remove_meal = False
        reason = ""

        # Vegetarian
        if diet == "Vegetarian":
            if contains_meat or contains_fish:
                remove_meal = True
                reason = (
                    "Excluded for vegetarian diet: contains meat or fish."
                )

        # Vegan
        elif diet == "Vegan":
            if (
                contains_meat
                or contains_fish
                or contains_dairy
                or contains_eggs
            ):
                remove_meal = True
                reason = (
                    "Excluded for vegan diet: contains animal products."
                )

        # Pescatarian
        elif diet == "Pescatarian":
            if contains_meat:
                remove_meal = True
                reason = (
                    "Excluded for pescatarian diet: contains meat."
                )

        # Pork restriction
        if (
            not remove_meal
            and (
                "no pork" in notes_lower
                or "avoid pork" in notes_lower
            )
        ):
            if contains_pork:
                remove_meal = True
                reason = (
                    "Excluded due to no-pork restriction."
                )

        if remove_meal:
            add_exclusion(
                exclusion_log,
                meal_name,
                reason
            )

        keep_rows.append(not remove_meal)

    filtered_df = filtered_df[keep_rows].copy()

    return filtered_df, exclusion_log