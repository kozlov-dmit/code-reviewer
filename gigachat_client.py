import logging
from typing import Dict, List, Optional

import requests


class GigaChatClient:
    """Tiny client for sending prompts to GigaChat-compatible OpenAI API."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://gigachat.devices.sberbank.ru/api/v1",
        model: str = "GigaChat",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        logging.debug("POST %s payload keys=%s", url, list(payload.keys()))
        response = self.session.post(url, json=payload, timeout=60)
        if not response.ok:
            raise RuntimeError(f"GigaChat API error {response.status_code}: {response.text}")
        data = response.json()
        # OpenAI-compatible shape
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected GigaChat response: {data}") from exc
