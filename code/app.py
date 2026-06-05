import streamlit as st
import pandas as pd
import os
import time

from filters import (
    apply_clinical_filters,
    apply_allergy_filters,
    apply_diet_filters
)

from planner import generate_7_day_plan

from retrieval import (
    retrieve_similar_meals
)

from nutrition import (
    calculate_daily_totals,
    calculate_diversity_score,
    compare_to_rda,
    generate_deficiency_snacks
)

from exports import (
    build_explainability_summary,
    convert_plan_to_csv
)

# --------------------------------------------------
# Page setup
# --------------------------------------------------
st.set_page_config(
    page_title="NutriAI Diet Helper",
    page_icon="🥗",
    layout="wide"
)


# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEALS_PATH = os.path.join(DATA_DIR, "expanded_meals.csv")


# --------------------------------------------------
# Persona presets
# --------------------------------------------------
PERSONAS = {
    "Custom User": {
        "age": 25,
        "sex": "Female",
        "diet": "Vegetarian",
        "conditions": [],
        "allergies": [],
        "calories": 2000,
        "notes": ""
    },

    "Priya — IBS + Vegetarian + Lactose Intolerant": {
        "age": 25,
        "sex": "Female",
        "diet": "Vegetarian",
        "conditions": ["IBS"],
        "allergies": ["Dairy"],
        "calories": 1800,
        "notes": "Must avoid high-FODMAP foods, dairy, meat, and fish."
    },

    "Ravi — GERD + Non-Veg + Gluten-Free": {
        "age": 30,
        "sex": "Male",
        "diet": "Non-Vegetarian",
        "conditions": ["GERD / Acid Reflux"],
        "allergies": ["Gluten"],
        "calories": 2200,
        "notes": "Must avoid GERD triggers, gluten, pork, and cross-contamination."
    },

    "Mei — Diabetes + Vegan + Tree Nut Allergy": {
        "age": 28,
        "sex": "Female",
        "diet": "Vegan",
        "conditions": ["Type 2 Diabetes"],
        "allergies": ["Tree Nuts"],
        "calories": 1600,
        "notes": "Must keep meals low-GI, vegan, nut-free, and high-fiber."
    },

    "James — Hypertension + Pescatarian + Soy Allergy": {
        "age": 40,
        "sex": "Male",
        "diet": "Pescatarian",
        "conditions": ["Hypertension"],
        "allergies": ["Soy"],
        "calories": 2000,
        "notes": "Must follow low-sodium DASH-style rules and avoid soy."
    }
}

DIET_OPTIONS = [
    "Vegetarian",
    "Vegan",
    "Non-Vegetarian",
    "Pescatarian"
]

CONDITION_OPTIONS = [
    "IBS",
    "GERD / Acid Reflux",
    "Type 2 Diabetes",
    "Hypertension"
]

ALLERGY_OPTIONS = [
    "Gluten",
    "Dairy",
    "Tree Nuts",
    "Soy",
    "Shellfish",
    "Eggs"
]


# --------------------------------------------------
# Helper functions
# --------------------------------------------------
def clean_list_display(items):
    if not items:
        return "None"
    return ", ".join(items)


def validate_profile(age, sex, diet, conditions, allergies, calorie_target):
    errors = []
    warnings = []

    if age < 1 or age > 100:
        errors.append("Age must be between 1 and 100.")

    if sex not in ["Female", "Male"]:
        errors.append("Please select a valid sex.")

    if diet not in DIET_OPTIONS:
        errors.append("Please select a valid diet preference.")

    if calorie_target < 1000 or calorie_target > 4000:
        errors.append(
            "Daily calorie target should be between 1,000 and 4,000 calories."
        )

    if len(conditions) == 0:
        warnings.append(
            "No clinical condition selected. Clinical filtering will be minimal."
        )

    if len(allergies) == 0:
        warnings.append(
            "No allergies selected. Allergy filtering will not remove any foods."
        )

    return errors, warnings


