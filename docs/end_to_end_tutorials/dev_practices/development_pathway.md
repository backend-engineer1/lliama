
# The Development Pathway

In your journey to developing an LLM application, it helps to start with a discovery phase of understanding your data and doing some identification of issues and corner cases as you interact with the system. 

Over time, you would try to formalize processes and evaluation methodology, setting up tools for observability, debugging and experiment tracking, and eventually production monitoring.

Below, we provide some additional guidance on considerations and hurdles you may face when developing your application.

## The Challenges of Building a Production-Ready LLM Application
Many who are interested in the LLM application space are not machine learning engineers but rather software developers or  even non-technical folk. 

One of the biggest strides forward that LLMs and foundation models have made to the AI/ML application landscape is that it makes it really easy to go from idea to prototype without facing all of the hurdles and uncertainty of a traditional machine learning project.

This would have involved collecting, exploring and cleaning data, keeping up with latest research and exploring different methods, training models, adjusting hyperparameters, and dealing with unexpected issues in model quality. 

The huge infrastructure burden, long development cycle, and high risk to reward ratio have been blockers to successful applications.

At the same time, despite the fact that getting a prototype working quickly through frameworks like LlamaIndex has become a lot more accessible, deploying a machine learning product in the real world is still rife with uncertainty and challenges.

### Quality and User Interaction
On the tamer side, one may face quality issues, and in the worse case, one may be liable to losing user trust if the application proves itself to be unreliable. 

We've already seen a bit of this with ChatGPT - despite its life-likeness and seeming ability to understand our conversations and requests, it often makes things up ("hallucinates"). It's not connected to the real world, data, or other digital applications.

It is important to be able to monitor, track and improve against quality issues.

## Tradeoffs in LLM Application Development
There are a few tradeoffs in LLM application development:
1. **Cost** - more powerful models may be more expensive
2. **Latency** - more powerful models may be slower
3. **Simplicity** (one size fits all) - how powerful and flexible is the model / pipeline?
4. **Reliability / Useability** - is my application working at least in the general case? Is it ready for unstructured user interaction? Have I covered the major usage patterns?

LLM infra improvements are progressing quickly and we expect cost and latency to go down over time.
  
Here are some additional concerns:
1. **Evaluation** - Once I start diving deeper into improving quality, how can I evaluate individual components? How can I keep track of issues and track whether / how they are being improved over time as I change my application?
2. **Data-Driven** - How can I automate more of my evaluation and iteration process? How do I start small and add useful data points over time? How can I organize different datasets and metrics which serving different purposes? How can I manage the complexity while keeping track of my guiding light of providing the best user experience? 
3. **Customization / Complexity Tradeoff** - How do I improve each stage of the pipeline - preprocessing and feature extraction, retrieval, generation? Does this involve adding additional structure or processing? How can I break down this goal into more measurable and trackable sub-goals?

Differences between **Evaluation** and being **Data-Driven**:
1. **Evaluation** does not necessarily have to be rigorous or fully data-driven process - especially at the initial stages. It is more concerned with the initial *development* phase of the application - validating that the overall pipeline works in the general case and starting to define possible signals and metrics which may be carried forward into production.
2. Being **Data-Driven** is closely tied to *automation*. After we've chosen our basic application structure, how can we improve the system over time? How can we ensure quality in a systematic way? How can we reduce the cost of monitoring, and what are the pathways to adding and curating data points? How can we leverage ML systems (including but not limited to LLMs) to make this process easier?

Additional considerations:
1. **Privacy** - how can I ensure that my data is not leaked if I am feeding it into these models? What infrastructure am I using and what is the security guarantee / how is the access control structured?

## Development Hurdles

Here are some potential problems you may encounter when developing your LLM application which may lead to unsatisfactory results.

### Retrieval

1. **Out of Domain:**
If your data is extremely specific (medical, legal, scientific, financial, or other documents with technical lingo), it may be worth:
    - trying out alternate embeddings 
      - Check the [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
      - You may configure a local embedding model [with the steps here](local-embedding-models)
    - testing out fine-tuning of embeddings
        - Tools: [setfit](https://github.com/huggingface/setfit)
        - Anecdotally, we have seen retrieval accuracy improve by ~12% by curating a small annotated dataset from production data
        - Even synthetic data generation without human labels has been shown to improve retrieval metrics across similar documents in train / val sets.
        - More detailed guides and case studies will come soon.
    - testing out sparse retrieval methods (see ColBERT, SPLADE)
        - these methods have been shown to generalize well to out of domain data
        - that are starting to be available in some enterprise systems (e.g. [Elastic Search's ELSeR](https://www.elastic.co/guide/en/machine-learning/current/ml-nlp-elser.html))
    - checking out our [evaluation principles guide](Evaluation) on how you might evaluate the above changes 
