"""Weaviate Vector store index.

An index that that is built on top of an existing vector store.

"""

from typing import Any, Optional, Sequence, cast

from gpt_index.data_structs import Node, WeaviateIndexStruct
from gpt_index.embeddings.base import BaseEmbedding
from gpt_index.embeddings.openai import OpenAIEmbedding
from gpt_index.indices.base import DOCUMENTS_INPUT, BaseGPTIndex
from gpt_index.indices.query.schema import QueryMode
from gpt_index.indices.utils import truncate_text
from gpt_index.langchain_helpers.chain_wrapper import LLMPredictor
from gpt_index.langchain_helpers.text_splitter import TokenTextSplitter
from gpt_index.prompts.default_prompts import DEFAULT_TEXT_QA_PROMPT
from gpt_index.prompts.prompts import QuestionAnswerPrompt
from gpt_index.readers.weaviate.data_structs import WeaviateNode
from gpt_index.readers.weaviate.utils import get_default_class_prefix
from gpt_index.schema import BaseDocument


class GPTWeaviateIndex(BaseGPTIndex[WeaviateIndexStruct]):
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
        text_qa_template (Optional[QuestionAnswerPrompt]): A Question-Answer Prompt
            (see :ref:`Prompt-Templates`).
        embed_model (Optional[BaseEmbedding]): Embedding model to use for
            embedding similarity.
    """

    index_struct_cls = WeaviateIndexStruct

    def __init__(
        self,
        documents: Optional[Sequence[DOCUMENTS_INPUT]] = None,
        index_struct: Optional[WeaviateIndexStruct] = None,
        text_qa_template: Optional[QuestionAnswerPrompt] = None,
        llm_predictor: Optional[LLMPredictor] = None,
        embed_model: Optional[BaseEmbedding] = None,
        weaviate_client: Optional[Any] = None,
        class_prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        import_err_msg = (
            "`weaviate` package not found, please run `pip install weaviate-client`"
        )
        try:
            import weaviate  # noqa: F401
            from weaviate import Client  # noqa: F401
        except ImportError:
            raise ValueError(import_err_msg)

        self.client = cast(Client, weaviate_client)
        if index_struct is not None:
            if class_prefix is not None:
                raise ValueError(
                    "class_prefix must be None when index_struct is not None."
                )
            self.class_prefix = index_struct.get_class_prefix()
        else:
            self.class_prefix = class_prefix or get_default_class_prefix()
        # try to create schema
        WeaviateNode.create_schema(self.client, self.class_prefix)

        self.text_qa_template = text_qa_template or DEFAULT_TEXT_QA_PROMPT
        self._embed_model = embed_model or OpenAIEmbedding()
        super().__init__(
            documents=documents,
            index_struct=index_struct,
            llm_predictor=llm_predictor,
            **kwargs,
        )
        # NOTE: when building the vector store index, text_qa_template is not partially
        # formatted because we don't know the query ahead of time.
        self._text_splitter = self._prompt_helper.get_text_splitter_given_prompt(
            self.text_qa_template, 1
        )

    def _add_document_to_index(
        self,
        index_struct: WeaviateIndexStruct,
        document: BaseDocument,
        text_splitter: TokenTextSplitter,
    ) -> None:
        """Add document to index."""
        text_chunks = text_splitter.split_text(document.get_text())
        for _, text_chunk in enumerate(text_chunks):
            fmt_text_chunk = truncate_text(text_chunk, 50)
            print(f"> Adding chunk: {fmt_text_chunk}")
            # add to Weaviate
            text_embedding = self._embed_model.get_text_embedding(text_chunk)

            node = Node(text=text_chunk, embedding=text_embedding)
            # serialize to gpt index
            WeaviateNode.from_gpt_index(
                self.client, node, index_struct.get_class_prefix()
            )

    def _build_index_from_documents(
        self, documents: Sequence[BaseDocument], verbose: bool = False
    ) -> WeaviateIndexStruct:
        """Build index from documents."""
        text_splitter = self._prompt_helper.get_text_splitter_given_prompt(
            self.text_qa_template, 1
        )
        index_struct = self.index_struct_cls(class_prefix=self.class_prefix)
        for d in documents:
            self._add_document_to_index(index_struct, d, text_splitter)
        return index_struct

    def _insert(self, document: BaseDocument, **insert_kwargs: Any) -> None:
        """Insert a document."""
        self._add_document_to_index(self._index_struct, document, self._text_splitter)

    def delete(self, document: BaseDocument) -> None:
        """Delete a document."""
        raise NotImplementedError("Delete not implemented for Weaviate index.")

    def _preprocess_query(self, mode: QueryMode, query_kwargs: Any) -> None:
        """Query mode to class."""
        super()._preprocess_query(mode, query_kwargs)
        # pass along weaviate client and info
        query_kwargs["weaviate_client"] = self.client
