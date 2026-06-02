from sqlalchemy.orm import Session
from typing import List
from app.repositories.submission import submission_repo
from app.models.submission import Submission
from app.schemas.submission import SubmissionCreate, SubmissionScoreCreate

def create_submission(db: Session, submission_in: SubmissionCreate, student_id: int) -> Submission:
    return submission_repo.create_with_answers(db, obj_in=submission_in, student_id=student_id)

def get_student_submissions(db: Session, student_id: int) -> List[Submission]:
    return submission_repo.get_by_student(db, student_id=student_id)

def grade_submission(db: Session, submission_id: int, scores_in: List[SubmissionScoreCreate], teacher_id: int) -> Submission:
    db_obj = submission_repo.get(db, id=submission_id)
    if not db_obj:
        return None
    return submission_repo.grade_submission(db, db_obj=db_obj, scores_in=scores_in, teacher_id=teacher_id)

def record_anti_cheat_event(db: Session, submission_id: int, event_type: str):
    db_obj = submission_repo.get(db, id=submission_id)
    if not db_obj:
        return None
    if event_type == "tab_switch":
        # Increment leave_tab_count
        new_count = db_obj.leave_tab_count + 1
        return submission_repo.update(db, db_obj=db_obj, obj_in={"leave_tab_count": new_count})
    return db_obj
