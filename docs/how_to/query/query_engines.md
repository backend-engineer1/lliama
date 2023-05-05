# Query Engines

Query engine is a generic interface that takes in a query and returns a response.
Query engines can be implemented by composing retrievers, response synthesizer modules.
They can also be built on top of other query engines.  



```{toctree}
---
caption: Examples
maxdepth: 1
---
../../examples/query_engine/CustomRetrievers.ipynb
../../examples/query_engine/RouterQueryEngine.ipynb
../../examples/query_engine/RetrieverRouterQueryEngine.ipynb
../../examples/query_engine/JointQASummary.ipynb
```