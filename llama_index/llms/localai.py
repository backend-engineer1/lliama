from typing import Any, Dict, Optional

from llama_index.bridge.pydantic import Field
from llama_index.constants import DEFAULT_CONTEXT_WINDOW
from llama_index.llms.openai import OpenAI

DEFAULT_KEY = "fake"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8080
DEFAULT_API_BASE = f"{DEFAULT_HOST}{DEFAULT_PORT}"


class LocalAI(OpenAI):
    """
    LocalAI is a free, open source, and self-hosted OpenAI alternative.

    Docs: https://localai.io/
    Source: https://github.com/go-skynet/LocalAI
    """

    @classmethod
    def class_name(cls) -> str:
        return "LocalAI"

    context_window: int = Field(
        default=DEFAULT_CONTEXT_WINDOW,
        description="The maximum number of context tokens for the model.",
    )
    globally_use_chat_completions: Optional[bool] = Field(
        default=None,
        description=(
            "Set None (default) to per-invocation decide on using /chat/completions"
            " vs /completions endpoints with query keyword arguments,"
            " set False to universally use /completions endpoint,"
            " set True to universally use /chat/completions endpoint."
        ),
    )

    def __init__(
        self,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        api_key: Optional[str] = DEFAULT_KEY,
        api_base: Optional[str] = DEFAULT_API_BASE,
        globally_use_chat_completions: Optional[bool] = None,
        **openai_kwargs: Any,
    ) -> None:
        super().__init__(api_key=api_key, api_base=api_base, **openai_kwargs)
        # Below sets the pydantic Fields specific to this class
        self.context_window = context_window
        self.globally_use_chat_completions = globally_use_chat_completions

    def _get_context_window(self) -> int:
        return self.context_window

    def _update_max_tokens(self, all_kwargs: Dict[str, Any], prompt: str) -> None:
        # This subclass only supports max_tokens via LocalAI(..., max_tokens=123)
        if self.max_tokens is not None:
            return
        all_kwargs.pop("max_tokens", None)

    @property
    def _is_chat_model(self) -> bool:
        if self.globally_use_chat_completions is not None:
            return self.globally_use_chat_completions
        raise NotImplementedError(
            f"Inferring of /chat/completions is not supported by {type(self).__name__}."
            f" Please use the kwarg 'use_chat_completions' in your query, setting"
            f" True to use /chat/completions or False to use /completions."
        )
