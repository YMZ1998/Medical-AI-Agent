import os
from typing import Any, Dict, List, Optional

import logging
import requests
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, SecretStr, root_validator, model_validator
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env

from typing import Generator, List
import dashscope
from http import HTTPStatus

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


class TongyiEmbeddings(BaseModel, Embeddings):
    """Tongyi embedding models."""

    model_name: str = "text_embedding_v4"
    dashscope_api_key: Optional[SecretStr] = None
    retry_count: int = 3
    @property
    def lc_secrets(self) -> Dict[str, str]:
        return {"dashscope_api_key": "DASHSCOPE_API_KEY"}

    @model_validator(mode="after")
    def validate_environment(self):
        # 从实例属性或环境变量中获取 key，并转成 SecretStr
        key = get_from_dict_or_env(self.__dict__, "dashscope_api_key", "DASHSCOPE_API_KEY")
        self.dashscope_api_key = convert_to_secret_str(key)

        # 检查 dashscope 包是否存在
        try:
            import dashscope
        except ImportError:
            raise ImportError(
                "Could not import dashscope python package. "
                "Please install it with `pip install dashscope --upgrade`."
            )

        return self

    def _embeb_retry(self, texts: List) -> Dict:
        embeddings = None
        for _ in range(self.retry_count):
            resp = dashscope.TextEmbedding.call(
                model=EMBEDDING_MODELS[self.model_name],
                input=texts)

            if resp.status_code != HTTPStatus.OK:
                logging.error(resp.message)
                continue

            embeddings = resp.output['embeddings']
            break

        if embeddings is None:
            raise RuntimeError(f"TongyiEmbeddings' failed up to {self.retry_count} times")

        return embeddings

    def _embed(self, texts: List[str]) -> List[List[float]]:
        # Call Tongyi Embedding SDK
        result = None  # merge the results.
        batch_counter = 0
        for batch in batched(texts):
            batch_emb = self._embeb_retry(batch)
            if result is None:
                result = batch_emb
            else:
                for emb in batch_emb:
                    emb['text_index'] += batch_counter
                    result.append(emb)
            batch_counter += len(batch)

        # Sort resulting embeddings by index
        sorted_embeddings = sorted(result, key=lambda e: e["text_index"])  # type: ignore

        # Return just the embeddings
        return [result["embedding"] for result in sorted_embeddings]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Call out to Jina's embedding endpoint.
        Args:
            texts: The list of texts to embed.
        Returns:
            List of embeddings, one for each text.
        """
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        """Call out to Jina's embedding endpoint.
        Args:
            text: The text to embed.
        Returns:
            Embeddings for the text.
        """
        return self._embed([text])[0]