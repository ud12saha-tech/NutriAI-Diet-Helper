import faiss
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# Model loading
# --------------------------------------------------
# The model is loaded ONCE the first time it is needed and then
# reused. This avoids reloading the (large) embedding model on
# every Streamlit rerun, which is slow and wastes memory.
# --------------------------------------------------

MODEL = None
MODEL_NAME = "all-MiniLM-L6-v2"


def get_model():
    global MODEL

    if MODEL is None:
        MODEL = SentenceTransformer(MODEL_NAME)

    return MODEL


def build_meal_text(row):

    return " ".join([
        str(row.get("meal_name", "")),
        str(row.get("category", "")),
        str(row.get("cuisine", "")),
        str(row.get("ingredients", ""))
    ])


def create_faiss_index(meals_df):

    model = get_model()

    texts = meals_df.apply(
        build_meal_text,
        axis=1
    ).tolist()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    return index, texts


def retrieve_similar_meals(
    meals_df,
    query_text,
    top_k=50
):

    if meals_df.empty:
        return meals_df

    model = get_model()

    index, texts = create_faiss_index(meals_df)

    query_embedding = model.encode(
        [query_text],
        convert_to_numpy=True
    )

    query_embedding = query_embedding.astype("float32")

    # Never request more neighbours than there are meals,
    # otherwise FAISS returns -1 indices and the .iloc lookup breaks.
    effective_k = min(top_k, len(meals_df))

    distances, indices = index.search(
        query_embedding,
        effective_k
    )

    return meals_df.iloc[indices[0]].copy()