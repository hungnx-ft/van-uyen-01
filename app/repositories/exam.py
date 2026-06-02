from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.exam import PracticeExam, MockExam, PracticeQuestion, MockQuestion
from app.schemas.exam import PracticeExamCreate, PracticeExamBase, MockExamCreate, MockExamBase

class CRUDPracticeExam(CRUDBase[PracticeExam, PracticeExamBase, PracticeExamBase]):
    def create_with_teacher(self, db: Session, *, obj_in: PracticeExamCreate, teacher_id: int) -> PracticeExam:
        db_obj = PracticeExam(title=obj_in.title, teacher_id=teacher_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        for q_in in obj_in.questions:
            db_q = PracticeQuestion(
                exam_id=db_obj.id,
                content=q_in.content,
                max_score=q_in.max_score
            )
            db.add(db_q)
        db.commit()
        db.refresh(db_obj)
        return db_obj

class CRUDMockExam(CRUDBase[MockExam, MockExamBase, MockExamBase]):
    def create_with_teacher(self, db: Session, *, obj_in: MockExamCreate, teacher_id: int) -> MockExam:
        db_obj = MockExam(title=obj_in.title, teacher_id=teacher_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        for q_in in obj_in.questions:
            db_q = MockQuestion(
                exam_id=db_obj.id,
                section=q_in.section,
                content=q_in.content,
                max_score=q_in.max_score
            )
            db.add(db_q)
        db.commit()
        db.refresh(db_obj)
        return db_obj

practice_exam_repo = CRUDPracticeExam(PracticeExam)
mock_exam_repo = CRUDMockExam(MockExam)
