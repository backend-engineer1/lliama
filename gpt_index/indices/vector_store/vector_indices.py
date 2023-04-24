"""Deprecated vector store indices."""

from typing import Any, Callable, Dict, Optional, Sequence, Type

from requests.adapters import Retry

from gpt_index.data_structs.data_structs_v2 import (
    ChatGPTRetrievalPluginIndexDict,
    ChromaIndexDict,
    FaissIndexDict,
    IndexDict,
    MilvusIndexDict,
    MyScaleIndexDict,
    OpensearchIndexDict,
    PineconeIndexDict,
    QdrantIndexDict,
    SimpleIndexDict,
    WeaviateIndexDict,
    DeepLakeIndexDict,
)
from gpt_index.data_structs.node_v2 import Node
from gpt_index.indices.base import BaseGPTIndex
from gpt_index.indices.service_context import ServiceContext
from gpt_index.indices.vector_store.base import GPTVectorStoreIndex
from gpt_index.vector_stores import (
    ChatGPTRetrievalPluginClient,
    ChromaVectorStore,
    DeepLakeVectorStore,
    FaissVectorStore,
    MilvusVectorStore,
    MyScaleVectorStore,
    PineconeVectorStore,
    QdrantVectorStore,
    SimpleVectorStore,
    WeaviateVectorStore,
)
from gpt_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)


