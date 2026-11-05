import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from config import DB_PATH, VIP_PRICE, VIP_DURATION_DAYS, FREE_TICKETS

def _sync_init_db():
    with sqlite3.connect(DB_PATH) as db:
        # 1. users
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                referred_by INTEGER DEFAULT NULL,
                vip_until TEXT DEFAULT NULL,
                created_at TEXT
            )
        """)
        # 2. unlocked_tickets
        db.execute("""
            CREATE TABLE IF NOT EXISTS unlocked_tickets (
                telegram_id INTEGER,
                ticket_number INTEGER,
                created_at TEXT,
                PRIMARY KEY (telegram_id, ticket_number)
            )
        """)
        # 3. user_errors (xatolar ustida ishlash)
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_errors (
                telegram_id INTEGER,
                question_id INTEGER,
                wrong_count INTEGER DEFAULT 1,
                created_at TEXT,
                PRIMARY KEY (telegram_id, question_id)
            )
        """)
        # 4. payments
        db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                receipt_photo_id TEXT,
                amount INTEGER DEFAULT 30000,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        # 5. test_results
        db.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                ticket_id INTEGER,
                score INTEGER,
                total INTEGER DEFAULT 20,
                passed INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        db.commit()

async def init_db():
    await asyncio.to_thread(_sync_init_db)

def _is_vip_active(vip_until_str: Optional[str]) -> bool:
    if not vip_until_str:
        return False
    try:
        exp = datetime.fromisoformat(vip_until_str)
        return datetime.now() < exp
    except Exception:
        return False

