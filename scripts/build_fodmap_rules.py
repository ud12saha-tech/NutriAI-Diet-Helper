import pandas as pd
import os

OUTPUT_PATH = os.path.join(
    "data",
    "fodmap_rules.csv"
)

# --------------------------------------------------
# HIGH FODMAP
# --------------------------------------------------

HIGH_FODMAP = {

    "vegetable": [
        "garlic","onion","shallot","leek","cauliflower",
        "artichoke","asparagus","mushroom","snow peas",
        "beetroot","fennel","savoy cabbage","brussels sprouts",
        "spring onion","scallion","green onion","broccoli stem",
        "okra","celery","sweet corn","cabbage"
    ],

    "fruit": [
        "apple","pear","mango","watermelon","cherry",
        "peach","nectarine","plum","apricot","blackberry",
        "lychee","persimmon","fig","guava","date",
        "prune","raisin","dried apricot","fruit cocktail",
        "boysenberry"
    ],

    "grain": [
        "wheat","rye","barley","bulgur","couscous",
        "wheat flour","whole wheat","bran","farro",
        "spelt"
    ],

    "legume": [
        "baked beans","kidney beans","black beans",
        "lentils","chickpeas","split peas","navy beans",
        "butter beans","soybeans","edamame",
        "pinto beans","cannellini beans"
    ],

    "dairy": [
        "milk","ice cream","soft cheese","cottage cheese",
        "yogurt","evaporated milk","condensed milk",
        "ricotta","custard","cream cheese",
        "buttermilk","sour cream"
    ],

    "sweetener": [
        "honey","high fructose corn syrup","agave",
        "molasses","sorbitol","mannitol","xylitol",
        "isomalt","maltitol","fructose"
    ],

    "beverage": [
        "apple juice","pear juice","mango juice",
        "chamomile tea","soy milk","oat milk concentrate",
        "rum","dessert wine"
    ],

    "condiment": [
        "garlic powder","onion powder","garlic salt",
        "onion flakes","bbq sauce","sweet chili sauce",
        "honey mustard","teriyaki sauce"
    ]
}


# --------------------------------------------------
# LOW FODMAP
# --------------------------------------------------

LOW_FODMAP = {

    "vegetable": [
        "spinach","carrot","cucumber","zucchini",
        "bell pepper","tomato","eggplant","potato",
        "sweet potato","lettuce","kale","green beans",
        "bok choy","pumpkin","radish","parsnip",
        "chives","arugula","collard greens","mustard greens",
        "turnip","watercress","endive","swiss chard",
        "spaghetti squash","acorn squash","butternut squash"
    ],

    "fruit": [
        "banana","blueberry","strawberry","orange",
        "kiwi","pineapple","grape","raspberry",
        "cantaloupe","honeydew","papaya","dragonfruit",
        "passionfruit","lime","lemon","clementine",
        "mandarin","cranberry","starfruit","jackfruit"
    ],

    "grain": [
        "rice","oats","quinoa","corn",
        "polenta","millet","buckwheat",
        "gluten free bread","rice noodles",
        "corn tortillas","rice cakes",
        "brown rice","wild rice"
    ],

    "protein": [
        "chicken","turkey","beef","salmon",
        "tuna","cod","egg","shrimp",
        "crab","lobster","halibut",
        "tilapia","trout","sardine",
        "anchovy","lamb","pork",
        "duck","venison","bison"
    ],

    "dairy": [
        "lactose free milk","hard cheese",
        "parmesan","cheddar","swiss cheese",
        "goat cheese","brie","feta"
    ],

    "nut_seed": [
        "chia","flaxseed","pumpkin seed",
        "walnut","pecan","macadamia",
        "sesame","sunflower seed",
        "hemp seed","pine nut"
    ],

    "beverage": [
        "green tea","black tea","coffee",
        "water","sparkling water",
        "orange juice","cranberry juice"
    ],

    "condiment": [
        "olive oil","vinegar","mustard",
        "basil","oregano","thyme",
        "rosemary","parsley","cilantro",
        "turmeric","cumin","paprika",
        "ginger","black pepper"
    ]
}


# --------------------------------------------------
# Variations
# --------------------------------------------------

def expand_variations(food):

    variations = {
        food,
        food.lower(),
        food.title()
    }

    words = food.split()

    if len(words) == 1:

        variations.add(f"fresh {food}")
        variations.add(f"raw {food}")
        variations.add(f"dried {food}")
        variations.add(f"organic {food}")

    return list(variations)


# --------------------------------------------------
# Build dataset
# --------------------------------------------------

def build_dataset():

    rows = []

    for category, foods in HIGH_FODMAP.items():

        for food in foods:

            for variation in expand_variations(food):

                rows.append({
                    "ingredient": variation,
                    "fodmap_level": "HIGH",
                    "fodmap_group": "Monash-derived",
                    "category": category
                })

    for category, foods in LOW_FODMAP.items():

        for food in foods:

            for variation in expand_variations(food):

                rows.append({
                    "ingredient": variation,
                    "fodmap_level": "LOW",
                    "fodmap_group": "None",
                    "category": category
                })

    df = pd.DataFrame(rows)

    df = df.drop_duplicates(
        subset=["ingredient"]
    )

    os.makedirs(
        "data",
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"FODMAP dataset created with "
        f"{len(df)} ingredients."
    )


if __name__ == "__main__":
    build_dataset()