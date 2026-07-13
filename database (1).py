import sqlite3
from contextlib import contextmanager

DB_NAME = "movies.db"


def init_db():
    """Bazani va jadvalni yaratadi (agar mavjud bo'lmasa)."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                code TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                caption TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT
            )
            """
        )
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()


def add_movie(code: str, file_id: str, caption: str = ""):
    """Yangi kinoni bazaga qo'shadi. Agar kod band bo'lsa, ustidan yozadi."""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO movies (code, file_id, caption) VALUES (?, ?, ?)",
            (code, file_id, caption),
        )
        conn.commit()


def get_movie(code: str):
    """Kod bo'yicha kinoni qaytaradi: (file_id, caption) yoki None."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT file_id, caption FROM movies WHERE code = ?", (code,)
        )
        return cur.fetchone()


def delete_movie(code: str) -> bool:
    """Kinoni o'chiradi. Muvaffaqiyatli bo'lsa True qaytaradi."""
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM movies WHERE code = ?", (code,))
        conn.commit()
        return cur.rowcount > 0


def count_movies() -> int:
    with get_connection() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM movies")
        return cur.fetchone()[0]


def add_user(user_id: int, username: str, full_name: str) -> bool:
    """Yangi foydalanuvchini qo'shadi. Agar u ALLAQACHON mavjud bo'lsa False,
    yangi bo'lsa True qaytaradi (shu orqali admin xabarnomasini faqat
    birinchi marta /start bosganda yuboramiz)."""
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if cur.fetchone():
            return False
        conn.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        conn.commit()
        return True


def count_users() -> int:
    with get_connection() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]
