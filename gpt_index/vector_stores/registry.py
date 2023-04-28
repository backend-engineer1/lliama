from enum import Enum
from typing import Dict, Type

from gpt_index.vector_stores.chatgpt_plugin import ChatGPTRetrievalPluginClient
from gpt_index.vector_stores.chroma import ChromaVectorStore
from gpt_index.vector_stores.deeplake import DeepLakeVectorStore
from gpt_index.vector_stores.faiss import FaissVectorStore
from gpt_index.vector_stores.milvus import MilvusVectorStore
from gpt_index.vector_stores.myscale import MyScaleVectorStore
from gpt_index.vector_stores.opensearch import OpensearchVectorStore
from gpt_index.vector_stores.pinecone import PineconeVectorStore
from gpt_index.vector_stores.qdrant import QdrantVectorStore
from gpt_index.vector_stores.simple import SimpleVectorStore
from gpt_index.vector_stores.types import VectorStore
from gpt_index.vector_stores.weaviate import WeaviateVectorStore


class VectorStoreType(str, Enum):
    SIMPLE = "simple"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    PINECONE = "pinecone"
    OPENSEARCH = "opensearch"
    FAISS = "faiss"
    CHROMA = "chroma"
    CHATGPT_PLUGIN = "chatgpt_plugin"
    MILVUS = "milvus"
    DEEPLAKE = "deeplake"
    MYSCALE = "myscale"


VECTOR_STORE_TYPE_TO_VECTOR_STORE_CLASS: Dict[VectorStoreType, Type[VectorStore]] = {
    VectorStoreType.SIMPLE: SimpleVectorStore,
    VectorStoreType.WEAVIATE: WeaviateVectorStore,
    VectorStoreType.QDRANT: QdrantVectorStore,
    VectorStoreType.MILVUS: MilvusVectorStore,
    VectorStoreType.PINECONE: PineconeVectorStore,
    VectorStoreType.OPENSEARCH: OpensearchVectorStore,
    VectorStoreType.FAISS: FaissVectorStore,
    VectorStoreType.CHROMA: ChromaVectorStore,
    VectorStoreType.CHATGPT_PLUGIN: ChatGPTRetrievalPluginClient,
    VectorStoreType.DEEPLAKE: DeepLakeVectorStore,
    VectorStoreType.MYSCALE: MyScaleVectorStore,
}

VECTOR_STORE_CLASS_TO_VECTOR_STORE_TYPE: Dict[Type[VectorStore], VectorStoreType] = {
    cls_: type_ for type_, cls_ in VECTOR_STORE_TYPE_TO_VECTOR_STORE_CLASS.items()
}
