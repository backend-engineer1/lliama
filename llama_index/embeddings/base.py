"""Base embeddings file."""

import asyncio
from abc import abstractmethod
from enum import Enum
from typing import Callable, Coroutine, List, Optional, Tuple

import numpy as np

from llama_index.bridge.pydantic import Field, validator, PrivateAttr
from llama_index.callbacks.base import CallbackManager
from llama_index.callbacks.schema import CBEventType, EventPayload
from llama_index.schema import BaseComponent
from llama_index.utils import get_tqdm_iterable

# TODO: change to numpy array
EMB_TYPE = List

DEFAULT_EMBED_BATCH_SIZE = 10


class SimilarityMode(str, Enum):
    """Modes for similarity/distance."""

    DEFAULT = "cosine"
    DOT_PRODUCT = "dot_product"
    EUCLIDEAN = "euclidean"


def mean_agg(embeddings: List[List[float]]) -> List[float]:
    """Mean aggregation for embeddings."""
    return list(np.array(embeddings).mean(axis=0))


def similarity(
    embedding1: EMB_TYPE,
    embedding2: EMB_TYPE,
    mode: SimilarityMode = SimilarityMode.DEFAULT,
) -> float:
    """Get embedding similarity."""
    if mode == SimilarityMode.EUCLIDEAN:
        # Using -euclidean distance as similarity to achieve same ranking order
        return -float(np.linalg.norm(np.array(embedding1) - np.array(embedding2)))
    elif mode == SimilarityMode.DOT_PRODUCT:
        product = np.dot(embedding1, embedding2)
        return product
    else:
        product = np.dot(embedding1, embedding2)
        norm = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        return product / norm


