import pandas as pd


DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

MEAL_TYPES = ["Breakfast", "Lunch", "Dinner"]


def get_candidates_by_meal_type(meals_df, meal_type):
    return meals_df[
        meals_df["meal_type"].str.lower() == meal_type.lower()
    ].copy()


def rank_candidates(candidates_df, used_meals, calorie_target):
    candidates = candidates_df.copy()

    if candidates.empty:
        return candidates

    candidates["already_used"] = candidates["meal_name"].isin(used_meals)
    candidates["calorie_gap"] = (candidates["calories"] - calorie_target).abs()

    # Strongly prioritize unused meals first, then calorie fit
    candidates = candidates.sort_values(
        by=["already_used", "calorie_gap", "calories"],
        ascending=[True, True, False]
    )

    return candidates


def choose_best_meal(candidates_df, used_meals, calorie_target):
    ranked = rank_candidates(
        candidates_df=candidates_df,
        used_meals=used_meals,
        calorie_target=calorie_target
    )

    if ranked.empty:
        return None, "No candidate meals available."

    selected = ranked.iloc[0]

    warning = ""

    if selected["meal_name"] in used_meals:
        warning = "Repeated meal used because safe options were limited."

    return selected, warning


def generate_7_day_plan(filtered_meals_df, calorie_target):
    """
    Generates a 7-day meal plan while prioritizing:
    1. safe meals already passed from filters
    2. no repeated meals when possible
    3. reasonable calorie fit
    4. breakfast/lunch/dinner structure
    """

    if filtered_meals_df.empty:
        return pd.DataFrame(), ["No meals available."]

    plan_rows = []
    generation_warnings = []
    used_meals = set()

    calorie_targets = {
        "Breakfast": calorie_target * 0.25,
        "Lunch": calorie_target * 0.35,
        "Dinner": calorie_target * 0.40
    }

    for day_number, day_name in enumerate(DAYS, start=1):

        for meal_type in MEAL_TYPES:

            candidates = get_candidates_by_meal_type(
                filtered_meals_df,
                meal_type
            )

            selected_meal, warning = choose_best_meal(
                candidates_df=candidates,
                used_meals=used_meals,
                calorie_target=calorie_targets[meal_type]
            )

            if selected_meal is None:
                generation_warnings.append(
                    f"{day_name} {meal_type}: no meal found."
                )
                continue

            used_meals.add(selected_meal["meal_name"])

            row = selected_meal.to_dict()
            row["day"] = day_name
            row["day_number"] = day_number
            row["planned_meal_type"] = meal_type

            plan_rows.append(row)

            if warning:
                generation_warnings.append(
                    f"{day_name} {meal_type}: {warning}"
                )

    plan_df = pd.DataFrame(plan_rows)

    if not plan_df.empty:
        ordered_columns = [
            "day_number",
            "day",
            "planned_meal_type",
            "meal_name",
            "category",
            "cuisine",
            "ingredients",
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
            "magnesium_mg",
            "gi_score"
        ]

        existing_columns = [
            col for col in ordered_columns
            if col in plan_df.columns
        ]

        plan_df = plan_df[existing_columns]

    return plan_df, generation_warnings