from dataclasses import dataclass
from logging import Logger
from store.store import Store
from ai.DeepSeek import DeepSeek
from ai.RAG import RAG

@dataclass(slots=True)
class TelegramContext:
    store: Store
    ai: DeepSeek
    logger: Logger
    rag: RAG
