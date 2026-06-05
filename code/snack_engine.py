import pandas as pd


SNACK_LIBRARY = {

    "protein_g": [
        "Hard Boiled Eggs",
        "Firm Tofu Cubes",
        "Pumpkin Seeds"
    ],

    "fiber_g": [
        "Kiwi",
        "Chia Seeds",
        "Oats"
    ],

    "iron_mg": [
        "Pumpkin Seeds",
        "Spinach",
        "Firm Tofu"
    ],

    "calcium_mg": [
        "Lactose-Free Yogurt",
        "Firm Tofu",
        "Fortified Almond Milk"
    ],

    "vitamin_b12_mcg": [
        "Eggs",
        "Fortified Cereal",
        "Lactose-Free Yogurt"
    ],

    "vitamin_d_mcg": [
        "Fortified Milk",
        "Egg Yolk",
        "Fortified Yogurt"
    ],

    "zinc_mg": [
        "Pumpkin Seeds",
        "Cashews",
        "Firm Tofu"
    ],

    "potassium_mg": [
        "Banana",
        "Kiwi",
        "Baked Potato"
    ],

    "magnesium_mg": [
        "Pumpkin Seeds",
        "Chia Seeds",
        "Almonds"
    ]
}


def generate_snack_recommendations(rda_warnings):
    """
    Converts nutrient warnings into snack suggestions.
    """

    rows = []

    for warning in rda_warnings:

        try:
            day = warning.split(":")[0]

            nutrient_text = (
                warning.split(":")[1]
                .split("below")[0]
                .strip()
            )

            nutrient_key = (
                nutrient_text
                .replace(" ", "_")
            )

            if nutrient_key not in SNACK_LIBRARY:
                continue

            snack_options = SNACK_LIBRARY[nutrient_key]

            snack_text = " • ".join(
                snack_options
            )

            rows.append({
                "day": day,
                "deficiency": nutrient_text,
                "recommended_snack": snack_text
            })

        except Exception:
            continue

    return pd.DataFrame(rows)