"""Default query for GPTSimpleVectorIndex."""
from typing import List, Tuple

from gpt_index.indices.data_structs import Node, SimpleIndexDict
from gpt_index.indices.query.embedding_utils import get_top_k_embeddings
from gpt_index.indices.query.vector_store.base import BaseGPTVectorStoreIndexQuery
from gpt_index.indices.utils import truncate_text


class GPTSimpleVectorIndexQuery(BaseGPTVectorStoreIndexQuery[SimpleIndexDict]):
    """GPTSimpleVectorIndex query.

    An embedding-based query for GPTSimpleVectorIndex, which queries
    an underlying dict-based embedding store to retrieve top-k nodes by
    embedding similarity to the query.

    .. code-block:: python

        response = index.query("<query_str>", mode="default")

    Args:
        text_qa_template (Optional[QuestionAnswerPrompt]): Question-Answer Prompt
            (see :ref:`Prompt-Templates`).
        refine_template (Optional[RefinePrompt]): Refinement Prompt
            (see :ref:`Prompt-Templates`).
        embed_model (Optional[OpenAIEmbedding]): Embedding model to use for
            embedding similarity.
        similarity_top_k (int): Number of similar nodes to retrieve.

    """

    def _get_nodes_for_response(
        self, query_str: str, verbose: bool = False
    ) -> Tuple[List[str], List[Node]]:
        """Get nodes for response."""
        # TODO: consolidate with get_query_text_embedding_similarities
        query_embedding = self._embed_model.get_query_embedding(query_str)
        items = self._index_struct.embedding_dict.items()
        node_ids = [t[0] for t in items]
        embeddings = [t[1] for t in items]

        _, top_ids = get_top_k_embeddings(
            self._embed_model,
            query_embedding,
            embeddings,
            similarity_top_k=self.similarity_top_k,
            embedding_ids=node_ids,
        )
        top_k_nodes = self._index_struct.get_nodes(top_ids)

        # print verbose output
        if verbose:
            fmt_txts = []
            for node_idx, node in zip(top_ids, top_k_nodes):
                fmt_txt = f"> [Node {node_idx}] {truncate_text(node.get_text(), 100)}"
                fmt_txts.append(fmt_txt)
            top_k_node_text = "\n".join(fmt_txts)
            print(f"> Top {len(top_k_nodes)} nodes:\n{top_k_node_text}")
        return top_ids, top_k_nodes
