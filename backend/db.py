"""Database layer using SQLite via SQLAlchemy."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from pathlib import Path
import os
from datetime import datetime

DB_DIR = Path(os.environ.get("XM_DATA_DIR", os.path.expanduser("~/.hermes/workspace/social-match")))
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "profiles.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Initialize database tables."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """))
        conn.commit()


@contextmanager
def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_or_create_session(session_id: str) -> dict:
    """Get or create a user profile session."""
    with get_db() as db:
        result = db.execute(
            text("SELECT profile_json FROM user_profiles WHERE user_id = :sid"),
            {"sid": session_id}
        ).fetchone()
        if result:
            import json
            return json.loads(result[0])
        # Create new session
        import json
        from datetime import datetime
        profile = {
            "user_id": session_id,
            "name": None,
            "age": None,
            "gender": None,
            "interests": [],
            "personality_traits": [],
            "social_preferences": [],
            "goals": [],
            "vector": None,
            "conversation_history": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        db.execute(
            text("INSERT INTO user_profiles VALUES (:uid, :pj, :ca, :ua)"),
            {
                "uid": session_id,
                "pj": json.dumps(profile, ensure_ascii=False),
                "ca": profile["created_at"],
                "ua": profile["updated_at"]
            }
        )
        return profile


def update_session(session_id: str, profile: dict):
    """Update a user profile session."""
    with get_db() as db:
        import json
        profile["updated_at"] = datetime.now().isoformat()
        db.execute(
            text("UPDATE user_profiles SET profile_json = :pj, updated_at = :ua WHERE user_id = :uid"),
            {
                "uid": session_id,
                "pj": json.dumps(profile, ensure_ascii=False),
                "ua": profile["updated_at"]
            }
        )


def append_conversation(session_id: str, role: str, content: str):
    """Append a message to conversation history."""
    from datetime import datetime
    with get_db() as db:
        db.execute(
            text("""
                INSERT INTO conversations (session_id, role, content, timestamp)
                VALUES (:sid, :role, :content, :ts)
            """),
            {"sid": session_id, "role": role, "content": content, "ts": datetime.now().isoformat()}
        )


def get_conversation_history(session_id: str, limit: int = 20) -> list[dict]:
    """Get conversation history for a session."""
    with get_db() as db:
        rows = db.execute(
            text("""
                SELECT role, content, timestamp FROM conversations
                WHERE session_id = :sid ORDER BY id DESC LIMIT :lim
            """),
            {"sid": session_id, "lim": limit}
        ).fetchall()
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in reversed(rows)]