@st.cache_data
def load_meals():
    if not os.path.exists(MEALS_PATH):
        return None

    meals_df = pd.read_csv(MEALS_PATH)

    for col in meals_df.columns:
        if meals_df[col].dtype == object:
            unique_values = set(
                meals_df[col].dropna().astype(str).str.upper().unique()
            )

            if unique_values.issubset({"TRUE", "FALSE"}):
                meals_df[col] = meals_df[col].astype(str).str.upper().map(
                    {"TRUE": True, "FALSE": False}
                )

    return meals_df


# --------------------------------------------------
# App header
# --------------------------------------------------
st.title("🥗 NutriAI Diet Helper")
st.subheader("Automated Diet Plan Builder for Personalized Clinical Nutrition")

st.write(
    "NutriAI generates a personalized 7-day meal plan based on clinical conditions, "
    "allergies, diet preferences, and nutrition targets."
)

st.info(
    "Current build step: 7-day meal generation. "
    "The app now filters unsafe meals and assigns safe options across the week."
)


# --------------------------------------------------
# Load data
# --------------------------------------------------
meals_df = load_meals()

if meals_df is None:
    st.error(
        "Could not find data/meals.csv. Please create the file before continuing."
    )
    st.stop()


# --------------------------------------------------
# Sidebar intake form
# --------------------------------------------------
st.sidebar.header("User Intake")

selected_persona = st.sidebar.selectbox(
    "Choose test persona or custom user",
    list(PERSONAS.keys())
)

persona_data = PERSONAS[selected_persona]

st.sidebar.caption(
    "Use the provided personas for testing, or choose Custom User to simulate hidden personas."
)

age = st.sidebar.number_input(
    "Age",
    min_value=1,
    max_value=100,
    value=persona_data["age"]
)

sex = st.sidebar.selectbox(
    "Sex",
    ["Female", "Male"],
    index=["Female", "Male"].index(persona_data["sex"])
)

diet = st.sidebar.selectbox(
    "Diet Preference",
    DIET_OPTIONS,
    index=DIET_OPTIONS.index(persona_data["diet"])
)

conditions = st.sidebar.multiselect(
    "Clinical Conditions",
    CONDITION_OPTIONS,
    default=persona_data["conditions"]
)

allergies = st.sidebar.multiselect(
    "Allergies / Intolerances",
    ALLERGY_OPTIONS,
    default=persona_data["allergies"]
)

calorie_target = st.sidebar.number_input(
    "Daily Calorie Target",
    min_value=1000,
    max_value=4000,
    value=persona_data["calories"],
    step=100
)

special_notes = st.sidebar.text_area(
    "Optional Constraints",
    value=persona_data["notes"],
    placeholder="Example: no pork, no beef, prefers dairy-free breakfast"
)

generate_clicked = st.sidebar.button("Generate Diet Plan")


# --------------------------------------------------
# Main layout
# --------------------------------------------------
left_col, right_col = st.columns([1, 1])

with left_col:
    st.header("Profile Summary")

    st.write("**Selected Persona:**", selected_persona)
    st.write("**Age:**", age)
    st.write("**Sex:**", sex)
    st.write("**Diet Preference:**", diet)
    st.write("**Clinical Conditions:**", clean_list_display(conditions))
    st.write("**Allergies / Intolerances:**", clean_list_display(allergies))
    st.write("**Daily Calorie Target:**", f"{calorie_target:,} kcal")

    if special_notes.strip():
        st.write("**Additional Notes:**", special_notes)

with right_col:
    st.header("Data Check")

    st.metric("Meals loaded", len(meals_df))

    with st.expander("Preview starter meals"):
        st.dataframe(
            meals_df[
                [
                    "meal_name",
                    "meal_type",
                    "ingredients",
                    "gi_score",
                    "sodium_mg"
                ]
            ],
            use_container_width=True
        )


