import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.api.models import Base, RunModel

logger = logging.getLogger("celesto_ledger")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ledger:ledger@ledger:5432/ledger")

# Fallback mechanism for local testing without active Postgres
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    logger.warning("Postgres unavailable at %s (%s). Falling back to local SQLite ledger.", DATABASE_URL, e)
    engine = create_engine("sqlite:///./ledger.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure seed row exists
    db = SessionLocal()
    try:
        seed = db.query(RunModel).filter_by(sandbox_name="sbx-seeddemo1").first()
        if not seed:
            seed = RunModel(
                run_id="run-seed-001",
                sandbox_name="sbx-seeddemo1",
                problem_id="issue-repro-seed-task",
                state="deleted",
                execution_target="celesto_sandbox"
            )
            db.add(seed)
            db.commit()
            logger.info("Inserted seed row sbx-seeddemo1 into ledger database.")
    except Exception as e:
        db.rollback()
        logger.error("Failed to seed database: %s", e)
    finally:
        db.close()


# Automatically initialize schema on import so tables exist in all environments
try:
    init_db()
except Exception as _e:
    pass


def get_db():

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
