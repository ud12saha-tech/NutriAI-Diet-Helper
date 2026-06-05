import json
import os
import re
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.monashfodmap.com"
RECIPE_INDEX_URL = "https://www.monashfodmap.com/recipe/?page={page}&search=&category="
OUTPUT_PATH = os.path.join("data", "monash_recipes.csv")

TOTAL_PAGES = 33
REQUEST_DELAY_SECONDS = 0.5


def clean_text(value):
    if value is None:
        return ""

    value = str(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_soup(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 NutriAI student project"
        }
    )

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def extract_recipe_links_from_index(page_number):
    """
    Extracts recipe URLs from one Monash recipe listing page.
    """

    url = RECIPE_INDEX_URL.format(page=page_number)
    print(f"Reading recipe index page {page_number}: {url}")

    soup = get_soup(url)

    recipe_links = []

    for blog_box in soup.select(".blog-box"):

        title_tag = blog_box.select_one("h2 a")

        if not title_tag:
            continue

        recipe_name = clean_text(title_tag.get_text())
        relative_url = title_tag.get("href")

        if not relative_url:
            continue

        recipe_url = urljoin(BASE_URL, relative_url)

        serves_text = ""
        cook_text = ""

        serves_tag = blog_box.select_one(".number_of_serves_data")
        cook_tag = blog_box.select_one(".cooking_time_data")

        if serves_tag:
            serves_text = clean_text(serves_tag.get_text())

        if cook_tag:
            cook_text = clean_text(cook_tag.get_text())

        recipe_links.append(
            {
                "recipe_name": recipe_name,
                "recipe_url": recipe_url,
                "servings_text": serves_text,
                "cook_time_text": cook_text,
                "index_page": page_number
            }
        )

    return recipe_links


def extract_json_ld_recipe(soup):
    """
    Extracts the structured Recipe JSON-LD object from a recipe page.
    """

    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        raw_json = script.string

        if not raw_json:
            continue

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict) and data.get("@type") == "Recipe":
            return data

    return None


def parse_number(value):
    """
    Extracts the first number from a string.
    Example: '738.00 cal' -> 738.0
    """

    if value is None:
        return None

    match = re.search(r"[-+]?\d*\.\d+|\d+", str(value))

    if match:
        return float(match.group())

    return None


def parse_recipe_page(recipe_meta):
    """
    Reads one recipe page and extracts ingredients + nutrition.
    """

    recipe_url = recipe_meta["recipe_url"]
    print(f"  Reading recipe: {recipe_meta['recipe_name']}")

    soup = get_soup(recipe_url)

    recipe_json = extract_json_ld_recipe(soup)

    if recipe_json is None:
        return {
            **recipe_meta,
            "description": "",
            "ingredients": "",
            "instructions": "",
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fat_g": None,
            "fiber_g": None,
            "sugar_g": None,
            "is_low_fodmap": True,
            "parse_status": "missing_json_ld"
        }

    ingredients = recipe_json.get("recipeIngredient", [])

    instructions_raw = recipe_json.get("recipeInstructions", [])

    instruction_texts = []

    for step in instructions_raw:
        if isinstance(step, dict):
            text = clean_text(step.get("text", ""))
            if text:
                instruction_texts.append(text)

    nutrition = recipe_json.get("nutrition", {})

    row = {
        **recipe_meta,
        "description": clean_text(recipe_json.get("description")),
        "recipe_yield": clean_text(recipe_json.get("recipeYield")),
        "prep_time": clean_text(recipe_json.get("prepTime")),
        "cook_time": clean_text(recipe_json.get("cookTime")),
        "total_time": clean_text(recipe_json.get("totalTime")),
        "ingredients": " | ".join([clean_text(x) for x in ingredients]),
        "instructions": " | ".join(instruction_texts),
        "calories": parse_number(nutrition.get("calories")),
        "protein_g": parse_number(nutrition.get("proteinContent")),
        "carbs_g": parse_number(nutrition.get("carbohydrateContent")),
        "fat_g": parse_number(nutrition.get("fatContent")),
        "fiber_g": parse_number(nutrition.get("fiberContent")),
        "sugar_g": parse_number(nutrition.get("sugarContent")),
        "is_low_fodmap": True,
        "parse_status": "ok"
    }

    return row


def build_monash_dataset():
    os.makedirs("data", exist_ok=True)

    recipe_metas = []

    for page_number in range(1, TOTAL_PAGES + 1):
        try:
            page_recipes = extract_recipe_links_from_index(page_number)
            recipe_metas.extend(page_recipes)
        except Exception as error:
            print(f"Failed index page {page_number}: {error}")

        time.sleep(REQUEST_DELAY_SECONDS)

    # Deduplicate by URL
    unique_recipe_metas = {}

    for recipe in recipe_metas:
        unique_recipe_metas[recipe["recipe_url"]] = recipe

    recipe_metas = list(unique_recipe_metas.values())

    print(f"\nRecipe links found: {len(recipe_metas)}")

    rows = []

    for recipe_meta in recipe_metas:
        try:
            row = parse_recipe_page(recipe_meta)
            rows.append(row)
        except Exception as error:
            rows.append(
                {
                    **recipe_meta,
                    "description": "",
                    "ingredients": "",
                    "instructions": "",
                    "calories": None,
                    "protein_g": None,
                    "carbs_g": None,
                    "fat_g": None,
                    "fiber_g": None,
                    "sugar_g": None,
                    "is_low_fodmap": True,
                    "parse_status": f"error: {error}"
                }
            )

        time.sleep(REQUEST_DELAY_SECONDS)

    df = pd.DataFrame(rows)

    df = df.drop_duplicates(subset=["recipe_url"])

    df.to_csv(OUTPUT_PATH, index=False)

    print("\nMonash recipe dataset created.")
    print(f"Rows saved: {len(df)}")
    print(f"Output path: {OUTPUT_PATH}")

    print("\nParse status counts:")
    print(df["parse_status"].value_counts())


if __name__ == "__main__":
    build_monash_dataset()