from llama_index import Document
from llama_index.indices.service_context import ServiceContext
from llama_index.node_parser import SimpleNodeParser
from llama_index.node_parser.extractors import (
    KeywordExtractor,
    MetadataExtractor,
    QuestionsAnsweredExtractor,
    SummaryExtractor,
    TitleExtractor,
)


def test_metadata_extractor(mock_service_context: ServiceContext) -> None:
    metadata_extractor = MetadataExtractor(
        extractors=[
            TitleExtractor(nodes=5),
            QuestionsAnsweredExtractor(questions=3),
            SummaryExtractor(summaries=["prev", "self"]),
            KeywordExtractor(keywords=10),
        ],
    )

    node_parser = SimpleNodeParser.from_defaults(
        metadata_extractor=metadata_extractor,
    )

    document = Document(
        text="sample text",
        metadata={"filename": "README.md", "category": "codebase"},
    )

    nodes = node_parser.get_nodes_from_documents([document])

    assert "document_title" in nodes[0].metadata
    assert "questions_this_excerpt_can_answer" in nodes[0].metadata
    assert "section_summary" in nodes[0].metadata
    assert "excerpt_keywords" in nodes[0].metadata
