from typing import List

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dependencies.permissions import owned_class
from app.models.exam import MockExam, MockQuestion, PracticeExam, PracticeQuestion
from app.models.submission import Submission, SubmissionAnswer
from app.models.user import User
from app.repositories.submission import submission_repo
from app.schemas.submission import SubmissionCreate, SubmissionScoreCreate


def create_submission(db: Session, submission_in: SubmissionCreate, student_id: int) -> Submission:
    if submission_in.exam_type not in ("Practice", "Mock"):
        raise HTTPException(422, "Invalid exam type")
    practice = submission_in.exam_type == "Practice"
    exam_id = submission_in.practice_exam_id if practice else submission_in.mock_exam_id
    other_id = submission_in.mock_exam_id if practice else submission_in.practice_exam_id
    if exam_id is None or other_id is not None:
        raise HTTPException(422, "Exactly one matching exam ID is required")
    exam = db.get(PracticeExam if practice else MockExam, exam_id)
    student = db.get(User, student_id)
    if not exam or (student.class_id and student.student_class.teacher_id != exam.teacher_id):
        raise HTTPException(404, "Exam not found")
    seen = set()
    for answer in submission_in.answers:
        question_id = answer.practice_question_id if practice else answer.mock_question_id
        unrelated = answer.mock_question_id if practice else answer.practice_question_id
        question = db.get(PracticeQuestion if practice else MockQuestion, question_id) if question_id else None
        if not question or question.exam_id != exam_id or unrelated is not None or question_id in seen:
            raise HTTPException(422, "Answers must reference distinct questions belonging to this exam")
        seen.add(question_id)
    return submission_repo.create_with_answers(db, obj_in=submission_in, student_id=student_id)


def get_student_submissions(db: Session, student_id: int) -> List[Submission]:
    return submission_repo.get_by_student(db, student_id=student_id)


def get_teacher_submissions(db: Session, teacher_id: int) -> List[Submission]:
    return (
        db.query(Submission)
        .outerjoin(PracticeExam, Submission.practice_exam_id == PracticeExam.id)
        .outerjoin(MockExam, Submission.mock_exam_id == MockExam.id)
        .filter(or_(PracticeExam.teacher_id == teacher_id, MockExam.teacher_id == teacher_id))
        .order_by(Submission.created_at.desc())
        .all()
    )


def grade_submission(db: Session, submission_id: int, scores_in: List[SubmissionScoreCreate], teacher_id: int, teacher_comment: str | None = None):
    submission = submission_repo.get(db, id=submission_id)
    if not submission:
        raise HTTPException(404, "Submission not found")
    exam = submission.practice_exam if submission.exam_type == "Practice" else submission.mock_exam
    if not exam or exam.teacher_id != teacher_id:
        raise HTTPException(404, "Submission not found")
    if submission.student.class_id:
        owned_class(db, submission.student.class_id, teacher_id)
    for score in scores_in:
        answer = db.get(SubmissionAnswer, score.answer_id)
        if not answer or answer.submission_id != submission_id:
            raise HTTPException(422, "Answer does not belong to this submission")
        if score.score < 0:
            raise HTTPException(422, "Score must be non-negative")
    return submission_repo.grade_submission(
        db, db_obj=submission, scores_in=scores_in, teacher_id=teacher_id, teacher_comment=teacher_comment
    )


def record_anti_cheat_event(db: Session, submission_id: int, event_type: str, student_id: int):
    submission = db.query(Submission).filter(Submission.id == submission_id,
                                            Submission.student_id == student_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    if event_type != "tab_switch":
        raise HTTPException(422, "Unsupported event type")
    db.query(Submission).filter(Submission.id == submission.id).update(
        {Submission.leave_tab_count: Submission.leave_tab_count + 1}, synchronize_session="fetch")
    db.flush()
    return submission