def _sync_get_or_create_user(telegram_id: int, full_name: str, username: str, referred_by: Optional[int] = None) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if row:
            # Mavjud foydalanuvchi ma'lumotlarini yangilash
            db.execute("UPDATE users SET full_name = ?, username = ? WHERE telegram_id = ?", (full_name, username, telegram_id))
            db.commit()
            cur = db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = dict(cur.fetchone())
            user["is_vip"] = _is_vip_active(user.get("vip_until"))
            return user

        # Yangi foydalanuvchi
        valid_ref = None
        if referred_by and referred_by != telegram_id:
            c = db.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (referred_by,))
            if c.fetchone():
                valid_ref = referred_by
                # Referal egasiga bilet sovg'a qilish
                _sync_unlock_next_referral_ticket(db, valid_ref)

        db.execute("""
            INSERT INTO users (telegram_id, full_name, username, referred_by, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, full_name, username, valid_ref, now))
        db.commit()

        return {
            "telegram_id": telegram_id,
            "full_name": full_name,
            "username": username,
            "referred_by": valid_ref,
            "vip_until": None,
            "is_vip": False,
            "created_at": now
        }

def _sync_unlock_next_referral_ticket(db: sqlite3.Connection, telegram_id: int) -> Optional[int]:
    """Referal orqali 4-biletdan boshlab navbatdagi qulflangan biletni ochadi"""
    cur = db.execute("SELECT ticket_number FROM unlocked_tickets WHERE telegram_id = ?", (telegram_id,))
    already_unlocked = {r[0] for r in cur.fetchall()}
    
    # 4-dan 70-gacha birinchi ochiq bo'lmagan biletni topish
    for t_num in range(4, 71):
        if t_num not in already_unlocked:
            now = datetime.now().isoformat()
            db.execute("""
                INSERT OR IGNORE INTO unlocked_tickets (telegram_id, ticket_number, created_at)
                VALUES (?, ?, ?)
            """, (telegram_id, t_num, now))
            return t_num
    return None

async def get_or_create_user(telegram_id: int, full_name: str, username: str, referred_by: Optional[int] = None) -> Dict[str, Any]:
    return await asyncio.to_thread(_sync_get_or_create_user, telegram_id, full_name, username, referred_by)

def _sync_get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["is_vip"] = _is_vip_active(res.get("vip_until"))
        return res

async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_get_user, telegram_id)

def _sync_get_unlocked_tickets(telegram_id: int, total_tickets: int = 70) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT vip_until FROM users WHERE telegram_id = ?", (telegram_id,))
        u = cur.fetchone()
        vip_active = _is_vip_active(u["vip_until"]) if u else False

        if vip_active:
            # Barcha biletlar ochiq
            return {
                "is_vip": True,
                "vip_until": u["vip_until"],
                "unlocked_tickets": list(range(1, total_tickets + 1))
            }

        # Standart holat: 1, 2, 3 doim ochiq + referal orqali ochilganlar
        cur = db.execute("SELECT ticket_number FROM unlocked_tickets WHERE telegram_id = ?", (telegram_id,))
        extra = [r[0] for r in cur.fetchall()]
        all_unlocked = sorted(list(set(FREE_TICKETS + extra)))
        return {
            "is_vip": False,
            "vip_until": None,
            "unlocked_tickets": all_unlocked
        }

async def get_unlocked_tickets(telegram_id: int, total_tickets: int = 70) -> Dict[str, Any]:
    return await asyncio.to_thread(_sync_get_unlocked_tickets, telegram_id, total_tickets)

def _sync_create_payment(telegram_id: int, receipt_photo_id: str, amount: int = VIP_PRICE) -> int:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("""
            INSERT INTO payments (telegram_id, receipt_photo_id, amount, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (telegram_id, receipt_photo_id, amount, now))
        db.commit()
        return cur.lastrowid

async def create_payment(telegram_id: int, receipt_photo_id: str, amount: int = VIP_PRICE) -> int:
    return await asyncio.to_thread(_sync_create_payment, telegram_id, receipt_photo_id, amount)

def _sync_get_payment(payment_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        row = cur.fetchone()
        return dict(row) if row else None

async def get_payment(payment_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_get_payment, payment_id)

def _sync_approve_payment(payment_id: int) -> Optional[Dict[str, Any]]:
    now = datetime.now()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        p = cur.fetchone()
        if not p or p["status"] != "pending":
            return None

        telegram_id = p["telegram_id"]
        # Hozirgi vip muddatini tekshirish (agar faol bo'lsa unga qo'shiladi)
        u_cur = db.execute("SELECT vip_until FROM users WHERE telegram_id = ?", (telegram_id,))
        u = u_cur.fetchone()
        start_date = now
        if u and u["vip_until"]:
            try:
                curr_exp = datetime.fromisoformat(u["vip_until"])
                if curr_exp > now:
                    start_date = curr_exp
            except Exception:
                pass

        new_vip_until = (start_date + timedelta(days=VIP_DURATION_DAYS)).isoformat()

        db.execute("UPDATE payments SET status = 'approved' WHERE id = ?", (payment_id,))
        db.execute("UPDATE users SET vip_until = ? WHERE telegram_id = ?", (new_vip_until, telegram_id))
        db.commit()

        return {
            "telegram_id": telegram_id,
            "vip_until": new_vip_until,
            "days": VIP_DURATION_DAYS
        }

async def approve_payment(payment_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_approve_payment, payment_id)

def _sync_reject_payment(payment_id: int) -> Optional[int]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        p = cur.fetchone()
        if not p or p["status"] != "pending":
            return None

        telegram_id = p["telegram_id"]
        db.execute("UPDATE payments SET status = 'rejected' WHERE id = ?", (payment_id,))
        db.commit()
        return telegram_id

async def reject_payment(payment_id: int) -> Optional[int]:
    return await asyncio.to_thread(_sync_reject_payment, payment_id)

# Xatolar bilan ishlash
def _sync_save_user_error(telegram_id: int, question_id: int):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            INSERT INTO user_errors (telegram_id, question_id, wrong_count, created_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(telegram_id, question_id) DO UPDATE SET
                wrong_count = wrong_count + 1,
                created_at = excluded.created_at
        """, (telegram_id, question_id, now))
        db.commit()

async def save_user_error(telegram_id: int, question_id: int):
    await asyncio.to_thread(_sync_save_user_error, telegram_id, question_id)

def _sync_resolve_user_error(telegram_id: int, question_id: int):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DELETE FROM user_errors WHERE telegram_id = ? AND question_id = ?", (telegram_id, question_id))
        db.commit()

async def resolve_user_error(telegram_id: int, question_id: int):
    await asyncio.to_thread(_sync_resolve_user_error, telegram_id, question_id)

def _sync_get_user_errors(telegram_id: int) -> List[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("SELECT question_id FROM user_errors WHERE telegram_id = ? ORDER BY wrong_count DESC", (telegram_id,))
        return [r[0] for r in cur.fetchall()]

async def get_user_errors(telegram_id: int) -> List[int]:
    return await asyncio.to_thread(_sync_get_user_errors, telegram_id)

# Test natijalari
def _sync_record_test_result(telegram_id: int, ticket_id: int, score: int, total: int = 20):
    passed = 1 if score >= 18 else 0
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            INSERT INTO test_results (telegram_id, ticket_id, score, total, passed, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, ticket_id, score, total, passed, now))
        db.commit()

async def record_test_result(telegram_id: int, ticket_id: int, score: int, total: int = 20):
    await asyncio.to_thread(_sync_record_test_result, telegram_id, ticket_id, score, total)

# Statistika va Admin
def _sync_get_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as db:
        total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        # VIP faol foydalanuvchilar
        now_str = datetime.now().isoformat()
        vip_users = db.execute("SELECT COUNT(*) FROM users WHERE vip_until > ?", (now_str,)).fetchone()[0]
        total_tests = db.execute("SELECT COUNT(*) FROM test_results").fetchone()[0]
        pending_payments = db.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'").fetchone()[0]
        total_earned = db.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'").fetchone()[0]
        return {
            "total_users": total_users,
            "vip_users": vip_users,
            "total_tests": total_tests,
            "pending_payments": pending_payments,
            "total_earned": total_earned
        }

async def get_stats() -> Dict[str, Any]:
    return await asyncio.to_thread(_sync_get_stats)

def _sync_get_all_user_ids() -> List[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("SELECT telegram_id FROM users")
        return [r[0] for r in cur.fetchall()]

async def get_all_user_ids() -> List[int]:
    return await asyncio.to_thread(_sync_get_all_user_ids)
