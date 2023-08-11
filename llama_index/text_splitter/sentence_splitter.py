"""Sentence splitter."""
from dataclasses import dataclass
from typing import Callable, List, Optional

from llama_index.callbacks.base import CallbackManager
from llama_index.callbacks.schema import CBEventType, EventPayload
from llama_index.constants import DEFAULT_CHUNK_SIZE
from llama_index.text_splitter.types import MetadataAwareTextSplitter
from llama_index.text_splitter.utils import (
    split_by_char,
    split_by_sentence_tokenizer,
    split_by_regex,
    split_by_sep,
)
from llama_index.utils import globals_helper


@dataclass
class _Split:
    text: str  # the split text
    is_sentence: bool  # save whether this is a full sentence


class SentenceSplitter(MetadataAwareTextSplitter):
    """_Split text with a preference for complete sentences.

    In general, this class tries to keep sentences and paragraphs together. Therefore
    compared to the original TokenTextSplitter, there are less likely to be
    hanging sentences or parts of sentences at the end of the node chunk.
    """

    def __init__(
        self,
        separator: str = " ",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = 200,
        tokenizer: Optional[Callable] = None,
        paragraph_separator: str = "\n\n\n",
        chunking_tokenizer_fn: Optional[Callable[[str], List[str]]] = None,
        secondary_chunking_regex: str = "[^,.;。]+[,.;。]?",
        callback_manager: Optional[CallbackManager] = None,
    ):
        """Initialize with parameters."""
        if chunk_overlap > chunk_size:
            raise ValueError(
                f"Got a larger chunk overlap ({chunk_overlap}) than chunk size "
                f"({chunk_size}), should be smaller."
            )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self.tokenizer = tokenizer or globals_helper.tokenizer
        self.callback_manager = callback_manager or CallbackManager([])

        chunking_tokenizer_fn = chunking_tokenizer_fn or split_by_sentence_tokenizer()

        self._split_fns = [
            split_by_sep(paragraph_separator),
            chunking_tokenizer_fn,
        ]

        self._sub_sentence_split_fns = [
            split_by_regex(secondary_chunking_regex),
            split_by_sep(separator),
            split_by_char(),
        ]

    def split_text_metadata_aware(self, text: str, metadata_str: str) -> List[str]:
        metadata_len = len(self.tokenizer(metadata_str))
        effective_chunk_size = self._chunk_size - metadata_len
        return self._split_text(text, chunk_size=effective_chunk_size)

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, chunk_size=self._chunk_size)

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """
        _Split incoming text and return chunks with overlap size.

        Has a preference for complete sentences, phrases, and minimal overlap.
        """
        if text == "":
            return []

        with self.callback_manager.event(
            CBEventType.CHUNKING, payload={EventPayload.CHUNKS: [text]}
        ) as event:

            splits = self._split(text, chunk_size)
            chunks = self._merge(splits, chunk_size)

            event.on_end(payload={EventPayload.CHUNKS: chunks})

        return chunks

    def _split(self, text: str, chunk_size: int) -> List[_Split]:
        """Break text into splits that are smaller than chunk size.

        The order of splitting is:
        1. split by paragraph separator
        2. split by chunking tokenizer (default is nltk sentence tokenizer)
        3. split by second chunking regex (default is "[^,\.;]+[,\.;]?")
        4. split by default separator (" ")

        """
        if len(self.tokenizer(text)) <= chunk_size:
            return [_Split(text, is_sentence=True)]

        for split_fn in self._split_fns:
            splits = split_fn(text)
            if len(splits) > 1:
                break

        if len(splits) > 1:
            is_sentence = True
        else:
            for split_fn in self._sub_sentence_split_fns:
                splits = split_fn(text)
                if len(splits) > 1:
                    break
            is_sentence = False

        new_splits = []
        for split in splits:
            split_len = len(self.tokenizer(split))
            if split_len <= chunk_size:
                new_splits.append(_Split(split, is_sentence=is_sentence))
            else:
                # recursively split
                new_splits.extend(self._split(split, chunk_size=chunk_size))
        return new_splits

    def _merge(self, splits: List[_Split], chunk_size: int) -> List[str]:
        """Merge splits into chunks."""
        chunks: List[str] = []
        cur_chunk: List[str] = []
        cur_tokens = 0
        while len(splits) > 0:
            cur_token = splits[0]
            cur_len = len(self.tokenizer(cur_token.text))
            if cur_len > chunk_size:
                raise ValueError("Single token exceed chunk size")
            if cur_tokens + cur_len > chunk_size:
                chunks.append("".join(cur_chunk).strip())
                cur_chunk = []
                cur_tokens = 0
            else:
                if (
                    cur_token.is_sentence
                    or cur_tokens + cur_len < chunk_size - self._chunk_overlap
                ):
                    cur_tokens += cur_len
                    cur_chunk.append(cur_token.text)
                    splits.pop(0)
                else:
                    chunks.append("".join(cur_chunk).strip())
                    cur_chunk = []
                    cur_tokens = 0

        # handle the last chunk
        chunk = "".join(cur_chunk).strip()
        if chunk:
            chunks.append(chunk)

        # run postprocessing to remove blank spaces
        chunks = self._postprocess_chunks(chunks)

        return chunks

    def _postprocess_chunks(self, chunks: List[str]) -> List[str]:
        """Post-process chunks."""
        new_chunks = []
        for doc in chunks:
            if doc.replace(" ", "") == "":
                continue
            new_chunks.append(doc)
        return new_chunks
