from app.database.session import Base
from app.models.user import User
from app.models.class_ import Class
from app.models.theory import TheoryArticle
from app.models.exam import PracticeExam, PracticeQuestion, MockExam, MockQuestion
from app.models.submission import Submission, SubmissionAnswer, SubmissionScore
from app.models.assignment import Assignment
from app.models.ai import AISetting, ExamRubric, AIGradingJob, AIGradingResult, AIGradingAnswer

# This file is used by Alembic to import all models and the Base class

from app.models.auth_session import AuthSession
