"""Keyword-table based index.

Similar to a "hash table" in concept. GPT Index first tries
to extract keywords from the source text, and stores the
keywords as keys per item. It similarly extracts keywords
from the query text. Then, it tries to match those keywords to
existing keywords in the table.

"""

import json
from abc import abstractmethod
from typing import Any, List, Optional, Set

from gpt_index.constants import MAX_CHUNK_OVERLAP, MAX_CHUNK_SIZE, NUM_OUTPUTS
from gpt_index.indices.base import DEFAULT_MODE, BaseGPTIndex, BaseGPTIndexQuery
from gpt_index.indices.data_structs import KeywordTable
from gpt_index.indices.keyword_table.query import (
    BaseGPTKeywordTableQuery,
    GPTKeywordTableGPTQuery,
    GPTKeywordTableRAKEQuery,
    GPTKeywordTableSimpleQuery,
)
from gpt_index.indices.keyword_table.utils import extract_keywords_given_response
from gpt_index.indices.utils import get_chunk_size_given_prompt, truncate_text
from gpt_index.langchain_helpers.text_splitter import TokenTextSplitter
from gpt_index.prompts.base import Prompt
from gpt_index.prompts.default_prompts import (
    DEFAULT_KEYWORD_EXTRACT_TEMPLATE,
    DEFAULT_QUERY_KEYWORD_EXTRACT_TEMPLATE,
)
from gpt_index.schema import Document

DQKET = DEFAULT_QUERY_KEYWORD_EXTRACT_TEMPLATE


class BaseGPTKeywordTableIndex(BaseGPTIndex[KeywordTable]):
    """Base GPT Index."""

    def __init__(
        self,
        documents: Optional[List[Document]] = None,
        index_struct: Optional[KeywordTable] = None,
        keyword_extract_template: Prompt = DEFAULT_KEYWORD_EXTRACT_TEMPLATE,
        max_keywords_per_query: int = 10,
        max_keywords_per_chunk: int = 10,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        # need to set parameters before building index in base class.
        self.keyword_extract_template = keyword_extract_template
        self.max_keywords_per_query = max_keywords_per_query
        self.max_keywords_per_chunk = max_keywords_per_chunk
        empty_keyword_extract_template = self.keyword_extract_template.format(
            max_keywords=self.max_keywords_per_chunk, text=""
        )
        chunk_size = get_chunk_size_given_prompt(
            empty_keyword_extract_template, MAX_CHUNK_SIZE, 1, NUM_OUTPUTS
        )
        self.text_splitter = TokenTextSplitter(
            separator=" ",
            chunk_size=chunk_size,
            chunk_overlap=MAX_CHUNK_OVERLAP,
        )
        super().__init__(documents=documents, index_struct=index_struct, **kwargs)

    def _mode_to_query(self, mode: str, **query_kwargs: Any) -> BaseGPTIndexQuery:
        """Query mode to class."""
        if mode == DEFAULT_MODE:
            query_kwargs.update(
                {
                    "max_keywords_per_query": self.max_keywords_per_query,
                    "keyword_extract_template": self.keyword_extract_template,
                }
            )
            query: BaseGPTKeywordTableQuery = GPTKeywordTableGPTQuery(
                self.index_struct, **query_kwargs
            )
        elif mode == "simple":
            query = GPTKeywordTableSimpleQuery(self.index_struct, **query_kwargs)
        elif mode == "rake":
            query = GPTKeywordTableRAKEQuery(self.index_struct, **query_kwargs)
        else:
            raise ValueError(f"Invalid query mode: {mode}.")
        return query

    @abstractmethod
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text."""

    def build_index_from_documents(self, documents: List[Document]) -> KeywordTable:
        """Build the index from documents."""
        # do simple concatenation
        text_data = "\n".join([d.text for d in documents])

        index_struct = KeywordTable(table={})

        text_chunks = self.text_splitter.split_text(text_data)
        for i, text_chunk in enumerate(text_chunks):
            keywords = self._extract_keywords(text_chunk)
            fmt_text_chunk = truncate_text(text_chunk, 50)
            text_chunk_id = index_struct.add_text(list(keywords), text_chunk)
            print(
                f"> Processing chunk {i} of {len(text_chunks)}, id {text_chunk_id}: "
                f"{fmt_text_chunk}"
            )
            print(f"> Keywords: {keywords}")
        return index_struct

    def insert(self, document: Document, **insert_kwargs: Any) -> None:
        """Insert a document."""
        text_chunks = self.text_splitter.split_text(document.text)
        for i, text_chunk in enumerate(text_chunks):
            keywords = self._extract_keywords(text_chunk)
            fmt_text_chunk = truncate_text(text_chunk, 50)
            text_chunk_id = self._index_struct.add_text(list(keywords), text_chunk)
            print(
                f"> Processing chunk {i} of {len(text_chunks)}, id {text_chunk_id}: "
                f"{fmt_text_chunk}"
            )
            print(f"> Keywords: {keywords}")

    def delete(self, document: Document) -> None:
        """Delete a document."""
        raise NotImplementedError("Delete not implemented for keyword table index.")

    @classmethod
    def load_from_disk(
        cls, save_path: str, **kwargs: Any
    ) -> "BaseGPTKeywordTableIndex":
        """Load from disk."""
        with open(save_path, "r") as f:
            return cls(index_struct=KeywordTable.from_dict(json.load(f)), **kwargs)


class GPTKeywordTableIndex(BaseGPTKeywordTableIndex):
    """GPT Keyword Table Index.

    Uses GPT to build keyword table.

    """

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text."""
        response, _ = self._llm_predictor.predict(
            self.keyword_extract_template,
            max_keywords=self.max_keywords_per_chunk,
            text=text,
        )
        keywords = extract_keywords_given_response(response)
        return keywords
