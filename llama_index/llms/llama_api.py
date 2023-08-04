from typing import Any, Dict, Optional, Sequence

from llama_index.callbacks import CallbackManager
from llama_index.constants import DEFAULT_NUM_OUTPUTS
from llama_index.llms.base import (
    ChatMessage,
    ChatResponse,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
    llm_chat_callback,
    llm_completion_callback,
)
from llama_index.llms.custom import CustomLLM
from llama_index.llms.generic_utils import chat_to_completion_decorator
from llama_index.llms.openai_utils import (
    from_openai_message_dict,
    to_openai_message_dicts,
)


class LlamaAPI(CustomLLM):
    def __init__(
        self,
        model: str = "llama-13b-chat",
        temperature: float = 0.0,
        max_tokens: int = DEFAULT_NUM_OUTPUTS,
        additional_kwargs: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        try:
            from llamaapi import LlamaAPI as Client
        except ImportError as e:
            raise ImportError(
                "llama_api not installed."
                "Please install it with `pip install llamaapi`."
            ) from e

        self._client = Client(api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._additional_kwargs = additional_kwargs or {}
        self.callback_manager = callback_manager or CallbackManager([])

    @property
    def _model_kwargs(self) -> Dict[str, Any]:
        base_kwargs = {
            "model": self._model,
            "temperature": self._temperature,
            "max_length": self._max_tokens,
        }
        model_kwargs = {
            **base_kwargs,
            **self._additional_kwargs,
        }
        return model_kwargs

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=4096,
            num_output=DEFAULT_NUM_OUTPUTS,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name="llama-api",
        )

    @llm_chat_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        message_dicts = to_openai_message_dicts(messages)
        json_dict = {
            "messages": message_dicts,
            **self._model_kwargs,
            **kwargs,
        }
        response = self._client.run(json_dict).json()
        message_dict = response["choices"][0]["message"]
        message = from_openai_message_dict(message_dict)

        return ChatResponse(message=message, raw=response)

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        complete_fn = chat_to_completion_decorator(self.chat)
        return complete_fn(prompt, **kwargs)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        raise NotImplementedError("stream_complete is not supported for LlamaAPI")

    @llm_chat_callback()
    def stream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:
        raise NotImplementedError("stream_chat is not supported for LlamaAPI")
