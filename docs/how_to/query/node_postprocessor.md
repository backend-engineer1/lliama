# Node Postprocessor

By default, when a query is executed on an index or a composed graph, LlamaIndex performs
the following steps:
1. **Retrieval step**: Retrieve a set of nodes from the index given the query. For instance, with a vector index, 
    this would be top-k relevant nodes; with a list index this would be all nodes.
2. **Synthesis step**: Synthesize a response over the set of nodes.

LlamaIndex provides a set of "postprocessor" modules that can augment the retrieval process in (1).
The process is very simple. After the retrieval step, we can analyze the initial set of nodes and add a "processing" step to 
refine this set of nodes - whether its by filtering out irrelevant nodes, adding more nodes, and more.

This is a simple but powerful step. This allows us to perform tasks like keyword filtering, as well as temporal reasoning
over your data.

We first provide the high-level API interface, and provide some example modules, and finally discuss usage.

We are also very open to contributions! Take a look at our [contribution guide](https://github.com/jerryjliu/llama_index/blob/main/CONTRIBUTING.md) if you 
are interested in contributing a Postprocessor.

## API Interface

The base class is `BaseNodePostprocessor`, and the API interface is very simple: 

```python

class BaseNodePostprocessor(BasePostprocessor, BaseModel):
    """Node postprocessor."""

    @abstractmethod
    def postprocess_nodes(
        self, nodes: List[Node], extra_info: Optional[Dict] = None
    ) -> List[Node]:
        """Postprocess nodes."""
```

It takes in a list of Node objects, and outputs another list of Node objects.

The full API reference can be found [here](/reference/node_postprocessor.rst).


## Example Usage

The postprocessor can be used as part of a `ResponseSynthesizer` in a `QueryEngine`, or on its own.

#### Index querying

```python

from gpt_index.indices.postprocessor import (
    FixedRecencyPostprocessor,
)
node_postprocessor = FixedRecencyPostprocessor(service_context=service_context)

query_engine = index.as_query_engine(
    similarity_top_k=3,
    node_postprocessors=[node_postprocessor]
)
response = query_engine.query(
    "How much did the author raise in seed funding from Idelle's husband (Julian) for Viaweb?", 
)

```


#### Using as Independent Module (Lower-Level Usage)

The module can also be used on its own as part of a broader flow. For instance,
here's an example where you choose to manually postprocess an initial set of source nodes.

```python
from gpt_index.indices.postprocessor import (
    FixedRecencyPostprocessor,
)

# get initial response from vector index
query_engine = index.as_query_engine(
    similarity_top_k=3,
    response_mode="no_text"
)
init_response = query_engine.query(query_str)
resp_nodes = [n.node for n in init_response.source_nodes]

# use node postprocessor to filter nodes
node_postprocessor = FixedRecencyPostprocessor(service_context=service_context)
new_nodes = node_postprocessor.postprocess_nodes(resp_nodes)

# use list index to synthesize answers
list_index = GPTListIndex(new_nodes)
query_engine = list_index.as_query_engine(
    node_postprocessors=[node_postprocessor]
)
response = query_engine.query(query_str)
```


## Example Modules

### Default Postprocessors

These postprocessors are simple modules that are already included by default.

#### KeywordNodePostprocessor

A simple postprocessor module where you are able to specify `required_keywords` or `exclude_keywords`.
This will filter out nodes that don't have required keywords, or contain excluded keywords.

#### SimilarityPostprocessor

A module where you are able to specify a `similarity_cutoff`.

#### Previous/Next Postprocessors

These postprocessors are able to exploit temporal relationships between nodes
(e.g. prev/next relationships) in order to retrieve additional
context, in the event that the existing context may not directly answer
the question. They augment the set of retrieved nodes with context
either in the future or the past (or both).

The most basic version is `PrevNextNodePostprocessor`, which takes a fixed
`num_nodes` as well as `mode` specifying "previous", "next", or "both".

We also have `AutoPrevNextNodePostprocessor`, which is able to infer
the `previous`, `next` direction.

![](/_static/node_postprocessors/prev_next.png)


#### Recency Postprocessors

These postprocessors are able to ensure that only the most recent
data is used as context, and that out of date context information is filtered out.

Imagine that you have three versions of a document, with slight changes between versions. For instance, this document may be describing patient history. If you ask a question over this data, you would want to make sure that you're referencing the latest document, and that out of date information is not passed in.

We support recency filtering through the following modules.

**`FixedRecencyPostProcessor`**: sorts retrieved nodes by date in reverse order, and takes a fixed top-k set of nodes.

![](/_static/node_postprocessors/recency.png)

**`EmbeddingRecencyPostprocessor`**: sorts retrieved nodes by date in reverse order, and then
looks at subsequent nodes and filters out nodes that have high embedding 
similarity with the current node. This allows us to maintain recent Nodes
that have "distinct" context, but filter out overlapping Nodes that
are outdated and overlap with more recent context.


**`TimeWeightedPostprocessor`**: adds time-weighting to retrieved nodes, using the formula `(1-time_decay) ** hours_passed`.
The recency score is added to any score that the node already contains.


