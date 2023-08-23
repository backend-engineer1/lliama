from typing import Dict, List, Type

from llama_index.agent import OpenAIAgent, ReActAgent
from llama_index.agent.types import BaseAgent
from llama_index.llms import Anthropic, OpenAI
from llama_index.llms.base import LLM
from llama_index.llms.llama_utils import messages_to_prompt
from llama_index.llms.replicate import Replicate

OPENAI_MODELS = [
    "text-davinci-003",
    "gpt-3.5-turbo-0613",
    "gpt-4-0613",
]
ANTHROPIC_MODELS = ["claude-instant-1", "claude-instant-1.2", "claude-2", "claude-2.0"]
LLAMA_MODELS = [
    "llama13b-v2-chat",
    "llama70b-v2-chat",
]
REPLICATE_MODELS: List[str] = []
ALL_MODELS = OPENAI_MODELS + ANTHROPIC_MODELS + LLAMA_MODELS

AGENTS: Dict[str, Type[BaseAgent]] = {
    "react": ReActAgent,
    "openai": OpenAIAgent,
}

LLAMA_13B_V2_CHAT = (
    "a16z-infra/llama13b-v2-chat:"
    "df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5"
)
LLAMA_70B_V2_CHAT = (
    "replicate/llama70b-v2-chat:"
    "e951f18578850b652510200860fc4ea62b3b16fac280f83ff32282f87bbd2e48"
)


def get_model(model: str) -> LLM:
    llm: LLM
    if model in OPENAI_MODELS:
        llm = OpenAI(model=model)
    elif model in ANTHROPIC_MODELS:
        llm = Anthropic(model=model)
    elif model in LLAMA_MODELS:
        model_dict = {
            "llama13b-v2-chat": LLAMA_13B_V2_CHAT,
            "llama70b-v2-chat": LLAMA_70B_V2_CHAT,
        }
        replicate_model = model_dict[model]
        llm = Replicate(
            model=replicate_model,
            temperature=0.01,
            context_window=4096,
            # override message representation for llama 2
            messages_to_prompt=messages_to_prompt,
        )
    else:
        raise ValueError(f"Unknown model {model}")
    return llm


def is_valid_combination(agent: str, model: str) -> bool:
    if agent == "openai" and model not in ["gpt-3.5-turbo-0613", "gpt-4-0613"]:
        print(f"{agent} does not work with {model}")
        return False
    return True
