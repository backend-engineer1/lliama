"""List index.

A simple data structure where LlamaIndex iterates through document chunks
in sequence in order to answer a given query.

"""

from enum import Enum
from typing import Any, Optional, Sequence, Union

from llama_index.data_structs.data_structs import IndexList
from llama_index.data_structs.node import Node
from llama_index.indices.base import BaseGPTIndex
from llama_index.indices.base_retriever import BaseRetriever
from llama_index.indices.service_context import ServiceContext


class ListRetrieverMode(str, Enum):
    DEFAULT = "default"
    EMBEDDING = "embedding"


class GPTListIndex(BaseGPTIndex[IndexList]):
    """GPT List Index.

    The list index is a simple data structure where nodes are stored in
    a sequence. During index construction, the document texts are
    chunked up, converted to nodes, and stored in a list.

    During query time, the list index iterates through the nodes
    with some optional filter parameters, and synthesizes an
    answer from all the nodes.

    Args:
        text_qa_template (Optional[QuestionAnswerPrompt]): A Question-Answer Prompt
            (see :ref:`Prompt-Templates`).
            NOTE: this is a deprecated field.

    """

    index_struct_cls = IndexList

    def __init__(
        self,
        nodes: Optional[Sequence[Node]] = None,
        index_struct: Optional[IndexList] = None,
        service_context: Optional[ServiceContext] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        super().__init__(
            nodes=nodes,
            index_struct=index_struct,
            service_context=service_context,
            **kwargs,
        )

    def as_retriever(
        self,
        retriever_mode: Union[str, ListRetrieverMode] = ListRetrieverMode.DEFAULT,
        **kwargs: Any,
    ) -> BaseRetriever:
        from llama_index.indices.list.retrievers import (
            ListIndexEmbeddingRetriever,
            ListIndexRetriever,
        )

        if retriever_mode == ListRetrieverMode.DEFAULT:
            return ListIndexRetriever(self, **kwargs)
        elif retriever_mode == ListRetrieverMode.EMBEDDING:
            return ListIndexEmbeddingRetriever(self, **kwargs)
        else:
            raise ValueError(f"Unknown retriever mode: {retriever_mode}")

    def _build_index_from_nodes(self, nodes: Sequence[Node]) -> IndexList:
        """Build the index from documents.

        Args:
            documents (List[BaseDocument]): A list of documents.

        Returns:
            IndexList: The created list index.
        """
        index_struct = IndexList()
        for n in nodes:
            index_struct.add_node(n)
        return index_struct

    def _insert(self, nodes: Sequence[Node], **insert_kwargs: Any) -> None:
        """Insert a document."""
        for n in nodes:
            # print("inserting node to index struct: ", n.get_doc_id())
            self._index_struct.add_node(n)

    def _delete(self, doc_id: str, **delete_kwargs: Any) -> None:
        """Delete a document."""
        cur_node_ids = self._index_struct.nodes
        cur_nodes = self._docstore.get_nodes(cur_node_ids)
        nodes_to_keep = [n for n in cur_nodes if n.ref_doc_id != doc_id]
        self._index_struct.nodes = [n.get_doc_id() for n in nodes_to_keep]
