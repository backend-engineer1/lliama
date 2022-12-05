"""Base data structure classes."""
import json
from abc import abstractmethod
from typing import Any, Generic, List, Optional, Sequence, TypeVar, cast

from gpt_index.indices.data_structs import IndexStruct
from gpt_index.langchain_helpers.chain_wrapper import LLMPredictor
from gpt_index.schema import BaseDocument

IS = TypeVar("IS", bound=IndexStruct)

DEFAULT_MODE = "default"
EMBEDDING_MODE = "embedding"


class BaseGPTIndexQuery(Generic[IS]):
    """Base GPT Index Query.

    Helper class that is used to query an index. Can be called within `query`
    method of a BaseGPTIndex object, or instantiated independently.

    """

    def __init__(
        self, index_struct: IS, llm_predictor: Optional[LLMPredictor] = None
    ) -> None:
        """Initialize with parameters."""
        if index_struct is None:
            raise ValueError("index_struct must be provided.")
        self._validate_index_struct(index_struct)
        self._index_struct = index_struct
        self._llm_predictor = llm_predictor or LLMPredictor()

    @property
    def index_struct(self) -> IS:
        """Get the index struct."""
        return self._index_struct

    def _validate_index_struct(self, index_struct: IS) -> None:
        """Validate the index struct."""
        pass

    @abstractmethod
    def query(self, query_str: str, verbose: bool = False) -> str:
        """Answer a query."""

    def set_llm_predictor(self, llm_predictor: LLMPredictor) -> None:
        """Set LLM predictor."""
        self._llm_predictor = llm_predictor


class BaseGPTIndex(Generic[IS]):
    """Base GPT Index."""

    def __init__(
        self,
        documents: Optional[Sequence[BaseDocument]] = None,
        index_struct: Optional[IS] = None,
        llm_predictor: Optional[LLMPredictor] = None,
    ) -> None:
        """Initialize with parameters."""
        if index_struct is None and documents is None:
            raise ValueError("One of documents or index_struct must be provided.")
        if index_struct is not None and documents is not None:
            raise ValueError("Only one of documents or index_struct can be provided.")

        self._llm_predictor = llm_predictor or LLMPredictor()

        # build index struct in the init function
        if index_struct is not None:
            self._index_struct = index_struct
        else:
            documents = cast(List[BaseDocument], documents)
            self._index_struct = self.build_index_from_documents(documents)

    @property
    def index_struct(self) -> IS:
        """Get the index struct."""
        return self._index_struct

    @abstractmethod
    def build_index_from_documents(self, documents: Sequence[BaseDocument]) -> IS:
        """Build the index from documents."""

    @abstractmethod
    def insert(self, document: BaseDocument, **insert_kwargs: Any) -> None:
        """Insert a document."""

    @abstractmethod
    def delete(self, document: BaseDocument) -> None:
        """Delete a document."""

    @abstractmethod
    def _mode_to_query(self, mode: str, **query_kwargs: Any) -> BaseGPTIndexQuery:
        """Query mode to class."""

    def query(
        self,
        query_str: str,
        verbose: bool = False,
        mode: str = DEFAULT_MODE,
        **query_kwargs: Any
    ) -> str:
        """Answer a query."""
        query_obj = self._mode_to_query(mode, **query_kwargs)
        # set llm_predictor if exists
        query_obj.set_llm_predictor(self._llm_predictor)
        return query_obj.query(query_str, verbose=verbose)

    @classmethod
    @abstractmethod
    def load_from_disk(cls, save_path: str, **kwargs: Any) -> "BaseGPTIndex":
        """Load from disk."""

    def save_to_disk(self, save_path: str) -> None:
        """Safe to file."""
        with open(save_path, "w") as f:
            json.dump(self.index_struct.to_dict(), f)
