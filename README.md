# NutriAI Diet Helper

## Overview

NutriAI is a personalized nutrition recommendation system that generates 7-day meal plans based on clinical conditions, allergies, dietary preferences, calorie targets, and nutrient requirements.

The application integrates:

* USDA FoodData Central
* NIH Dietary Reference Intake (RDA) tables
* Monash Low-FODMAP resources

The system supports users with:

* IBS
* GERD
* Type 2 Diabetes
* Hypertension
* Common food allergies and intolerances

## BAX-423 Techniques

This project incorporates two BAX-423 techniques:

1. Embedding-Based Retrieval (FAISS)
2. Ranking-Based Recommendation

## Project Structure

* `code/` – application logic
* `data/` – datasets and reference tables
* `scripts/` – data ingestion and preprocessing scripts
* `docs/` – technical brief
* `outputs/` – generated outputs

## Installation

Install required packages:

```bash
pip install -r requirements.txt
```

## Run Application

```bash
streamlit run code/app.py
```

## Test Personas

* Priya (IBS + Vegetarian + Dairy Intolerance)
* Ravi (GERD + Gluten-Free)
* Mei (Type 2 Diabetes + Vegan + Tree Nut Allergy)
* James (Hypertension + Pescatarian + Soy Allergy)

## Public Deployment

https://nutriai-diet-apper-sqzqn5dhkxsiam2ednwfhd.streamlit.app/
