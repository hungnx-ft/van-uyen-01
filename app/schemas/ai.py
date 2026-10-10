from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AISettingsResponse(BaseModel):
    provider: str
    model: str
    base_url: str | None
    has_api_key: bool
    is_enabled: bool


class AISettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=150)
    base_url: str | None = Field(default=None, max_length=500)
    api_key: str | None = Field(default=None, min_length=1, max_length=4096)
    is_enabled: bool = False


class AIConnectionResponse(BaseModel):
    ok: bool
    message: str


class AIGradingAnswerResponse(BaseModel):
    id: int
    practice_question_id: int | None
    mock_question_id: int | None
    ai_score: float
    ai_question_comment: str | None

    model_config = ConfigDict(from_attributes=True)


class AIGradingResultResponse(BaseModel):
    id: int
    job_id: int
    submission_id: int
    total_score: float | None
    overall_comment: str | None
    improvement_suggestion: str | None
    confidence: float | None
    created_at: datetime
    answers: list[AIGradingAnswerResponse]

    model_config = ConfigDict(from_attributes=True)


class AIGradingJobResponse(BaseModel):
    id: int
    submission_id: int
    rubric_id: int
    provider: str
    model: str
    rubric_version: int
    status: str
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    attempt_count: int = 0
    result: AIGradingResultResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class AIGradingAnswerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    practice_question_id: int | None = None
    mock_question_id: int | None = None
    ai_score: float = Field(ge=0)
    ai_question_comment: str | None = Field(default=None, max_length=10000)


class AIGradingResultInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_score: float | None = Field(default=None, ge=0)
    overall_comment: str | None = Field(default=None, max_length=20000)
    improvement_suggestion: str | None = Field(default=None, max_length=20000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    raw_response: str | None = Field(default=None, max_length=500000)
    answers: list[AIGradingAnswerInput] = Field(min_length=1, max_length=200)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


class AIUsageResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_tokens: int
    estimated_cost_usd: float
    low_confidence_jobs: int
    average_score_deviation: float | None


class AIBulkJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    submission_ids: list[int] = Field(min_length=1, max_length=200)


class AIBulkJobFailure(BaseModel):
    submission_id: int
    detail: str


class AIBulkJobResponse(BaseModel):
    jobs: list[AIGradingJobResponse]
    failed: list[AIBulkJobFailure]


class AIFeedbackUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    teacher_comment: str | None = Field(default=None, max_length=20000)
    teacher_improvement_note: str | None = Field(default=None, max_length=20000)
    publish: bool = False


class AIFeedbackResponse(BaseModel):
    submission_id: int
    teacher_score: float | None
    teacher_comment: str | None
    teacher_improvement_note: str | None
    feedback_published: bool
    feedback_published_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
