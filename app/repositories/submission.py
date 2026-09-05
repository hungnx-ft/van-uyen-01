from typing import List
from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.submission import Submission, SubmissionAnswer, SubmissionScore
from app.schemas.submission import SubmissionCreate, SubmissionScoreCreate
from pydantic import BaseModel

class CRUDSubmission(CRUDBase[Submission, SubmissionCreate, BaseModel]):
    def create_with_answers(self, db: Session, *, obj_in: SubmissionCreate, student_id: int) -> Submission:
        db_obj = Submission(
            student_id=student_id,
            exam_type=obj_in.exam_type,
            practice_exam_id=obj_in.practice_exam_id,
            mock_exam_id=obj_in.mock_exam_id,
            attempt=obj_in.attempt,
            submitted_at=obj_in.submitted_at,
            status="Submitted"
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        
        for a_in in obj_in.answers:
            db_a = SubmissionAnswer(
                submission_id=db_obj.id,
                practice_question_id=a_in.practice_question_id,
                mock_question_id=a_in.mock_question_id,
                student_answer=a_in.student_answer
            )
            db.add(db_a)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def get_by_student(self, db: Session, *, student_id: int) -> List[Submission]:
        return db.query(Submission).filter(Submission.student_id == student_id).all()
        
    def grade_submission(self, db: Session, *, db_obj: Submission, scores_in: List[SubmissionScoreCreate], teacher_id: int, teacher_comment: str | None = None) -> Submission:
        for score_in in scores_in:
            db_score = SubmissionScore(
                submission_id=db_obj.id,
                answer_id=score_in.answer_id,
                score=score_in.score,
                teacher_comment=score_in.teacher_comment,
                teacher_id=teacher_id
            )
            db.add(db_score)
        db_obj.status = "Graded"
        db_obj.teacher_score = sum(score.score for score in scores_in)
        db_obj.teacher_comment = teacher_comment
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

submission_repo = CRUDSubmission(Submission)
