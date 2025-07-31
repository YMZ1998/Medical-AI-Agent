import logging
import os
from http import HTTPStatus
from typing import Dict, Optional
from typing import Generator, List

import dashscope
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

EMBEDDING_MODELS = {
    "text_embedding_v1": dashscope.TextEmbedding.Models.text_embedding_v1,
    "text_embedding_v2": dashscope.TextEmbedding.Models.text_embedding_v2,
    "text_embedding_v3": dashscope.TextEmbedding.Models.text_embedding_v3,
    "text_embedding_v4": dashscope.TextEmbedding.Models.text_embedding_v4,
}
# 最多支持25条，每条最长支持2048tokens
DASHSCOPE_MAX_BATCH_SIZE = 25

def batched(inputs: List,
            batch_size: int = DASHSCOPE_MAX_BATCH_SIZE) -> Generator[List, None, None]:
    for i in range(0, len(inputs), batch_size):
        yield inputs[i:i + batch_size]


class TongyiEmbeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "text_embedding_v2",
        dashscope_api_key: Optional[str] = None,
        retry_count: int = 3,
    ):
        self.model_name = model_name
        self.dashscope_api_key = dashscope_api_key or os.getenv("DASHSCOPE_API_KEY")
        self.retry_count = retry_count

        try:
            import dashscope
            self.dashscope = dashscope
        except ImportError:
            raise ImportError(
                "Could not import dashscope python package. "
                "Please install it with `pip install dashscope --upgrade`."
            )

    def _embeb_retry(self, texts: List[str]) -> List[Dict]:
        embeddings = None
        for _ in range(self.retry_count):
            resp = self.dashscope.TextEmbedding.call(
                model=EMBEDDING_MODELS[self.model_name],
                input=texts
            )
            if resp.status_code != HTTPStatus.OK:
                logging.error(resp.message)
                continue
            embeddings = resp.output['embeddings']
            break

        if embeddings is None:
            raise RuntimeError("TongyiEmbeddings failed after retries")

        return embeddings

    def _embed(self, texts: List[str]) -> List[List[float]]:
        result = []
        batch_counter = 0
        for batch in batched(texts):
            batch_emb = self._embeb_retry(batch)
            for emb in batch_emb:
                emb['text_index'] += batch_counter
                result.append(emb)
            batch_counter += len(batch)

        sorted_embeddings = sorted(result, key=lambda e: e["text_index"])
        return [e["embedding"] for e in sorted_embeddings]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]
