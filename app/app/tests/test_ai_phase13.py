import pytest

from app.core.config import Settings
from app.schemas.ai import AIGradingResultInput
from app.services.ai_providers import GradingResponse, QuestionSpec, validate_grading_response


def test_production_settings_reject_wildcard_cors():
    with pytest.raises(ValueError):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="x" * 40, CORS_ORIGINS=["*"])


def test_ai_result_input_rejects_negative_usage_and_confidence():
    with pytest.raises(ValueError):
        AIGradingResultInput(answers=[{"practice_question_id": 1, "ai_score": 1}], prompt_tokens=-1)
    with pytest.raises(ValueError):
        AIGradingResultInput(answers=[{"practice_question_id": 1, "ai_score": 1}], confidence=2)


def test_quality_score_validation_rejects_total_above_maximum():
    result = GradingResponse(total_score=6, confidence=.9,
                             answers=[{"question_key": "q1", "score": 2}])
    with pytest.raises(ValueError, match="Total score"):
        validate_grading_response(result, (QuestionSpec("q1", 5),))
