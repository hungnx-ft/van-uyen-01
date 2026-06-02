from sqlalchemy.orm import Session
from app.repositories.exam import practice_exam_repo, mock_exam_repo
from app.schemas.exam import PracticeExamCreate, MockExamCreate

def create_practice_exam(db: Session, exam_in: PracticeExamCreate, teacher_id: int):
    # Validate exactly 5 questions
    if len(exam_in.questions) != 5:
        raise ValueError("Practice exam must have exactly 5 questions.")
    
    # Check total score
    total_score = sum(q.max_score for q in exam_in.questions)
    if abs(total_score - 4.0) > 0.01:
        raise ValueError("Practice exam total score must be 4.0.")
        
    return practice_exam_repo.create_with_teacher(db, obj_in=exam_in, teacher_id=teacher_id)

def create_mock_exam(db: Session, exam_in: MockExamCreate, teacher_id: int):
    # Validate section 1: 5 questions, section 2: 2 questions
    section_1 = [q for q in exam_in.questions if q.section == 1]
    section_2 = [q for q in exam_in.questions if q.section == 2]
    
    if len(section_1) != 5 or len(section_2) != 2:
        raise ValueError("Mock exam must have exactly 5 questions in Section 1 and 2 questions in Section 2.")
        
    # Check total score
    total_score = sum(q.max_score for q in exam_in.questions)
    if abs(total_score - 10.0) > 0.01:
        raise ValueError("Mock exam total score must be 10.0.")

    return mock_exam_repo.create_with_teacher(db, obj_in=exam_in, teacher_id=teacher_id)
