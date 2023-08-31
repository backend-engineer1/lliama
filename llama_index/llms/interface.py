"""Node parser interface."""
from typing import List, Sequence, Dict
from pydantic import BaseModel
from abc import ABC, abstractmethod

from llama_index.schema import BaseNode, Document


class NodeParser(BaseModel, ABC):
    """Base interface for node parser."""

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False,
    ) -> List[BaseNode]:
        """Parse documents into nodes.

        Args:
            documents (Sequence[Document]): documents to parse

        """


class BaseExtractor(BaseModel, ABC):
    """Base interface for feature extractor."""

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def extract(
        self,
        nodes: List[BaseNode],
    ) -> List[Dict]:
        """Post process nodes parsed from documents.

        Args:
            nodes (List[BaseNode]): nodes to extract from
        """