class GPTSimpleVectorIndex(GPTVectorStoreIndex):
    """GPT Simple Vector Index.

    The GPTSimpleVectorIndex is a data structure where nodes are keyed by
    embeddings, and those embeddings are stored within a simple dictionary.
    During index construction, the document texts are chunked up,
    converted to nodes with text; they are then encoded in
    document embeddings stored within the dict.

    During query time, the index uses the dict to query for the top
    k most similar nodes, and synthesizes an answer from the
    retrieved nodes.

    Args:
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).

    """

    index_struct_cls: Type[IndexDict] = SimpleIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        index_struct: Optional[IndexDict] = None,
        service_context: Optional[ServiceContext] = None,
        vector_store: Optional[SimpleVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTFaissIndex(GPTVectorStoreIndex):
    """GPT Faiss Index.

    The GPTFaissIndex is a data structure where nodes are keyed by
    embeddings, and those embeddings are stored within a Faiss index.
    During index construction, the document texts are chunked up,
    converted to nodes with text; they are then encoded in
    document embeddings stored within Faiss.

    During query time, the index uses Faiss to query for the top
    k most similar nodes, and synthesizes an answer from the
    retrieved nodes.

    Args:
        faiss_index (faiss.Index): A Faiss Index object (required). Note: the index
            will be reset during index construction.
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
    """

    index_struct_cls: Type[IndexDict] = FaissIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        service_context: Optional[ServiceContext] = None,
        faiss_index: Optional[Any] = None,
        index_struct: Optional[IndexDict] = None,
        vector_store: Optional[FaissVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        if vector_store is None:
            if faiss_index is None:
                raise ValueError("faiss_index is required.")
            vector_store = FaissVectorStore(faiss_index)

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )

    @classmethod
    def load_from_disk(
        cls, save_path: str, faiss_index_save_path: Optional[str] = None, **kwargs: Any
    ) -> "BaseGPTIndex":
        """Load index from disk.

        This method loads the index from a JSON file stored on disk. The index data
        structure itself is preserved completely. If the index is defined over
        subindices, those subindices will also be preserved (and subindices of
        those subindices, etc.).
        In GPTFaissIndex, we allow user to specify an additional
        `faiss_index_save_path` to load faiss index from a file - that
        way, the user does not have to recreate the faiss index outside
        of this class.

        Args:
            save_path (str): The save_path of the file.
            faiss_index_save_path (Optional[str]): The save_path of the
                Faiss index file. If not specified, the Faiss index
                will not be saved to disk.
            **kwargs: Additional kwargs to pass to the index constructor.

        Returns:
            BaseGPTIndex: The loaded index.
        """
        if faiss_index_save_path is not None:
            import faiss

            faiss_index = faiss.read_index(faiss_index_save_path)
            return super().load_from_disk(save_path, faiss_index=faiss_index, **kwargs)
        else:
            return super().load_from_disk(save_path, **kwargs)

    def save_to_disk(
        self,
        save_path: str,
        encoding: str = "ascii",
        faiss_index_save_path: Optional[str] = None,
        **save_kwargs: Any,
    ) -> None:
        """Save to file.

        This method stores the index into a JSON file stored on disk.
        In GPTFaissIndex, we allow user to specify an additional
        `faiss_index_save_path` to save the faiss index to a file - that
        way, the user can pass in the same argument in
        `GPTFaissIndex.load_from_disk` without having to recreate
        the Faiss index outside of this class.

        Args:
            save_path (str): The save_path of the file.
            encoding (str): The encoding to use when saving the file.
            faiss_index_save_path (Optional[str]): The save_path of the
                Faiss index file. If not specified, the Faiss index
                will not be saved to disk.
        """
        super().save_to_disk(save_path, encoding=encoding, **save_kwargs)

        if faiss_index_save_path is not None:
            import faiss

            faiss.write_index(self._vector_store.client, faiss_index_save_path)


class GPTPineconeIndex(GPTVectorStoreIndex):
    """GPT Pinecone Index.

    The GPTPineconeIndex is a data structure where nodes are keyed by
    embeddings, and those embeddings are stored within a Pinecone index.
    During index construction, the document texts are chunked up,
    converted to nodes with text; they are then encoded in
    document embeddings stored within Pinecone.

    During query time, the index uses Pinecone to query for the top
    k most similar nodes, and synthesizes an answer from the
    retrieved nodes.

    Args:
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
    """

    index_struct_cls: Type[IndexDict] = PineconeIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        pinecone_index: Optional[Any] = None,
        index_name: Optional[str] = None,
        environment: Optional[str] = None,
        namespace: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        pinecone_kwargs: Optional[Dict] = None,
        insert_kwargs: Optional[Dict] = None,
        query_kwargs: Optional[Dict] = None,
        delete_kwargs: Optional[Dict] = None,
        index_struct: Optional[IndexDict] = None,
        service_context: Optional[ServiceContext] = None,
        vector_store: Optional[PineconeVectorStore] = None,
        add_sparse_vector: bool = False,
        tokenizer: Optional[Callable] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        pinecone_kwargs = pinecone_kwargs or {}

        if vector_store is None:
            vector_store = PineconeVectorStore(
                pinecone_index=pinecone_index,
                index_name=index_name,
                environment=environment,
                namespace=namespace,
                metadata_filters=metadata_filters,
                pinecone_kwargs=pinecone_kwargs,
                insert_kwargs=insert_kwargs,
                query_kwargs=query_kwargs,
                delete_kwargs=delete_kwargs,
                add_sparse_vector=add_sparse_vector,
                tokenizer=tokenizer,
            )
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTWeaviateIndex(GPTVectorStoreIndex):
    """GPT Weaviate Index.

    The GPTWeaviateIndex is a data structure where nodes are keyed by
    embeddings, and those embeddings are stored within a Weaviate index.
    During index construction, the document texts are chunked up,
    converted to nodes with text; they are then encoded in
    document embeddings stored within Weaviate.

    During query time, the index uses Weaviate to query for the top
    k most similar nodes, and synthesizes an answer from the
    retrieved nodes.

    Args:
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
    """

    index_struct_cls: Type[IndexDict] = WeaviateIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        service_context: Optional[ServiceContext] = None,
        weaviate_client: Optional[Any] = None,
        class_prefix: Optional[str] = None,
        index_struct: Optional[IndexDict] = None,
        vector_store: Optional[WeaviateVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        if vector_store is None:
            if weaviate_client is None:
                raise ValueError("weaviate_client is required.")
            vector_store = WeaviateVectorStore(
                weaviate_client=weaviate_client, class_prefix=class_prefix
            )
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTQdrantIndex(GPTVectorStoreIndex):
    """GPT Qdrant Index.

    The GPTQdrantIndex is a data structure where nodes are keyed by
    embeddings, and those embeddings are stored within a Qdrant collection.
    During index construction, the document texts are chunked up,
    converted to nodes with text; they are then encoded in
    document embeddings stored within Qdrant.

    During query time, the index uses Qdrant to query for the top
    k most similar nodes, and synthesizes an answer from the
    retrieved nodes.

    Args:
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
        client (Optional[Any]): QdrantClient instance from `qdrant-client` package
        collection_name: (Optional[str]): name of the Qdrant collection
    """

    index_struct_cls: Type[IndexDict] = QdrantIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        service_context: Optional[ServiceContext] = None,
        client: Optional[Any] = None,
        collection_name: Optional[str] = None,
        index_struct: Optional[IndexDict] = None,
        vector_store: Optional[QdrantVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        if vector_store is None:
            if client is None:
                raise ValueError("client is required.")
            if collection_name is None:
                raise ValueError("collection_name is required.")
            vector_store = QdrantVectorStore(
                client=client, collection_name=collection_name
            )
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTMilvusIndex(GPTVectorStoreIndex):
    """GPT Milvus Index.

    In this GPT index we store the text, its embedding and
    a few pieces of its metadata in a Milvus collection.
    This implementation allows the use of an already existing
    collection if it is one that was created this vector store.
    It also supports creating a new one if the collection doesnt exist
    or if `overwrite` is set to True.

    Args:
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
        collection_name (str, optional): The name of the collection
            where data will be stored. Defaults to "llamalection".
        index_params (dict, optional): The index parameters for Milvus,
            if none are provided an HNSW index will be used. Defaults to None.
        search_params (dict, optional): The search parameters for a Milvus query.
            If none are provided, default params will be generated. Defaults to None.
        dim (int, optional): The dimension of the embeddings. If it is not provided,
            collection creation will be done on first insert. Defaults to None.
        host (str, optional): The host address of Milvus. Defaults to "localhost".
        port (int, optional): The port of Milvus. Defaults to 19530.
        user (str, optional): The username for RBAC. Defaults to "".
        password (str, optional): The password for RBAC. Defaults to "".
        use_secure (bool, optional): Use https. Defaults to False.
        overwrite (bool, optional): Whether to overwrite existing collection
            with same name. Defaults to False.

    Raises:
        ImportError: Unable to import `pymilvus`.
        MilvusException: Error communicating with Milvus,
            more can be found in logging under Debug.

    Returns:
        MilvusVectorstore: Vectorstore that supports add, delete, and query.
    """

    index_struct_cls: Type[IndexDict] = MilvusIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        collection_name: str = "llamalection",
        index_params: Optional[dict] = None,
        search_params: Optional[dict] = None,
        dim: Optional[int] = None,
        host: str = "localhost",
        port: int = 19530,
        user: str = "",
        password: str = "",
        use_secure: bool = False,
        overwrite: bool = False,
        service_context: Optional[ServiceContext] = None,
        index_struct: Optional[IndexDict] = None,
        vector_store: Optional[MilvusVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""

        if vector_store is None:
            vector_store = MilvusVectorStore(
                collection_name=collection_name,
                index_params=index_params,
                search_params=search_params,
                dim=dim,
                host=host,
                port=port,
                user=user,
                password=password,
                use_secure=use_secure,
                overwrite=overwrite,
            )
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTDeepLakeIndex(GPTVectorStoreIndex):
    """GPT DeepLake Vector Store.

    In this vector store we store the text, its embedding and
    a few pieces of its metadata in a deeplake dataset. This implemnetation
    allows the use of an already existing deeplake dataset if it is one that was created
    this vector store. It also supports creating a new one if the dataset doesnt
    exist or if `overwrite` is set to True.

    Args:
        deeplake_path (str, optional): Path to the deeplake dataset, where data will be
        stored. Defaults to "llama_index".
        overwrite (bool, optional): Whether to overwrite existing dataset with same
            name. Defaults to False.
        token (str, optional): the deeplake token that allows you to access the dataset
            with proper access. Defaults to None.
        read_only (bool, optional): Whether to open the dataset with read only mode.
        ingestion_batch_size (bool): used for controlling batched data injestion to
            deeplake dataset. Defaults to 1024.
        ingestion_num_workers (int): number of workers to use during data injestion.
            Defaults to 4.
        overwrite (bool, optional): Whether to overwrite existing dataset with the
            new dataset with the same name.

    Raises:
        ImportError: Unable to import `deeplake`.
        UserNotLoggedinException: When user is not logged in with credentials
            or token.
        TokenPermissionError: When dataset does not exist or user doesn't have
            enough permissions to modify the dataset.
        InvalidTokenException: If the specified token is invalid


    Returns:
        DeepLakeVectorstore: Vectorstore that supports add, delete, and query.
    """

    index_struct_cls: Type[IndexDict] = DeepLakeIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        index_struct: Optional[IndexDict] = None,
        service_context: Optional[ServiceContext] = None,
        vector_store: Optional[DeepLakeVectorStore] = None,
        dataset_path: str = "llama_index",
        overwrite: bool = False,
        read_only: bool = False,
        ingestion_batch_size: int = 1024,
        ingestion_num_workers: int = 4,
        token: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        vector_store = DeepLakeVectorStore(
            dataset_path=dataset_path,
            overwrite=overwrite,
            read_only=read_only,
            ingestion_batch_size=ingestion_batch_size,
            ingestion_num_workers=ingestion_num_workers,
            token=token,
        )
        super(GPTDeepLakeIndex, self).__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTMyScaleIndex(GPTVectorStoreIndex):
    """GPT MyScale Index.

    In this GPT index we store the text, its embedding and
    a few pieces of its metadata in a MyScale table. There will be
    a vector index build for the embedding column.
    This implementation allows the use of an already existing
    table if it is one that was created this vector store.
    It also supports creating a new table if the table doesn't exist

    Args:
        myscale_client (httpclient): clickhouse-connect httpclient of
            an existing MyScale cluster.
        table_name (str, optional): The name of the MyScale table
            where data will be stored. Defaults to "llama_index".
        database_name (str, optional): The name of the MyScale database
            where data will be stored. Defaults to "default".
        index_type (str, optional): The type of the MyScale vector index.
            Defaults to "IVFFLAT".
        metric (str, optional): The metric type of the MyScale vector index.
            Defaults to "cosine".
        batch_size (int, optional): the size of documents to insert.
            Defaults to 32.
        index_params (dict, optional): The index parameters for MyScale.
            Defaults to None.
        search_params (dict, optional): The search parameters for a MyScale query.
            Defaults to None.

    Returns:
        MyScaleVectorStore: Vectorstore that supports add, delete, and query.
    """

    index_struct_cls: Type[IndexDict] = MyScaleIndexDict

    def __init__(
        self,
        myscale_client: Optional[Any] = None,
        table_name: str = "llama_index",
        database_name: str = "default",
        index_type: str = "IVFFLAT",
        metric: str = "cosine",
        batch_size: int = 32,
        index_params: Optional[dict] = None,
        search_params: Optional[dict] = None,
        nodes: Optional[Sequence[Node]] = None,
        service_context: Optional[ServiceContext] = None,
        index_struct: Optional[IndexDict] = None,
        vector_store: Optional[MyScaleVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""

        if vector_store is None:
            vector_store = MyScaleVectorStore(
                myscale_client=myscale_client,
                table=table_name,
                database=database_name,
                index_type=index_type,
                metric=metric,
                batch_size=batch_size,
                index_params=index_params,
                search_params=search_params,
                service_context=service_context,
            )
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTChromaIndex(GPTVectorStoreIndex):
    """GPT Chroma Index.

    The GPTChromaIndex is a data structure where nodes are keyed by
    embeddings, and those embeddings are stored within a Chroma collection.
    During index construction, the document texts are chunked up,
    converted to nodes with text; they are then encoded in
    document embeddings stored within Chroma.

    During query time, the index uses Chroma to query for the top
    k most similar nodes, and synthesizes an answer from the
    retrieved nodes.

    Args:
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
        chroma_collection (Optional[Any]): Collection instance from `chromadb` package.

    """

    index_struct_cls: Type[IndexDict] = ChromaIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        index_struct: Optional[IndexDict] = None,
        service_context: Optional[ServiceContext] = None,
        chroma_collection: Optional[Any] = None,
        vector_store: Optional[ChromaVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        if vector_store is None:
            if chroma_collection is None:
                raise ValueError("chroma_collection is required.")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class GPTOpensearchIndex(GPTVectorStoreIndex):
    """GPT Opensearch Index.

    The GPTOpensearchIndex is a data structure where nodes are keyed by
    embeddings, and those embeddings are stored in a document that is indexed
    with its embedding as well as its textual data (text field is defined in
    the OpensearchVectorClient).
    During index construction, the document texts are chunked up,
    converted to nodes with text; each node's embedding is computed, and then
    the node's text, along with the embedding, is converted into JSON document that
    is indexed in Opensearch. The embedding data is put into a field with type
    "knn_vector" and the text is put into a standard Opensearch text field.

    During query time, the index performs approximate KNN search using the
    "knn_vector" field that the embeddings were mapped to.

    Args:
        client (Optional[OpensearchVectorClient]): The client which encapsulates
            logic for using Opensearch as a vector store (that is, it holds stuff
            like endpoint, index_name and performs operations like initializing the
            index and adding new doc/embeddings to said index).
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
    """

    index_struct_cls: Type[IndexDict] = OpensearchIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        service_context: Optional[ServiceContext] = None,
        client: Optional[OpensearchVectorClient] = None,
        index_struct: Optional[IndexDict] = None,
        vector_store: Optional[OpensearchVectorStore] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        if vector_store is None:
            if client is None:
                raise ValueError("client is required.")
            vector_store = OpensearchVectorStore(client)
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )


class ChatGPTRetrievalPluginIndex(GPTVectorStoreIndex):
    """ChatGPTRetrievalPlugin index.

    This index directly interfaces with any server that hosts
    the ChatGPT Retrieval Plugin interface:
    https://github.com/openai/chatgpt-retrieval-plugin.

    Args:
        client (Optional[OpensearchVectorClient]): The client which encapsulates
            logic for using Opensearch as a vector store (that is, it holds stuff
            like endpoint, index_name and performs operations like initializing the
            index and adding new doc/embeddings to said index).
        service_context (ServiceContext): Service context container (contains
            components like LLMPredictor, PromptHelper, etc.).
    """

    index_struct_cls: Type[IndexDict] = ChatGPTRetrievalPluginIndexDict

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        index_struct: Optional[ChatGPTRetrievalPluginIndexDict] = None,
        service_context: Optional[ServiceContext] = None,
        endpoint_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        retries: Optional[Retry] = None,
        batch_size: int = 100,
        vector_store: Optional[ChatGPTRetrievalPluginClient] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""

        if vector_store is None:
            if endpoint_url is None:
                raise ValueError("endpoint_url is required.")
            if bearer_token is None:
                raise ValueError("bearer_token is required.")
            vector_store = ChatGPTRetrievalPluginClient(
                endpoint_url,
                bearer_token,
                retries=retries,
                batch_size=batch_size,
            )
        assert vector_store is not None

        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            vector_store=vector_store,
            **kwargs,
        )
