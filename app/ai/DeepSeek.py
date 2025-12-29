import logging
import asyncio
from typing import Optional, Dict, Any, Callable

from ai.skeleton import Skeleton
from dsk.api import (
    DeepSeekAPI,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    APIError,
)

class DeepSeek(Skeleton):
    def __init__(self, logger: logging, userToken: str, system_prompt: str = "", system_files_id: list[str] = []):
        self.logger: logging = logger
        self.api = DeepSeekAPI(userToken)
        self.system_prompt = system_prompt
        self.system_files_id = system_files_id

        # настройки ретраев
        self._max_retries = 5
        self._base_backoff = 1  # секунды

    async def _to_thread(self, fn: Callable, *args, **kwargs):
        """Запускает синхронный вызов API в отдельном треде без трюков с event loop."""
        return await asyncio.to_thread(fn, *args, **kwargs)

    async def _retryable(self, func: Callable, *args, **kwargs):
        """Ретраит сеть/лимиты с экспоненциальной паузой; аутентификацию не ретраит."""
        for attempt in range(1, self._max_retries + 1):
            self.logger.info("[DeepSeek] Attempt %d/%d to call %s", attempt, self._max_retries, func.__name__)
            try:
                return await self._to_thread(func, *args, **kwargs)
            
            except AuthenticationError as e:
                self.logger.exception(f"[DeepSeek] Auth error on attempt {attempt}: {e}")
                raise
            except (RateLimitError, NetworkError, APIError) as e:
                if attempt == self._max_retries:
                    self.logger.exception(f"[DeepSeek] Failed after {attempt} attempts: {e}")
                    raise
                sleep_for = self._base_backoff * (2 ** (attempt - 1))
                self.logger.warning(f"[DeepSeek] Retrying in {sleep_for}s (attempt {attempt}/{self._max_retries})")
                await asyncio.sleep(sleep_for)
            except Exception as e:
                self.logger.warning(f"[DeepSeek] Error: {e}")
                raise

    async def send(self, message: str, session_id: str, parent_id: Optional[str] = None, ref_file_ids: list = []) -> Dict[str, Any]:
        return await self._retryable(self.api.chat_completion, session_id, message, parent_id, ref_file_ids)

    async def create_thread(self) -> tuple[str, Optional[int]]:
        response = {}
        
        session_id: str = await self._retryable(self.api.create_chat_session)
        if self.system_prompt:
            try:
                response = await self.send(self.system_prompt, session_id, ref_file_ids=self.system_files_id)
            except Exception as e:
                self.logger.exception(f"[DeepSeek] Failed to apply system prompt for session {session_id}: {e}", )

        return session_id, response.get("next_parent_id", None)
    
    async def upload_file(self, file_path: str) -> str:
        return await self._retryable(self.api.upload_file, file_path)