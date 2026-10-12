"""Explicitly bootstrap a teacher: python -m app.cli.seed_teacher --username ... --full-name ..."""
import argparse
import getpass
import os

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app import models  # noqa: F401
from app.database.session import SessionLocal
from app.schemas.user import AccountCreate
from app.services.user import create_teacher


def main():
    parser = argparse.ArgumentParser(description="Create a teacher without exposing a public API")
    parser.add_argument("--username", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--school-name")
    args = parser.parse_args()
    password = os.environ.get("SEED_TEACHER_PASSWORD") or getpass.getpass("Teacher password: ")
    try:
        request = AccountCreate(username=args.username, password=password, full_name=args.full_name,
                                school_name=args.school_name)
        with SessionLocal.begin() as db:
            user = create_teacher(db, request)
            user_id = user.id
    except ValidationError:
        parser.exit(2, "Invalid account fields: check username, name and password length.\n")
    except HTTPException as exc:
        parser.exit(2, f"{exc.detail}\n")
    except SQLAlchemyError:
        parser.exit(2, "Cannot create teacher: check database connectivity and migrations.\n")
    print(f"Created teacher #{user_id}. Existing accounts are never overwritten.")



if __name__ == "__main__":
    main()
