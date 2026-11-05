import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from config import (
    DB_PATH,
    PRICE_3_TICKETS,
    PRICE_EXAM_1,
    PRICE_EXAM_30,
    PRICE_VIP_90,
    FREE_TICKETS,
    TOTAL_TICKETS
)

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
                exam_pass_until TEXT DEFAULT NULL,
                exam_attempts INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        # Migration: ustunlar mavjudligini tekshirish
        cur = db.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if "exam_pass_until" not in cols:
            db.execute("ALTER TABLE users ADD COLUMN exam_pass_until TEXT DEFAULT NULL")
        if "exam_attempts" not in cols:
            db.execute("ALTER TABLE users ADD COLUMN exam_attempts INTEGER DEFAULT 0")

        # 2. unlocked_tickets
        db.execute("""
            CREATE TABLE IF NOT EXISTS unlocked_tickets (
                telegram_id INTEGER,
                ticket_number INTEGER,
                expires_at TEXT DEFAULT NULL,
                created_at TEXT,
                PRIMARY KEY (telegram_id, ticket_number)
            )
        """)
        cur = db.execute("PRAGMA table_info(unlocked_tickets)")
        ut_cols = {row[1] for row in cur.fetchall()}
        if "expires_at" not in ut_cols:
            db.execute("ALTER TABLE unlocked_tickets ADD COLUMN expires_at TEXT DEFAULT NULL")

        # 3. user_errors (xatolar tahlili)
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
                payment_type TEXT DEFAULT 'vip_90',
                details TEXT,
                ticket_numbers TEXT,
                receipt_photo_id TEXT,
                amount INTEGER DEFAULT 30000,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        cur = db.execute("PRAGMA table_info(payments)")
        p_cols = {row[1] for row in cur.fetchall()}
        if "payment_type" not in p_cols:
            db.execute("ALTER TABLE payments ADD COLUMN payment_type TEXT DEFAULT 'vip_90'")
        if "details" not in p_cols:
            db.execute("ALTER TABLE payments ADD COLUMN details TEXT")
        if "ticket_numbers" not in p_cols:
            db.execute("ALTER TABLE payments ADD COLUMN ticket_numbers TEXT")

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

        # 6. pending_payment_selections (Mini Appdan tanlangan xaridni bot bilan sinxronlash)
        db.execute("""
            CREATE TABLE IF NOT EXISTS pending_payment_selections (
                telegram_id INTEGER PRIMARY KEY,
                payment_type TEXT,
                details TEXT,
                ticket_numbers TEXT,
                amount INTEGER,
                updated_at TEXT
            )
        """)
        db.commit()

def _sync_save_pending_selection(telegram_id: int, payment_type: str, details: str, ticket_numbers: str, amount: int):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            INSERT OR REPLACE INTO pending_payment_selections (telegram_id, payment_type, details, ticket_numbers, amount, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, payment_type, details, ticket_numbers, amount, now))
        db.commit()

async def save_pending_selection(telegram_id: int, payment_type: str, details: str, ticket_numbers: str, amount: int):
    await asyncio.to_thread(_sync_save_pending_selection, telegram_id, payment_type, details, ticket_numbers, amount)

def _sync_get_pending_selection(telegram_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM pending_payment_selections WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return dict(row) if row else None

async def get_pending_selection(telegram_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_get_pending_selection, telegram_id)

def _sync_clear_pending_selection(telegram_id: int):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DELETE FROM pending_payment_selections WHERE telegram_id = ?", (telegram_id,))
        db.commit()

async def clear_pending_selection(telegram_id: int):
    await asyncio.to_thread(_sync_clear_pending_selection, telegram_id)

async def init_db():
    await asyncio.to_thread(_sync_init_db)

def _is_active(dt_str: Optional[str]) -> bool:
    if not dt_str:
        return False
    try:
        exp = datetime.fromisoformat(dt_str)
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
            db.execute("UPDATE users SET full_name = ?, username = ? WHERE telegram_id = ?", (full_name, username, telegram_id))
            db.commit()
            cur = db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = dict(cur.fetchone())
            user["is_vip"] = _is_active(user.get("vip_until"))
            user["has_exam_pass"] = _is_active(user.get("exam_pass_until"))
            return user

        # Yangi foydalanuvchi
        valid_ref = None
        if referred_by and referred_by != telegram_id:
            c = db.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (referred_by,))
            if c.fetchone():
                valid_ref = referred_by
                # Taklif qilganga navbatdagi qulflangan biletni ochish
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
            "exam_pass_until": None,
            "exam_attempts": 0,
            "is_vip": False,
            "has_exam_pass": False,
            "created_at": now
        }

