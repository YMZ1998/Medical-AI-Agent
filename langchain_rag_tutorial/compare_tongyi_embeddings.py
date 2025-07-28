import os

from langchain.evaluation import load_evaluator

from API import get_dashscope_api_key
from embeddings import TongyiEmbeddings

dashscope_api_key = get_dashscope_api_key()

def main():
    # 初始化 Tongyi Embeddings
    embedding_function = TongyiEmbeddings(dashscope_api_key=os.environ['DASHSCOPE_API_KEY'])

    # 获取单词的 embedding
    vector = embedding_function.embed_query("apple")
    print(f"Vector for 'apple': {vector}")
    print(f"Vector length: {len(vector)}")

    # 比较两个词的 embedding 距离
    evaluator = load_evaluator("pairwise_embedding_distance", embeddings=embedding_function)
    words = ("apple", "iphone")
    result = evaluator.evaluate_string_pairs(prediction=words[0], prediction_b=words[1])
    print(f"Comparing ({words[0]}, {words[1]}): {result}")

    texts = [
        "你好吗",
        "你的名字是什么",
        "我的肚子好痛啊",
        "肠胃不舒服",
        "我在吃东西"
    ]
    embeddings = embedding_function.embed_documents(texts)

    print(len(embeddings), len(embeddings[0]))

    import numpy as np

    def normalize(x):
        x = np.asarray(x)
        norms = np.sum(np.multiply(x, x))
        norms = np.sqrt(norms)
        return x / norms

    for i in range(5):
        similarity = np.dot(normalize(embeddings[2]), normalize(embeddings[i]))
        print(f'"{texts[2]}"与"{texts[i]}"的语义相似度为：{similarity}')


if __name__ == "__main__":
    main()
