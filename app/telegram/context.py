from dataclasses import dataclass
from logging import Logger
from typing import TYPE_CHECKING

from store.store import Store

if TYPE_CHECKING:
    from ai.DeepSeek import DeepSeek
    from ai.RAG import RAG

@dataclass(slots=True)
class TelegramContext:
    store: Store
    ai: "DeepSeek"
    logger: Logger
    rag: "RAG"
