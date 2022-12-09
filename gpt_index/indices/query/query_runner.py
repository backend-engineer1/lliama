"""Query runner."""

from typing import Dict, List, Optional

from gpt_index.indices.data_structs import IndexStruct, IndexStructType
from gpt_index.indices.query.base import BaseQueryRunner
from gpt_index.indices.query.query_map import get_query_cls
from gpt_index.indices.query.schema import QueryConfig, QueryMode
from gpt_index.langchain_helpers.chain_wrapper import LLMPredictor
from gpt_index.schema import DocumentStore

DEFAULT_QUERY_CONFIGS = [
    QueryConfig(
        index_struct_type=IndexStructType.TREE,
        query_mode=QueryMode.DEFAULT,
    ),
    QueryConfig(
        index_struct_type=IndexStructType.LIST,
        query_mode=QueryMode.DEFAULT,
    ),
    QueryConfig(
        index_struct_type=IndexStructType.KEYWORD_TABLE,
        query_mode=QueryMode.DEFAULT,
    ),
]


class QueryRunner(BaseQueryRunner):
    """Tool to take in a query request and perform a query with the right classes.

    Higher-level wrapper over a given query.

    """

    def __init__(
        self,
        llm_predictor: LLMPredictor,
        docstore: DocumentStore,
        query_configs: Optional[List[Dict]] = None,
        verbose: bool = False,
    ) -> None:
        """Init params."""
        config_dict: Dict[IndexStructType, QueryConfig] = {}
        if query_configs is None:
            query_config_objs = DEFAULT_QUERY_CONFIGS
        else:
            query_config_objs = [QueryConfig.from_dict(qc) for qc in query_configs]

        for qc in query_config_objs:
            config_dict[qc.index_struct_type] = qc
        self._config_dict = config_dict
        self._llm_predictor = llm_predictor
        self._docstore = docstore
        self._verbose = verbose

    def query(self, query_str: str, index_struct: IndexStruct) -> str:
        """Run query."""
        index_struct_type = IndexStructType.from_index_struct(index_struct)
        if index_struct_type not in self._config_dict:
            raise ValueError(f"IndexStructType {index_struct_type} not in config_dict")
        config = self._config_dict[index_struct_type]
        mode = config.query_mode
        query_cls = get_query_cls(index_struct_type, mode)
        query_obj = query_cls(
            index_struct,
            **config.query_kwargs,
            query_runner=self,
            docstore=self._docstore,
        )

        # set llm_predictor if exists
        query_obj.set_llm_predictor(self._llm_predictor)

        return query_obj.query(query_str, verbose=self._verbose)
