## meals.csv = recipes from chatgpt, build_expanded_meals = meals.csv recipes + monash low FODMAP recipes ##
## ------------------------------------------------

import pandas as pd
import os


MEALS_PATH = os.path.join("data", "meals.csv")
MONASH_PATH = os.path.join("data", "monash_recipes.csv")
USDA_PATH = os.path.join("data", "usda_food_snapshot.csv")
OUTPUT_PATH = os.path.join("data", "expanded_meals.csv")


def classify_meal_type(recipe_name):
    recipe_name = str(recipe_name).lower()

    breakfast_terms = [
        "oat", "breakfast", "granola", "smoothie",
        "muffin", "pancake", "toast", "porridge"
    ]

    dinner_terms = [
        "bolognese", "curry", "rice", "stir fry",
        "pasta", "salad", "soup", "chicken",
        "beef", "fish", "salmon"
    ]

    for term in breakfast_terms:
        if term in recipe_name:
            return "Breakfast"

    for term in dinner_terms:
        if term in recipe_name:
            return "Dinner"

    return "Lunch"


def infer_diet_flags(ingredients_text):
    text = str(ingredients_text).lower()

    contains_meat = any(
        term in text
        for term in ["chicken", "beef", "turkey", "pork", "lamb", "bacon"]
    )

    contains_fish = any(
        term in text
        for term in ["salmon", "tuna", "fish", "cod", "shrimp", "crab"]
    )

    contains_dairy = any(
        term in text
        for term in ["milk", "yogurt", "yoghurt", "cheese", "cream", "butter"]
    )

    contains_eggs = "egg" in text

    contains_gluten = any(
        term in text
        for term in ["wheat", "flour", "bread", "pasta"]
    )

    contains_pork = any(
        term in text
        for term in ["pork", "bacon", "ham"]
    )

    contains_soy = any(
        term in text
        for term in ["soy", "tofu", "edamame", "miso", "tempeh"]
    )

    contains_tree_nuts = any(
        term in text
        for term in [
            "almond", "walnut", "cashew", "pecan",
            "pistachio", "hazelnut", "macadamia"
        ]
    )

    contains_shellfish = any(
        term in text
        for term in ["shrimp", "crab", "lobster", "prawn", "scallop"]
    )

    return {
        "contains_meat": contains_meat,
        "contains_fish": contains_fish,
        "contains_dairy": contains_dairy,
        "contains_eggs": contains_eggs,
        "contains_gluten": contains_gluten,
        "contains_pork": contains_pork,
        "contains_soy": contains_soy,
        "contains_tree_nuts": contains_tree_nuts,
        "contains_shellfish": contains_shellfish
    }


def clean_ingredient_name(text):
    text = str(text).lower()

    remove_words = [
        "fresh", "finely", "roughly", "chopped", "grated",
        "sliced", "diced", "peeled", "ground", "large",
        "medium", "small", "optional", "lactose-free",
        "low-fodmap", "gluten-free", "cup", "cups", "tbsp",
        "tsp", "tablespoon", "teaspoon"
    ]

    for word in remove_words:
        text = text.replace(word, "")

    text = text.split(",")[0]
    text = text.strip()

    return text


def estimate_micronutrients(ingredients_text, usda_df):
    nutrient_cols = [
        "iron_mg",
        "calcium_mg",
        "vitamin_b12_mcg",
        "vitamin_d_mcg",
        "zinc_mg",
        "sodium_mg",
        "potassium_mg",
        "magnesium_mg"
    ]

    totals = {nutrient: 0 for nutrient in nutrient_cols}
    matches_found = 0

    ingredients = str(ingredients_text).split("|")

    # Only use the first 10 ingredients to avoid over-counting long garnish lists.
    ingredients = ingredients[:10]

    for ingredient in ingredients:
        ingredient = clean_ingredient_name(ingredient)

        if len(ingredient) < 3:
            continue

        matches = usda_df[
            usda_df["description"].str.contains(
                ingredient,
                case=False,
                na=False,
                regex=False
            )
        ]

        if matches.empty:
            continue

        matches = matches.head(5)
        matches_found += 1

        for nutrient in nutrient_cols:
            value = matches[nutrient].mean()

            if pd.notna(value):
                totals[nutrient] += value

    if matches_found == 0:
        return {
            "iron_mg": 3,
            "calcium_mg": 200,
            "vitamin_b12_mcg": 1,
            "vitamin_d_mcg": 1,
            "zinc_mg": 2,
            "sodium_mg": 300,
            "potassium_mg": 400,
            "magnesium_mg": 80
        }

    for nutrient in totals:
        totals[nutrient] = round(totals[nutrient], 2)

    return totals


def build_expanded_meals():
    meals_df = pd.read_csv(MEALS_PATH)
    monash_df = pd.read_csv(MONASH_PATH)
    usda_df = pd.read_csv(USDA_PATH)

    monash_rows = []

    for _, row in monash_df.iterrows():
        ingredients = row.get("ingredients", "")

        flags = infer_diet_flags(ingredients)

        micronutrients = estimate_micronutrients(
            ingredients_text=ingredients,
            usda_df=usda_df
        )

        monash_rows.append({
            "meal_name": row["recipe_name"],
            "meal_type": classify_meal_type(row["recipe_name"]),
            "category": "Monash Recipe",
            "cuisine": "Mixed",
            "ingredients": ingredients,

            "calories": row.get("calories", 400),
            "protein_g": row.get("protein_g", 15),
            "carbs_g": row.get("carbs_g", 40),
            "fat_g": row.get("fat_g", 15),
            "fiber_g": row.get("fiber_g", 5),

            "iron_mg": micronutrients["iron_mg"],
            "calcium_mg": micronutrients["calcium_mg"],
            "vitamin_b12_mcg": micronutrients["vitamin_b12_mcg"],
            "vitamin_d_mcg": micronutrients["vitamin_d_mcg"],
            "zinc_mg": micronutrients["zinc_mg"],
            "sodium_mg": micronutrients["sodium_mg"],
            "potassium_mg": micronutrients["potassium_mg"],
            "magnesium_mg": micronutrients["magnesium_mg"],

            "gi_score": 50,

            "is_vegetarian": not flags["contains_meat"] and not flags["contains_fish"],
            "is_vegan": (
                not flags["contains_meat"]
                and not flags["contains_fish"]
                and not flags["contains_dairy"]
                and not flags["contains_eggs"]
            ),
            "is_pescatarian": not flags["contains_meat"],

            "contains_meat": flags["contains_meat"],
            "contains_fish": flags["contains_fish"],
            "contains_dairy": flags["contains_dairy"],
            "contains_eggs": flags["contains_eggs"],
            "contains_gluten": flags["contains_gluten"],
            "contains_soy": flags["contains_soy"],
            "contains_tree_nuts": flags["contains_tree_nuts"],
            "contains_shellfish": flags["contains_shellfish"],
            "contains_pork": flags["contains_pork"]
        })

    monash_meals_df = pd.DataFrame(monash_rows)

    expanded_df = pd.concat(
        [meals_df, monash_meals_df],
        ignore_index=True
    )

    expanded_df = expanded_df.drop_duplicates(subset=["meal_name"])

    expanded_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Original meals: {len(meals_df)}")
    print(f"Monash meals: {len(monash_meals_df)}")
    print(f"Expanded meals: {len(expanded_df)}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_expanded_meals()