# --------------------------------------------------
# Generate plan
# --------------------------------------------------
if generate_clicked:
    start_time = time.time()

    st.divider()
    st.header("Generation Status")

    errors, warnings = validate_profile(
        age=age,
        sex=sex,
        diet=diet,
        conditions=conditions,
        allergies=allergies,
        calorie_target=calorie_target
    )

    if errors:
        st.error("Please fix the following issues before generating a plan:")
        for error in errors:
            st.write(f"- {error}")

    else:
        st.success("Profile validated successfully.")

        if warnings:
            st.warning("Warnings:")
            for warning in warnings:
                st.write(f"- {warning}")

        # -----------------------------------------
        # Clinical filtering
        # -----------------------------------------
        clinical_filtered_meals, clinical_exclusions = apply_clinical_filters(
            meals_df=meals_df,
            conditions=conditions
        )

        # -----------------------------------------
        # Allergy filtering
        # -----------------------------------------
        allergy_filtered_meals, allergy_exclusions = apply_allergy_filters(
            meals_df=clinical_filtered_meals,
            allergies=allergies
        )

        # -----------------------------------------
        # Diet filtering
        # -----------------------------------------
        filtered_meals, diet_exclusions = apply_diet_filters(
            meals_df=allergy_filtered_meals,
            diet=diet,
            notes=special_notes
        )

        exclusion_log = (
            clinical_exclusions
            + allergy_exclusions
            + diet_exclusions
        )

        # -----------------------------------------
        # Meal generation
        # -----------------------------------------
        query_text = " ".join([
            diet,
            " ".join(conditions),
            " ".join(allergies),
            special_notes
        ])

        retrieved_meals_df = (
            retrieve_similar_meals(
                meals_df=filtered_meals,
                query_text=query_text,
                top_k=min(
                    75,
                    len(filtered_meals)
                )
            )
        )

        plan_df, generation_warnings = (
            generate_7_day_plan(
                filtered_meals_df=retrieved_meals_df,
                calorie_target=calorie_target
            )
        )
        
        ## Diversity + Nutrition ##
        diversity_score = calculate_diversity_score(
            plan_df
        ) 

        daily_totals_df = calculate_daily_totals(
            plan_df
        )

        rda_comparison_df, rda_warnings = compare_to_rda(
            daily_totals_df=daily_totals_df,
            sex=sex,
            age=age
        )

        snack_recommendations_df = (
            generate_deficiency_snacks(
                rda_warnings
            )
        )

        ## Explainability summary ##
        explainability_summary = (
            build_explainability_summary(
                persona_name=selected_persona,
                conditions=conditions,
                allergies=allergies,
                diet=diet,
                notes=special_notes,
                exclusion_log=exclusion_log
            )
        )

        end_time = time.time()
        generation_time = end_time - start_time

        st.subheader("Pipeline Metrics")

        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

        with metric_col1:
            st.metric("Original meals", len(meals_df))

        with metric_col2:
            st.metric("Safe meals", len(filtered_meals))

        with metric_col3:
            st.metric(
                "FAISS Retrieved",
                len(retrieved_meals_df)
            )

        with metric_col4:
            st.metric(
                "Meals removed",
                len(meals_df) - len(filtered_meals)
            )

        with metric_col5:
            st.metric(
                "Generation time",
                f"{generation_time:.2f}s"
            )

        if generation_time <= 60:
            st.success("Generation completed under 60 seconds.")
        else:
            st.error("Generation exceeded the 60-second requirement.")

        if generation_warnings:
            st.warning("Meal generation warnings:")
            for warning in generation_warnings:
                st.write(f"- {warning}")

        st.subheader("7-Day Meal Plan")

        if plan_df.empty:
            st.error(
                "No meal plan could be generated. "
                "More safe meal options are needed for this profile."
            )
        else:
            st.dataframe(
                plan_df[
                    [
                        "day",
                        "planned_meal_type",
                        "meal_name",
                        "category",
                        "cuisine",
                        "calories",
                        "protein_g",
                        "carbs_g",
                        "fat_g",
                        "fiber_g"
                    ]
                ],
                use_container_width=True
            )

        # -----------------------------------------
        # Diversity score
        # -----------------------------------------
        st.subheader("Diversity Score")

        st.metric(
            "Meal Diversity Score",
            diversity_score
        )

        if diversity_score >= 0.7:
            st.success(
                "Diversity score meets the ≥0.7 goal."
            )
        else:
            st.warning(
                "Diversity score is below 0.7. "
                "More meal variety is needed."
            )

        # -----------------------------------------
        # Daily nutrition totals
        # -----------------------------------------
        with st.expander(
            "Daily Nutrition Totals"
        ):

            if not daily_totals_df.empty:
                st.dataframe(
                    daily_totals_df,
                    use_container_width=True
                )
        # -----------------------------------------
        # RDA comparison
        # -----------------------------------------
        with st.expander(
            "RDA Comparison"
        ):

            if not rda_comparison_df.empty:

                st.dataframe(
                    rda_comparison_df,
                    use_container_width=True
                )

        # -----------------------------------------
        # Nutrient warnings
        # -----------------------------------------
        st.subheader(
            "Suggested Corrective Snacks"
        )

        if snack_recommendations_df.empty:

            st.success(
                "No nutrient deficiencies detected."
            )

        else:

            snack_recommendations_df = (
                snack_recommendations_df.rename(
                    columns={
                        "day": "Day",
                        "deficiency": "Nutrient Deficiency",
                        "recommended_snacks": "Suggested Snacks"
                    }
                )
            )

            st.dataframe(
                snack_recommendations_df,
                use_container_width=True
            )

        with st.expander(
            "View Detailed Deficiency Warnings"
        ):

            if not rda_warnings:

                st.write(
                    "No deficiency warnings."
                )

            else:

                from collections import defaultdict

                grouped_warnings = defaultdict(list)

                for warning in rda_warnings:

                    day = warning.split(":")[0]

                    nutrient = (
                        warning.split(":")[1]
                        .split("below")[0]
                        .strip()
                    )

                    grouped_warnings[day].append(
                        nutrient
                    )

                for day, nutrients in grouped_warnings.items():

                    st.markdown(f"### {day}")

                    for nutrient in nutrients:

                        st.write(f"• {nutrient}")
        # -----------------------------------------
        # Explainability
        # -----------------------------------------
        st.subheader(
            "Why This Plan Was Generated"
        )

        st.text(
            explainability_summary
        )

        # -----------------------------------------
        # CSV Export
        # -----------------------------------------
        if not plan_df.empty:

            csv_bytes = (
                convert_plan_to_csv(
                    plan_df
                )
            )

            st.download_button(
                label="Download Meal Plan CSV",
                data=csv_bytes,
                file_name="nutriai_meal_plan.csv",
                mime="text/csv"
            )

        with st.expander("Safe Meals After All Filters"):

            if filtered_meals.empty:
                st.error("No meals passed all filters.")
            else:
                st.dataframe(
                    filtered_meals[
                        [
                            "meal_name",
                            "meal_type",
                            "category",
                            "ingredients",
                            "calories",
                            "gi_score",
                            "sodium_mg"
                        ]
                    ],
                    use_container_width=True
                )

        with st.expander("Excluded Meals & Reasons"):

            if exclusion_log:
                exclusion_df = pd.DataFrame(exclusion_log)
                st.dataframe(exclusion_df, use_container_width=True)
            else:
                st.info("No meals were removed by filters.")

        st.info(
            "Current build includes clinical filtering, dietary filtering, "
            "FAISS-based meal retrieval, ranking-based meal recommendation, "
            "nutrition analysis, and nutrient deficiency snack recommendations."
        )