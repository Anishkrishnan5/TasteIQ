import json
from dataclasses import dataclass
from typing import Any

import requests


class GenerationUnavailableError(RuntimeError):
    """Raised when the optional language-model provider cannot return a valid answer."""


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    cited_source_ids: list[int]


class GeminiClient:
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 20) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> GeneratedAnswer:
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 500,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "answer": {"type": "STRING"},
                        "cited_source_ids": {
                            "type": "ARRAY",
                            "items": {"type": "INTEGER"},
                        },
                    },
                    "required": ["answer", "cited_source_ids"],
                },
            },
        }
        try:
            response = requests.post(
                f"{self.base_url}/{self.model}:generateContent",
                headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed: dict[str, Any] = json.loads(text)
            answer = str(parsed["answer"]).strip()
            source_ids = [int(value) for value in parsed["cited_source_ids"]]
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            raise GenerationUnavailableError(
                "Gemini did not return a valid grounded response."
            ) from exc
        if not answer:
            raise GenerationUnavailableError("Gemini returned an empty response.")
        return GeneratedAnswer(answer=answer, cited_source_ids=source_ids)
