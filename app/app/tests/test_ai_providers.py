import pytest

from app.services.ai_providers import (
    GradingResponse,
    OpenAICompatibleProvider,
    ProviderError,
    QuestionSpec,
    _json_from_content,
    validate_grading_response,
)


def specs():
    return (QuestionSpec("q1", 2), QuestionSpec("q2", 3))


def test_fenced_json_is_parsed():
    assert _json_from_content("```json\n{\"ok\": true}\n```") == {"ok": True}


def test_scores_are_checked_against_question_limits():
    result = GradingResponse(
        total_score=4, confidence=0.8,
        answers=[{"question_key": "q1", "score": 2}, {"question_key": "q2", "score": 2}],
    )
    assert validate_grading_response(result, specs()).total_score == 4

    result.answers[0].score = 2.1
    with pytest.raises(ValueError, match="exceeds maximum"):
        validate_grading_response(result, specs())


def test_unknown_and_duplicate_questions_are_rejected():
    unknown = GradingResponse(total_score=1, confidence=0.5,
                              answers=[{"question_key": "q3", "score": 1}])
    with pytest.raises(ValueError, match="Unknown question"):
        validate_grading_response(unknown, specs())
    duplicate = GradingResponse(total_score=2, confidence=0.5,
                                answers=[{"question_key": "q1", "score": 1},
                                         {"question_key": "q1", "score": 1}])
    with pytest.raises(ValueError, match="Duplicate"):
        validate_grading_response(duplicate, specs())


def test_openai_adapter_requires_credentials():
    with pytest.raises(ValueError):
        OpenAICompatibleProvider(api_key="", model="gpt-test")
    with pytest.raises(ValueError):
        OpenAICompatibleProvider(api_key="secret", model="")