class BaseEmbedding(BaseComponent):
    """Base class for embeddings."""

    model_name: str = Field(
        default="unknown", description="The name of the embedding model."
    )
    embed_batch_size: int = Field(
        default=DEFAULT_EMBED_BATCH_SIZE,
        description="The batch size for embedding calls.",
    )
    callback_manager: CallbackManager = Field(
        default_factory=lambda: CallbackManager([]), exclude=True
    )
    _text_queue: List[Tuple[str, str]] = PrivateAttr(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    @validator("callback_manager", pre=True)
    def _validate_callback_manager(
        cls, v: Optional[CallbackManager]
    ) -> CallbackManager:
        if v is None:
            return CallbackManager([])
        return v

    @abstractmethod
    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding."""

    @abstractmethod
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Get query embedding asynchronously."""

    def get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding."""
        with self.callback_manager.event(
            CBEventType.EMBEDDING, payload={EventPayload.SERIALIZED: self.to_dict()}
        ) as event:
            query_embedding = self._get_query_embedding(query)

            event.on_end(
                payload={
                    EventPayload.CHUNKS: [query],
                    EventPayload.EMBEDDINGS: [query_embedding],
                },
            )
        return query_embedding

    async def aget_query_embedding(self, query: str) -> List[float]:
        """Get query embedding."""
        with self.callback_manager.event(
            CBEventType.EMBEDDING, payload={EventPayload.SERIALIZED: self.to_dict()}
        ) as event:
            query_embedding = await self._aget_query_embedding(query)

            event.on_end(
                payload={
                    EventPayload.CHUNKS: [query],
                    EventPayload.EMBEDDINGS: [query_embedding],
                },
            )
        return query_embedding

    def get_agg_embedding_from_queries(
        self,
        queries: List[str],
        agg_fn: Optional[Callable[..., List[float]]] = None,
    ) -> List[float]:
        """Get aggregated embedding from multiple queries."""
        query_embeddings = [self.get_query_embedding(query) for query in queries]
        agg_fn = agg_fn or mean_agg
        return agg_fn(query_embeddings)

    async def aget_agg_embedding_from_queries(
        self,
        queries: List[str],
        agg_fn: Optional[Callable[..., List[float]]] = None,
    ) -> List[float]:
        """Get aggregated embedding from multiple queries."""
        query_embeddings = [await self.aget_query_embedding(query) for query in queries]
        agg_fn = agg_fn or mean_agg
        return agg_fn(query_embeddings)

    @abstractmethod
    def _get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Asynchronously get text embedding.

        By default, this falls back to _get_text_embedding.
        Meant to be overriden if there is a true async implementation.

        """
        return self._get_text_embedding(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embeddings.

        By default, this is a wrapper around _get_text_embedding.
        Meant to be overriden for batch queries.

        """
        result = [self._get_text_embedding(text) for text in texts]
        return result

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Asynchronously get text embeddings.

        By default, this is a wrapper around _aget_text_embedding.
        Meant to be overriden for batch queries.

        """
        result = await asyncio.gather(
            *[self._aget_text_embedding(text) for text in texts]
        )
        return result

    def get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""
        with self.callback_manager.event(
            CBEventType.EMBEDDING, payload={EventPayload.SERIALIZED: self.to_dict()}
        ) as event:
            text_embedding = self._get_text_embedding(text)

            event.on_end(
                payload={
                    EventPayload.CHUNKS: [text],
                    EventPayload.EMBEDDINGS: [text_embedding],
                }
            )

        return text_embedding

    def queue_text_for_embedding(self, text_id: str, text: str) -> None:
        """Queue text for embedding.

        Used for batching texts during embedding calls.

        """
        self._text_queue.append((text_id, text))

    def get_queued_text_embeddings(
        self, show_progress: bool = False
    ) -> Tuple[List[str], List[List[float]]]:
        """Get queued text embeddings.

        Call embedding API to get embeddings for all queued texts.

        """
        text_queue = self._text_queue
        cur_batch: List[Tuple[str, str]] = []
        result_ids: List[str] = []
        result_embeddings: List[List[float]] = []

        queue_with_progress = enumerate(
            get_tqdm_iterable(text_queue, show_progress, "Generating embeddings")
        )

        for idx, (text_id, text) in queue_with_progress:
            cur_batch.append((text_id, text))
            if idx == len(text_queue) - 1 or len(cur_batch) == self.embed_batch_size:
                # flush
                with self.callback_manager.event(
                    CBEventType.EMBEDDING,
                    payload={EventPayload.SERIALIZED: self.to_dict()},
                ) as event:
                    cur_batch_ids = [text_id for text_id, _ in cur_batch]
                    cur_batch_texts = [text for _, text in cur_batch]
                    embeddings = self._get_text_embeddings(cur_batch_texts)
                    result_ids.extend(cur_batch_ids)
                    result_embeddings.extend(embeddings)
                    event.on_end(
                        payload={
                            EventPayload.CHUNKS: cur_batch_texts,
                            EventPayload.EMBEDDINGS: embeddings,
                        },
                    )
                cur_batch = []

        # reset queue
        self._text_queue = []
        return result_ids, result_embeddings

    async def aget_queued_text_embeddings(
        self, text_queue: List[Tuple[str, str]], show_progress: bool = False
    ) -> Tuple[List[str], List[List[float]]]:
        """Asynchronously get a list of text embeddings.

        Call async embedding API to get embeddings for all queued texts in parallel.
        Argument `text_queue` must be passed in to avoid updating it async.

        """
        cur_batch: List[Tuple[str, str]] = []
        callback_payloads: List[Tuple[str, List[str]]] = []
        result_ids: List[str] = []
        result_embeddings: List[List[float]] = []
        embeddings_coroutines: List[Coroutine] = []
        for idx, (text_id, text) in enumerate(text_queue):
            cur_batch.append((text_id, text))
            if idx == len(text_queue) - 1 or len(cur_batch) == self.embed_batch_size:
                # flush
                event_id = self.callback_manager.on_event_start(
                    CBEventType.EMBEDDING,
                    payload={EventPayload.SERIALIZED: self.to_dict()},
                )
                cur_batch_ids = [text_id for text_id, _ in cur_batch]
                cur_batch_texts = [text for _, text in cur_batch]
                callback_payloads.append((event_id, cur_batch_texts))
                embeddings_coroutines.append(
                    self._aget_text_embeddings(cur_batch_texts)
                )
                result_ids.extend(cur_batch_ids)

        # flatten the results of asyncio.gather, which is a list of embeddings lists
        nested_embeddings = []
        if show_progress:
            try:
                from tqdm.auto import tqdm

                nested_embeddings = [
                    await f
                    for f in tqdm(
                        asyncio.as_completed(embeddings_coroutines),
                        total=len(embeddings_coroutines),
                        desc="Generating embeddings",
                    )
                ]
            except ImportError:
                nested_embeddings = await asyncio.gather(*embeddings_coroutines)
                pass
        else:
            nested_embeddings = await asyncio.gather(*embeddings_coroutines)

        result_embeddings = [
            embedding for embeddings in nested_embeddings for embedding in embeddings
        ]

        for (event_id, text_batch), embeddings in zip(
            callback_payloads, nested_embeddings
        ):
            self.callback_manager.on_event_end(
                CBEventType.EMBEDDING,
                payload={
                    EventPayload.CHUNKS: text_batch,
                    EventPayload.EMBEDDINGS: embeddings,
                },
                event_id=event_id,
            )

        return result_ids, result_embeddings

    def similarity(
        self,
        embedding1: EMB_TYPE,
        embedding2: EMB_TYPE,
        mode: SimilarityMode = SimilarityMode.DEFAULT,
    ) -> float:
        """Get embedding similarity."""
        return similarity(embedding1=embedding1, embedding2=embedding2, mode=mode)
