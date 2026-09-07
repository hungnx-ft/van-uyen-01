"""Provider-neutral AI grading interface.

This module deliberately does not know about database models.  The grading
worker can build a :class:`GradingRequest`, call ``provider.grade`` and then
persist the validated result in the AI grading tables.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ProviderError(RuntimeError):
    """A provider could not return a usable grading response."""


@dataclass(frozen=True)
class QuestionSpec:
    key: str
    max_score: float


@dataclass(frozen=True)
class GradingRequest:
    rubric: str
    submission: str
    questions: tuple[QuestionSpec, ...]


class GradingAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_key: str = Field(min_length=1, max_length=100)
    score: float = Field(ge=0)
    comment: str = Field(default="", max_length=10000)


class GradingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_score: float = Field(ge=0)
    overall_comment: str = Field(default="", max_length=20000)
    improvement_suggestion: str = Field(default="", max_length=20000)
    confidence: float = Field(ge=0, le=1)
    answers: list[GradingAnswer] = Field(min_length=1, max_length=200)


def _json_from_content(content: str) -> dict[str, Any]:
    """Parse plain JSON or a fenced JSON response from a chat model."""
    text = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError("Provider returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ProviderError("Provider response must be a JSON object")
    return value


def validate_grading_response(response: GradingResponse, questions: tuple[QuestionSpec, ...]) -> GradingResponse:
    """Ensure every returned score belongs to a question and its max score."""
    limits = {question.key: question.max_score for question in questions}
    if len(limits) != len(questions):
        raise ValueError("Question keys must be unique")
    seen: set[str] = set()
    for answer in response.answers:
        maximum = limits.get(answer.question_key)
        if maximum is None:
            raise ValueError(f"Unknown question key: {answer.question_key}")
        if answer.question_key in seen:
            raise ValueError(f"Duplicate question key: {answer.question_key}")
        if answer.score > maximum:
            raise ValueError(f"Score for {answer.question_key} exceeds maximum {maximum}")
        seen.add(answer.question_key)
    if response.total_score > sum(limits.values()) + 1e-6:
        raise ValueError("Total score exceeds exam maximum")
    return response


class GradingProvider(Protocol):
    async def grade(self, request: GradingRequest) -> GradingResponse: ...


class OpenAICompatibleProvider:
    """Adapter for OpenAI Chat Completions and compatible APIs."""

    def __init__(self, *, api_key: str, model: str, base_url: str = "https://api.openai.com/v1",
                 timeout: float = 90.0):
        if not api_key.strip():
            raise ValueError("api_key is required")
        if not model.strip():
            raise ValueError("model is required")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _prompt(request: GradingRequest) -> tuple[str, str]:
        schema = {
            "total_score": "number",
            "overall_comment": "string",
            "improvement_suggestion": "string",
            "confidence": "number between 0 and 1",
            "answers": [{"question_key": "string", "score": "number", "comment": "string"}],
        }
        system = (
            "Bạn là trợ lý chấm bài. Chấm công bằng theo barem, chỉ trả về JSON hợp lệ, "
            f"đúng schema này: {json.dumps(schema, ensure_ascii=False)}. "
            "Không thêm markdown hay khóa nào khác."
        )
        question_limits = "\n".join(f"- {q.key}: tối đa {q.max_score}" for q in request.questions)
        user = (f"BAREM:\n{request.rubric}\n\nBÀI LÀM:\n{request.submission}\n\n"
                f"CÂU HỎI VÀ ĐIỂM TỐI ĐA:\n{question_limits}")
        return system, user

    async def grade(self, request: GradingRequest) -> GradingResponse:
        if len(request.rubric.encode("utf-8")) > 500_000 or len(request.submission.encode("utf-8")) > 500_000:
            raise ProviderError("Rubric or submission is too large")
        system, user = self._prompt(request)
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
                content = body["choices"][0]["message"]["content"]
            result = GradingResponse.model_validate(_json_from_content(content))
            return validate_grading_response(result, request.questions)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValidationError, ValueError) as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(f"Invalid provider grading response: {exc}") from exc


def build_provider(*, provider: str, api_key: str, model: str, base_url: str | None = None) -> GradingProvider:
    normalized = provider.strip().lower()
    if normalized in {"openai", "openai-compatible"}:
        return OpenAICompatibleProvider(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.openai.com/v1",
        )
    raise ValueError(f"Provider adapter not implemented: {provider}")
