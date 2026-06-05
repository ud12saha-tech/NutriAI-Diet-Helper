import faiss
import numpy as np
import pandas as pd

from sentence_transformers import (
    SentenceTransformer
)

MODEL = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def build_meal_text(row):

    return " ".join([
        str(row.get("meal_name", "")),
        str(row.get("category", "")),
        str(row.get("cuisine", "")),
        str(row.get("ingredients", ""))
    ])


def create_faiss_index(meals_df):

    texts = meals_df.apply(
        build_meal_text,
        axis=1
    ).tolist()

    embeddings = MODEL.encode(
        texts,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype(
        "float32"
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

    return index, texts


def retrieve_similar_meals(
    meals_df,
    query_text,
    top_k=50
):

    if meals_df.empty:
        return meals_df

    index, texts = create_faiss_index(
        meals_df
    )

    query_embedding = MODEL.encode(
        [query_text],
        convert_to_numpy=True
    )

    query_embedding = (
        query_embedding
        .astype("float32")
    )

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    return meals_df.iloc[
        indices[0]
    ].copy()