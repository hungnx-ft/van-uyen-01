from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.submission import AntiCheatEvent
from app.services.submission import record_anti_cheat_event
from app.dependencies.auth import get_current_student
from app.models.user import User

router = APIRouter()

@router.post("/event")
def log_anti_cheat_event(
    event: AntiCheatEvent,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    submission = record_anti_cheat_event(db, submission_id=event.submission_id, event_type=event.event_type, student_id=current_user.id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": "Event recorded", "leave_tab_count": submission.leave_tab_count}