def _sync_unlock_next_referral_ticket(db: sqlite3.Connection, telegram_id: int) -> Optional[int]:
    """Referal orqali hali ochilmagan eng birinchi biletni topib ochadi"""
    cur = db.execute("SELECT ticket_number FROM unlocked_tickets WHERE telegram_id = ?", (telegram_id,))
    already_unlocked = {r[0] for r in cur.fetchall()}
    
    for t_num in range(4, TOTAL_TICKETS + 1):
        if t_num not in already_unlocked:
            now = datetime.now()
            exp = (now + timedelta(days=90)).isoformat()
            db.execute("""
                INSERT OR REPLACE INTO unlocked_tickets (telegram_id, ticket_number, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, t_num, exp, now.isoformat()))
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
        res["is_vip"] = _is_active(res.get("vip_until"))
        res["has_exam_pass"] = _is_active(res.get("exam_pass_until"))
        return res

async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_get_user, telegram_id)

def _sync_get_user_access(telegram_id: int, total_tickets: int = TOTAL_TICKETS) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        u = cur.fetchone()
        
        is_vip = _is_active(u["vip_until"]) if u else False
        has_exam_pass = _is_active(u["exam_pass_until"]) if u else False
        attempts = u["exam_attempts"] if (u and u["exam_attempts"]) else 0

        now_str = datetime.now().isoformat()
        
        if is_vip:
            unlocked = list(range(1, total_tickets + 1))
            can_exam = True
        else:
            # 1, 2, 3 doim ochiq + muddati tugamagan xaridlar / referallar
            c = db.execute("""
                SELECT ticket_number FROM unlocked_tickets 
                WHERE telegram_id = ? AND (expires_at IS NULL OR expires_at > ?)
            """, (telegram_id, now_str))
            extra = [r[0] for r in c.fetchall()]
            unlocked = sorted(list(set(FREE_TICKETS + extra)))
            # Imtihon huquqi: VIP yoki 30 kunlik ruxsat yoki urinishlar soni > 0 yoki barcha biletlar ochiq
            can_exam = has_exam_pass or (attempts > 0) or (len(unlocked) >= total_tickets)

        return {
            "telegram_id": telegram_id,
            "is_vip": is_vip,
            "vip_until": u["vip_until"] if u else None,
            "has_exam_pass": has_exam_pass,
            "exam_pass_until": u["exam_pass_until"] if u else None,
            "exam_attempts": attempts,
            "can_take_exam": can_exam,
            "unlocked_tickets": unlocked,
            "total_tickets": total_tickets
        }

async def get_user_access(telegram_id: int, total_tickets: int = TOTAL_TICKETS) -> Dict[str, Any]:
    return await asyncio.to_thread(_sync_get_user_access, telegram_id, total_tickets)

def _sync_consume_exam_attempt(telegram_id: int) -> bool:
    """Imtihon topshirish uchun 1 ta urinishni sarflaydi (agar VIP yoki 30 kunlik bo'lmasa)"""
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT vip_until, exam_pass_until, exam_attempts FROM users WHERE telegram_id = ?", (telegram_id,))
        u = cur.fetchone()
        if not u:
            return False

        if _is_active(u["vip_until"]) or _is_active(u["exam_pass_until"]):
            return True # Cheksiz ruxsat

        if u["exam_attempts"] and u["exam_attempts"] > 0:
            db.execute("UPDATE users SET exam_attempts = exam_attempts - 1 WHERE telegram_id = ?", (telegram_id,))
            db.commit()
            return True

        return False

async def consume_exam_attempt(telegram_id: int) -> bool:
    return await asyncio.to_thread(_sync_consume_exam_attempt, telegram_id)

def _sync_unlock_tickets(telegram_id: int, ticket_numbers: List[int], days: int = 90):
    now = datetime.now()
    exp = (now + timedelta(days=days)).isoformat()
    with sqlite3.connect(DB_PATH) as db:
        for num in ticket_numbers:
            db.execute("""
                INSERT OR REPLACE INTO unlocked_tickets (telegram_id, ticket_number, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, int(num), exp, now.isoformat()))
        db.commit()

async def unlock_tickets(telegram_id: int, ticket_numbers: List[int], days: int = 90):
    await asyncio.to_thread(_sync_unlock_tickets, telegram_id, ticket_numbers, days)

def _sync_create_payment(
    telegram_id: int,
    payment_type: str,
    details: str,
    ticket_numbers: str,
    amount: int,
    receipt_photo_id: str
) -> int:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("""
            INSERT INTO payments (telegram_id, payment_type, details, ticket_numbers, receipt_photo_id, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (telegram_id, payment_type, details, ticket_numbers, receipt_photo_id, amount, now))
        db.commit()
        return cur.lastrowid

async def create_payment(
    telegram_id: int,
    payment_type: str,
    details: str,
    ticket_numbers: str,
    amount: int,
    receipt_photo_id: str
) -> int:
    return await asyncio.to_thread(
        _sync_create_payment,
        telegram_id,
        payment_type,
        details,
        ticket_numbers,
        amount,
        receipt_photo_id
    )

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
        ptype = p["payment_type"] or "vip_90"

        u_cur = db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        u = u_cur.fetchone()

        opened_desc = ""

        # 1. 3 ta tanlangan bilet (5 000 so'm, 90 kun)
        if ptype == "tickets_3":
            raw_nums = p["ticket_numbers"] or ""
            t_nums = [int(n.strip()) for n in raw_nums.split(",") if n.strip().isdigit()]
            exp = (now + timedelta(days=90)).isoformat()
            for t_num in t_nums:
                db.execute("""
                    INSERT OR REPLACE INTO unlocked_tickets (telegram_id, ticket_number, expires_at, created_at)
                    VALUES (?, ?, ?, ?)
                """, (telegram_id, t_num, exp, now.isoformat()))
            opened_desc = f"Tanlangan biletlar: {', '.join(str(x) for x in t_nums)} (90 kunga)"

        # 2. 1 martalik imtihon (2 000 so'm)
        elif ptype == "exam_1":
            db.execute("UPDATE users SET exam_attempts = COALESCE(exam_attempts, 0) + 1 WHERE telegram_id = ?", (telegram_id,))
            opened_desc = "1 martalik 20 talik Imtihon topshirish ruxsati"

        # 3. 30 kunlik cheksiz imtihon (15 000 so'm)
        elif ptype == "exam_30":
            start_date = now
            if u and u["exam_pass_until"] and _is_active(u["exam_pass_until"]):
                start_date = datetime.fromisoformat(u["exam_pass_until"])
            new_exp = (start_date + timedelta(days=30)).isoformat()
            db.execute("UPDATE users SET exam_pass_until = ? WHERE telegram_id = ?", (new_exp, telegram_id))
            opened_desc = f"30 kunlik cheksiz Imtihon ruxsati ({new_exp[:10]} gacha)"

        # 4. VIP 90 kunlik to'liq kirish (30 000 so'm)
        elif ptype == "vip_90":
            start_date = now
            if u and u["vip_until"] and _is_active(u["vip_until"]):
                start_date = datetime.fromisoformat(u["vip_until"])
            new_vip = (start_date + timedelta(days=90)).isoformat()
            db.execute("UPDATE users SET vip_until = ? WHERE telegram_id = ?", (new_vip, telegram_id))
            opened_desc = f"VIP 90 kunlik to'liq kirish (barcha {TOTAL_TICKETS} ta bilet va cheksiz imtihon)"

        db.execute("UPDATE payments SET status = 'approved' WHERE id = ?", (payment_id,))
        db.commit()

        return {
            "telegram_id": telegram_id,
            "payment_type": ptype,
            "opened_desc": opened_desc,
            "amount": p["amount"]
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
        now_str = datetime.now().isoformat()
        vip_users = db.execute("SELECT COUNT(*) FROM users WHERE vip_until > ?", (now_str,)).fetchone()[0]
        exam_pass_users = db.execute("SELECT COUNT(*) FROM users WHERE exam_pass_until > ?", (now_str,)).fetchone()[0]
        total_tests = db.execute("SELECT COUNT(*) FROM test_results").fetchone()[0]
        pending_payments = db.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'").fetchone()[0]
        total_earned = db.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'").fetchone()[0]
        return {
            "total_users": total_users,
            "vip_users": vip_users,
            "exam_pass_users": exam_pass_users,
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
