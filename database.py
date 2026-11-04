import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from config import DB_PATH, PACKAGES

def _sync_init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                unlocked_max_ticket INTEGER DEFAULT 3,
                vip_until TEXT DEFAULT NULL,
                referrer_id INTEGER DEFAULT NULL,
                invited_count INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                package_key TEXT,
                photo_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                wrong_count INTEGER DEFAULT 1,
                is_resolved INTEGER DEFAULT 0,
                last_updated TEXT,
                UNIQUE(user_id, question_id)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticket_id INTEGER,
                score INTEGER,
                total INTEGER,
                passed INTEGER,
                created_at TEXT
            )
        """)
        db.commit()

async def init_db():
    _sync_init_db()

def _sync_get_or_create_user(user_id: int, first_name: str, username: str, referrer_id: Optional[int] = None) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            user = dict(row)
            if user.get("vip_until"):
                try:
                    exp = datetime.fromisoformat(user["vip_until"])
                    if datetime.now() > exp:
                        db.execute(
                            "UPDATE users SET unlocked_max_ticket = 3, vip_until = NULL WHERE user_id = ?",
                            (user_id,)
                        )
                        db.commit()
                        user["unlocked_max_ticket"] = 3
                        user["vip_until"] = None
                except Exception:
                    pass
            return user

        ref_valid = None
        if referrer_id and referrer_id != user_id:
            c = db.execute("SELECT user_id, unlocked_max_ticket FROM users WHERE user_id = ?", (referrer_id,))
            ref_user = c.fetchone()
            if ref_user:
                ref_valid = referrer_id
                new_max = ref_user["unlocked_max_ticket"] + 1
                db.execute("""
                    UPDATE users 
                    SET invited_count = invited_count + 1,
                        unlocked_max_ticket = ?
                    WHERE user_id = ?
                """, (new_max, referrer_id))

        db.execute("""
            INSERT INTO users (user_id, first_name, username, unlocked_max_ticket, referrer_id, created_at)
            VALUES (?, ?, ?, 3, ?, ?)
        """, (user_id, first_name, username, ref_valid, now))
        db.commit()

        return {
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "unlocked_max_ticket": 3,
            "vip_until": None,
            "referrer_id": ref_valid,
            "invited_count": 0,
            "created_at": now
        }

async def get_or_create_user(user_id: int, first_name: str, username: str, referrer_id: Optional[int] = None) -> Dict[str, Any]:
    return await asyncio.to_thread(_sync_get_or_create_user, user_id, first_name, username, referrer_id)

def _sync_get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_get_user, user_id)

def _sync_create_receipt(user_id: int, package_key: str, photo_id: str) -> int:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("""
            INSERT INTO receipts (user_id, package_key, photo_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, package_key, photo_id, now))
        db.commit()
        return cur.lastrowid

async def create_receipt(user_id: int, package_key: str, photo_id: str) -> int:
    return await asyncio.to_thread(_sync_create_receipt, user_id, package_key, photo_id)

def _sync_get_receipt(receipt_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
        row = cur.fetchone()
        return dict(row) if row else None

async def get_receipt(receipt_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_get_receipt, receipt_id)

def _sync_approve_receipt(receipt_id: int) -> Optional[Dict[str, Any]]:
    now = datetime.now()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
        receipt = cur.fetchone()
        if not receipt or receipt["status"] != "pending":
            return None

        user_id = receipt["user_id"]
        pkg_key = receipt["package_key"]
        pkg = PACKAGES.get(pkg_key, PACKAGES["pack_4_6"])

        vip_until = (now + timedelta(days=pkg["duration_days"])).strftime("%Y-%m-%d %H:%M:%S")

        c = db.execute("SELECT unlocked_max_ticket FROM users WHERE user_id = ?", (user_id,))
        u_row = c.fetchone()
        curr_max = u_row["unlocked_max_ticket"] if u_row else 3
        new_max = max(curr_max, pkg["to_ticket"])

        db.execute("UPDATE receipts SET status = 'approved' WHERE id = ?", (receipt_id,))
        db.execute("""
            UPDATE users 
            SET unlocked_max_ticket = ?,
                vip_until = ?
            WHERE user_id = ?
        """, (new_max, vip_until, user_id))
        db.commit()

        return {
            "user_id": user_id,
            "new_max_ticket": new_max,
            "vip_until": vip_until,
            "package_title": pkg["title"]
        }

async def approve_receipt(receipt_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_approve_receipt, receipt_id)

def _sync_reject_receipt(receipt_id: int) -> Optional[int]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
        receipt = cur.fetchone()
        if not receipt or receipt["status"] != "pending":
            return None

        user_id = receipt["user_id"]
        db.execute("UPDATE receipts SET status = 'rejected' WHERE id = ?", (receipt_id,))
        db.commit()
        return user_id

async def reject_receipt(receipt_id: int) -> Optional[int]:
    return await asyncio.to_thread(_sync_reject_receipt, receipt_id)

def _sync_record_mistake(user_id: int, question_id: int):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            INSERT INTO mistakes (user_id, question_id, wrong_count, is_resolved, last_updated)
            VALUES (?, ?, 1, 0, ?)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
                wrong_count = wrong_count + 1,
                is_resolved = 0,
                last_updated = excluded.last_updated
        """, (user_id, question_id, now))
        db.commit()

async def record_mistake(user_id: int, question_id: int):
    await asyncio.to_thread(_sync_record_mistake, user_id, question_id)

def _sync_resolve_mistake(user_id: int, question_id: int):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            UPDATE mistakes 
            SET is_resolved = 1 
            WHERE user_id = ? AND question_id = ?
        """, (user_id, question_id))
        db.commit()

async def resolve_mistake(user_id: int, question_id: int):
    await asyncio.to_thread(_sync_resolve_mistake, user_id, question_id)

def _sync_get_user_mistakes(user_id: int) -> List[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("""
            SELECT question_id FROM mistakes 
            WHERE user_id = ? AND is_resolved = 0
            ORDER BY wrong_count DESC
        """, (user_id,))
        rows = cur.fetchall()
        return [r[0] for r in rows]

async def get_user_mistakes(user_id: int) -> List[int]:
    return await asyncio.to_thread(_sync_get_user_mistakes, user_id)

def _sync_record_test_result(user_id: int, ticket_id: int, score: int, total: int = 20):
    passed = 1 if score >= 18 else 0
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            INSERT INTO test_results (user_id, ticket_id, score, total, passed, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, ticket_id, score, total, passed, now))
        db.commit()

async def record_test_result(user_id: int, ticket_id: int, score: int, total: int = 20):
    await asyncio.to_thread(_sync_record_test_result, user_id, ticket_id, score, total)

def _sync_get_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as db:
        total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        paid_users = db.execute("SELECT COUNT(*) FROM users WHERE unlocked_max_ticket > 3").fetchone()[0]
        total_tests = db.execute("SELECT COUNT(*) FROM test_results").fetchone()[0]
        pending_receipts = db.execute("SELECT COUNT(*) FROM receipts WHERE status = 'pending'").fetchone()[0]
        return {
            "total_users": total_users,
            "paid_users": paid_users,
            "total_tests": total_tests,
            "pending_receipts": pending_receipts
        }

async def get_stats() -> Dict[str, Any]:
    return await asyncio.to_thread(_sync_get_stats)

def _sync_get_all_user_ids() -> List[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("SELECT user_id FROM users")
        return [r[0] for r in cur.fetchall()]

async def get_all_user_ids() -> List[int]:
    return await asyncio.to_thread(_sync_get_all_user_ids)
