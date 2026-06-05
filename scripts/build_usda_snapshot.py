import os
import time
import requests
import pandas as pd


API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

OUTPUT_PATH = os.path.join("data", "usda_food_snapshot.csv")

SEARCH_TERMS = [

    # proteins
    "chicken",
    "turkey",
    "beef",
    "pork",
    "salmon",
    "tuna",
    "cod",
    "shrimp",
    "egg",
    "eggs",
    "tofu",

    # grains
    "rice",
    "brown rice",
    "white rice",
    "quinoa",
    "oats",
    "oatmeal",
    "corn",
    "polenta",
    "bread",
    "pasta",

    # dairy
    "milk",
    "yogurt",
    "yoghurt",
    "cheese",
    "butter",

    # vegetables
    "spinach",
    "pumpkin",
    "tomato",
    "tomatoes",
    "capsicum",
    "pepper",
    "cucumber",
    "zucchini",
    "carrot",
    "potato",
    "sweet potato",
    "lettuce",
    "broccoli",
    "kale",

    # fruits
    "banana",
    "strawberry",
    "blueberry",
    "raspberry",
    "orange",
    "lemon",
    "pineapple",
    "kiwi",
    "grape",

    # legumes / nuts
    "soy",
    "beans",
    "lentils",
    "chickpeas",
    "almond",
    "walnut",
    "peanut",

    # recipe ingredients that appear often
    "coconut",
    "ginger",
    "parsley",
    "coriander",
    "cinnamon"
]

DATA_TYPES = [
    "Foundation",
    "SR Legacy",
    "Survey (FNDDS)",
    "Branded"
]

TARGET_RECORDS_PER_TERM = 500
PAGE_SIZE = 200


NUTRIENT_NAME_MAP = {
    "Energy": "calories",
    "Protein": "protein_g",
    "Carbohydrate, by difference": "carbs_g",
    "Total lipid (fat)": "fat_g",
    "Fiber, total dietary": "fiber_g",
    "Iron, Fe": "iron_mg",
    "Calcium, Ca": "calcium_mg",
    "Vitamin B-12": "vitamin_b12_mcg",
    "Vitamin D (D2 + D3)": "vitamin_d_mcg",
    "Vitamin D": "vitamin_d_mcg",
    "Zinc, Zn": "zinc_mg",
    "Sodium, Na": "sodium_mg",
    "Potassium, K": "potassium_mg",
    "Magnesium, Mg": "magnesium_mg"
}


def get_api_key():
    api_key = os.getenv("USDA_API_KEY")

    if not api_key:
        raise RuntimeError(
            "USDA_API_KEY was not found. "
            "Set it in your terminal before running this script."
        )

    return api_key


def extract_nutrients(food):
    nutrients = {
        "calories": None,
        "protein_g": None,
        "carbs_g": None,
        "fat_g": None,
        "fiber_g": None,
        "iron_mg": None,
        "calcium_mg": None,
        "vitamin_b12_mcg": None,
        "vitamin_d_mcg": None,
        "zinc_mg": None,
        "sodium_mg": None,
        "potassium_mg": None,
        "magnesium_mg": None
    }

    for nutrient in food.get("foodNutrients", []):
        nutrient_name = nutrient.get("nutrientName")
        value = nutrient.get("value")

        if nutrient_name in NUTRIENT_NAME_MAP:
            output_col = NUTRIENT_NAME_MAP[nutrient_name]
            nutrients[output_col] = value

    return nutrients


def search_foods(api_key, query, page_number):
    payload = {
        "query": query,
        "dataType": DATA_TYPES,
        "pageSize": PAGE_SIZE,
        "pageNumber": page_number,
        "sortBy": "dataType.keyword",
        "sortOrder": "asc"
    }

    params = {
        "api_key": api_key
    }

    response = requests.post(
        API_URL,
        params=params,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def build_snapshot():
    api_key = get_api_key()

    os.makedirs("data", exist_ok=True)

    rows = []
    seen_fdc_ids = set()

    for query in SEARCH_TERMS:
        print(f"\nSearching USDA for: {query}")

        page_number = 1
        term_records = 0

        while term_records < TARGET_RECORDS_PER_TERM:
            try:
                data = search_foods(
                    api_key=api_key,
                    query=query,
                    page_number=page_number
                )
            except Exception as error:
                print(f"Request failed for {query}, page {page_number}: {error}")
                break

            foods = data.get("foods", [])

            if not foods:
                break

            for food in foods:
                description = str(
                    food.get("description", "")
                ).upper()

                brand_owner = str(
                    food.get("brandOwner", "")
                ).upper()

                if (
                    food.get("dataType") == "Branded"
                    and len(description) > 120
                ):
                    continue
                
                fdc_id = food.get("fdcId")

                if fdc_id in seen_fdc_ids:
                    continue

                seen_fdc_ids.add(fdc_id)

                nutrient_values = extract_nutrients(food)

                row = {
                    "fdc_id": fdc_id,
                    "description": food.get("description"),
                    "data_type": food.get("dataType"),
                    "brand_owner": food.get("brandOwner"),
                    "ingredients": food.get("ingredients"),
                    **nutrient_values
                }

                rows.append(row)
                term_records += 1

                if term_records >= TARGET_RECORDS_PER_TERM:
                    break

            print(f"Collected records: {len(rows)}")

            page_number += 1
            time.sleep(0.2)

            if page_number > 50:
                break


    df = pd.DataFrame(rows)

    df = df.drop_duplicates(subset=["fdc_id"])

    nutrient_cols = [
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

    for col in nutrient_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.to_csv(OUTPUT_PATH, index=False)

    print("\nUSDA snapshot created successfully.")
    print(f"Rows saved: {len(df)}")
    print(f"Output path: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_snapshot()