import os

import openai
from langchain.evaluation import load_evaluator
from langchain_openai import OpenAIEmbeddings

from api_config import api_config

dashscope_api_key = api_config.get_api_key()
openai.api_key = os.environ['OPENAI_API_KEY']

def main():
    # Get embedding for a word.
    embedding_function = OpenAIEmbeddings()
    vector = embedding_function.embed_query("apple")
    print(f"Vector for 'apple': {vector}")
    print(f"Vector length: {len(vector)}")

    # Compare vector of two words
    evaluator = load_evaluator("pairwise_embedding_distance")
    words = ("apple", "iphone")
    x = evaluator.evaluate_string_pairs(prediction=words[0], prediction_b=words[1])
    print(f"Comparing ({words[0]}, {words[1]}): {x}")


if __name__ == "__main__":
    main()
