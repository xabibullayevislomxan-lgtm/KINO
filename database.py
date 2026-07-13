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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS series (
                code TEXT PRIMARY KEY,
                title TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                series_code TEXT NOT NULL,
                episode_number INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                PRIMARY KEY (series_code, episode_number)
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


# ---------- Seriallar ----------

def add_series(code: str, title: str):
    """Yangi serial qo'shadi (yoki nomini yangilaydi)."""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO series (code, title) VALUES (?, ?)",
            (code, title),
        )
        conn.commit()


def get_series(code: str):
    """Serial nomini qaytaradi yoki None."""
    with get_connection() as conn:
        cur = conn.execute("SELECT title FROM series WHERE code = ?", (code,))
        row = cur.fetchone()
        return row[0] if row else None


def add_episode(series_code: str, episode_number: int, file_id: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO episodes (series_code, episode_number, file_id) "
            "VALUES (?, ?, ?)",
            (series_code, episode_number, file_id),
        )
        conn.commit()


def get_episode(series_code: str, episode_number: int):
    """Bitta qism file_id sini qaytaradi yoki None."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT file_id FROM episodes WHERE series_code = ? AND episode_number = ?",
            (series_code, episode_number),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_episode_numbers(series_code: str):
    """Shu serialning barcha qism raqamlarini (tartiblangan) qaytaradi."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT episode_number FROM episodes WHERE series_code = ? "
            "ORDER BY episode_number",
            (series_code,),
        )
        return [row[0] for row in cur.fetchall()]


def list_all_movies():
    """Barcha oddiy kino kodlarini qaytaradi."""
    with get_connection() as conn:
        cur = conn.execute("SELECT code FROM movies ORDER BY code")
        return [row[0] for row in cur.fetchall()]


def list_all_series():
    """Barcha seriallarni (code, title) qaytaradi."""
    with get_connection() as conn:
        cur = conn.execute("SELECT code, title FROM series ORDER BY code")
        return cur.fetchall()
