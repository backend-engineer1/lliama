(evaluation)=
# Evaluation

## Concept
Evaluation and benchmarking are crucial concepts in LLM development. To improve the performance of an LLM app (RAG, agents), you must have a way to measure it.

LlamaIndex offers key modules to measure the quality of generated results. We also offer key modules to measure retrieval quality.

- **Response Evaluation**: Does the response match the retrieved context? Does it also match the query? Does it match the reference answer or guidelnes?
- **Retrieval Evaluation**: Are the retrieved sources relevant to the query?

This section describes how the evaluation components within LlamaIndex work.

### Response Evaluation

Evaluation of generated results can be difficult, since unlike traditional machine learning the predicted result isn't a single number, and it can be hard to define quantitative metrics for this problem.

LlamaIndex offers **LLM-based** evaluation modules to measure the quality of results. This uses a "gold" LLM (e.g. GPT-4) to decide whether the predicted answer is correct in a variety of ways.

Note that many of these current evaluation modules
do *not* require ground-truth labels. Evaluation can be done with some combination of the query, context, response,
and combine these with LLM calls.

These evaluation modules are in the following forms:
- **Correctness**: Whether the generated answer matches that of the reference answer given the query (requires labels).
- **Semantic Similarity** Whether the predicted answer is semantically similar to the reference answer (requires labels).
- **Faithfulness**: Evaluates if the answer is faithful to the retrieved contexts (in other words, whether if there's hallucination).
- **Context Relevancy**: Whether retrieved context and answer are relevant to the query.
- **Guideline Adherence**: Whether the predicted answer adheres to specific guidelines.

#### Question Generation

In addition to evaluating queries, LlamaIndex can also use your data to generate questions to evaluate on. This means that you can automatically generate questions, and then run an evaluation pipeline to test if the LLM can actually answer questions accurately using your data.

### Retrieval Evaluation

We also provide modules to help evaluate retrieval independently.

The concept of retrieval evaluation is not new; given a dataset of questions and ground-truth rankings, we can evaluate retrievers using ranking metrics like mean-reciprocal rank (MRR), hit-rate, precision, and more.

The core retrieval evaluation steps revolve around the following:
- **Dataset generation**: Given an unstructured text corpus, synthetically generate (question, context) pairs.
- **Retrieval Evaluation**: Given a retriever and a set of questions, evaluate retrieved results using ranking metrics.

## Integrations

We also integrate with community evaluation tools.

- [DeepEval](../../../community/integrations/deepeval.md)
- [Ragas](https://github.com/explodinggradients/ragas/blob/main/docs/howtos/integrations/llamaindex.ipynb)

## Usage Pattern

For full usage details, see the usage pattern below.

```{toctree}
---
maxdepth: 1
---
usage_pattern.md
usage_pattern_retrieval.md
```

## Modules

Notebooks with usage of these components can be found below.

```{toctree}
---
maxdepth: 1
---
modules.md
```
