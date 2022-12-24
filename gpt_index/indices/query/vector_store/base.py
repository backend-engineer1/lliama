"""Base vector store index query."""


from abc import abstractmethod
from typing import Any, Generic, List, Optional, Tuple, TypeVar

from gpt_index.embeddings.openai import OpenAIEmbedding
from gpt_index.indices.data_structs import BaseIndexDict, Node
from gpt_index.indices.query.base import BaseGPTIndexQuery
from gpt_index.indices.response.builder import ResponseBuilder
from gpt_index.indices.utils import truncate_text
from gpt_index.prompts.default_prompts import (
    DEFAULT_REFINE_PROMPT,
    DEFAULT_TEXT_QA_PROMPT,
)
from gpt_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt

BID = TypeVar("BID", bound=BaseIndexDict)


class BaseGPTVectorStoreIndexQuery(BaseGPTIndexQuery[BID], Generic[BID]):
    """Base vector store query."""

    def __init__(
        self,
        index_struct: BID,
        text_qa_template: Optional[QuestionAnswerPrompt] = None,
        refine_template: Optional[RefinePrompt] = None,
        embed_model: Optional[OpenAIEmbedding] = None,
        similarity_top_k: Optional[int] = 1,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        super().__init__(index_struct=index_struct, **kwargs)
        self.text_qa_template = text_qa_template or DEFAULT_TEXT_QA_PROMPT
        self.refine_template = refine_template or DEFAULT_REFINE_PROMPT
        self._embed_model = embed_model or OpenAIEmbedding()
        self.similarity_top_k = similarity_top_k

    def _give_response_for_nodes(
        self, query_str: str, nodes: List[Node], verbose: bool = False
    ) -> str:
        """Give response for nodes."""
        response_builder = ResponseBuilder(
            self._prompt_helper,
            self._llm_predictor,
            self.text_qa_template,
            self.refine_template,
        )
        for node in nodes:
            text = self._get_text_from_node(query_str, node, verbose=verbose)
            response_builder.add_text_chunks([text])
        response = response_builder.get_response(
            query_str, verbose=verbose, mode=self._response_mode
        )

        return response or ""

    @abstractmethod
    def _get_nodes_for_response(
        self, query_str: str, verbose: bool = False
    ) -> Tuple[List[str], List[Node]]:
        """Get nodes for response."""

    def _query(self, query_str: str, verbose: bool = False) -> str:
        """Answer a query."""
        print(f"> Starting query: {query_str}")
        node_idxs, top_k_nodes = self._get_nodes_for_response(
            query_str, verbose=verbose
        )
        # print verbose output
        if verbose:
            fmt_txts = []
            for node_idx, node in zip(node_idxs, top_k_nodes):
                fmt_txt = f"> [Node {node_idx}] {truncate_text(node.get_text(), 100)}"
                fmt_txts.append(fmt_txt)
            top_k_node_text = "\n".join(fmt_txts)
            print(f"> Top {len(top_k_nodes)} nodes:\n{top_k_node_text}")
        return self._give_response_for_nodes(query_str, top_k_nodes, verbose=verbose)
