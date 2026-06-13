import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite

from bot.config import Config


class Database:
    def __init__(self, config: Config):
        self.path = config.database_path
        self.main_admin_id = config.main_admin_id

    async def connect(self) -> aiosqlite.Connection:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        return db

    async def init(self) -> None:
        async with await self.connect() as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    added_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    approved_by INTEGER,
                    transaction_id TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    admin_id INTEGER,
                    plan TEXT,
                    reject_reason TEXT,
                    created_at TEXT NOT NULL,
                    processed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS saved_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    added_by INTEGER NOT NULL,
                    added_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rejection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    admin_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            await db.execute(
                "INSERT OR IGNORE INTO admins (user_id, username, full_name, added_at) VALUES (?, ?, ?, ?)",
                (
                    self.main_admin_id,
                    None,
                    "Asosiy Admin",
                    datetime.utcnow().isoformat(),
                ),
            )
            await db.commit()

    async def ensure_user(
        self, user_id: int, username: str | None, full_name: str
    ) -> None:
        now = datetime.utcnow().isoformat()
        async with await self.connect() as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, full_name, created_at, last_active)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name,
                    last_active = excluded.last_active
                """,
                (user_id, username, full_name, now, now),
            )
            await db.commit()

    async def is_admin(self, user_id: int) -> bool:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT 1 FROM admins WHERE user_id = ?", (user_id,)
            )
            return await cur.fetchone() is not None

    async def get_admins(self) -> list[dict[str, Any]]:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT user_id, username, full_name, added_at FROM admins ORDER BY added_at"
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def add_admin(
        self, user_id: int, username: str | None, full_name: str
    ) -> bool:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT 1 FROM admins WHERE user_id = ?", (user_id,)
            )
            if await cur.fetchone():
                return False
            await db.execute(
                "INSERT INTO admins (user_id, username, full_name, added_at) VALUES (?, ?, ?, ?)",
                (user_id, username, full_name, datetime.utcnow().isoformat()),
            )
            await db.commit()
            return True

    async def remove_admin(self, user_id: int) -> bool:
        if user_id == self.main_admin_id:
            return False
        async with await self.connect() as db:
            cur = await db.execute(
                "DELETE FROM admins WHERE user_id = ?", (user_id,)
            )
            await db.commit()
            return cur.rowcount > 0

    async def create_payment(
        self, user_id: int, file_id: str
    ) -> tuple[str, int]:
        transaction_id = uuid.uuid4().hex
        now = datetime.utcnow().isoformat()
        async with await self.connect() as db:
            cur = await db.execute(
                """
                INSERT INTO payments (transaction_id, user_id, file_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (transaction_id, user_id, file_id, now),
            )
            await db.commit()
            return transaction_id, cur.lastrowid

    async def get_payment(self, transaction_id: str) -> dict[str, Any] | None:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT * FROM payments WHERE transaction_id = ?",
                (transaction_id,),
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def has_pending_payment(self, user_id: int) -> bool:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT 1 FROM payments WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            return await cur.fetchone() is not None

    async def approve_payment(
        self,
        transaction_id: str,
        admin_id: int,
        plan: str,
        days: int,
    ) -> dict[str, Any] | None:
        now = datetime.utcnow()
        expires = now + timedelta(days=days)
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT * FROM payments WHERE transaction_id = ? AND status = 'pending'",
                (transaction_id,),
            )
            payment = await cur.fetchone()
            if not payment:
                return None

            payment = dict(payment)
            await db.execute(
                """
                UPDATE payments
                SET status = 'approved', admin_id = ?, plan = ?, processed_at = ?
                WHERE transaction_id = ?
                """,
                (admin_id, plan, now.isoformat(), transaction_id),
            )
            await db.execute(
                """
                INSERT INTO subscriptions
                (user_id, plan, started_at, expires_at, approved_by, transaction_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
                """,
                (
                    payment["user_id"],
                    plan,
                    now.isoformat(),
                    expires.isoformat(),
                    admin_id,
                    transaction_id,
                ),
            )
            await db.commit()
            payment["plan"] = plan
            payment["expires_at"] = expires.isoformat()
            return payment

    async def reject_payment(
        self, transaction_id: str, admin_id: int, reason: str
    ) -> dict[str, Any] | None:
        now = datetime.utcnow().isoformat()
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT * FROM payments WHERE transaction_id = ? AND status = 'pending'",
                (transaction_id,),
            )
            payment = await cur.fetchone()
            if not payment:
                return None

            payment = dict(payment)
            await db.execute(
                """
                UPDATE payments
                SET status = 'rejected', admin_id = ?, reject_reason = ?, processed_at = ?
                WHERE transaction_id = ?
                """,
                (admin_id, reason, now, transaction_id),
            )
            await db.execute(
                """
                INSERT INTO rejection_history (user_id, admin_id, reason, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (payment["user_id"], admin_id, reason, now),
            )
            await db.commit()
            return payment

    async def get_active_subscription(self, user_id: int) -> dict[str, Any] | None:
        now = datetime.utcnow().isoformat()
        async with await self.connect() as db:
            cur = await db.execute(
                """
                SELECT * FROM subscriptions
                WHERE user_id = ? AND status = 'active' AND expires_at > ?
                ORDER BY expires_at DESC LIMIT 1
                """,
                (user_id, now),
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_expired_subscriptions(self) -> list[dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        async with await self.connect() as db:
            cur = await db.execute(
                """
                SELECT * FROM subscriptions
                WHERE status = 'active' AND expires_at <= ?
                """,
                (now,),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def expire_subscription(self, sub_id: int) -> None:
        async with await self.connect() as db:
            await db.execute(
                "UPDATE subscriptions SET status = 'expired' WHERE id = ?",
                (sub_id,),
            )
            await db.commit()

    async def add_saved_target(
        self, chat_id: int, title: str, target_type: str, added_by: int
    ) -> bool:
        async with await self.connect() as db:
            try:
                await db.execute(
                    """
                    INSERT INTO saved_targets (chat_id, title, type, added_by, added_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chat_id,
                        title,
                        target_type,
                        added_by,
                        datetime.utcnow().isoformat(),
                    ),
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_saved_targets(self) -> list[dict[str, Any]]:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT * FROM saved_targets ORDER BY title"
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_saved_target(self, target_id: int) -> dict[str, Any] | None:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT * FROM saved_targets WHERE id = ?", (target_id,)
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_stats(self) -> dict[str, int]:
        async with await self.connect() as db:
            stats = {}
            for key, query in {
                "users": "SELECT COUNT(*) FROM users",
                "active_subs": "SELECT COUNT(*) FROM subscriptions WHERE status='active'",
                "pending_payments": "SELECT COUNT(*) FROM payments WHERE status='pending'",
                "approved_payments": "SELECT COUNT(*) FROM payments WHERE status='approved'",
                "rejected_payments": "SELECT COUNT(*) FROM payments WHERE status='rejected'",
                "admins": "SELECT COUNT(*) FROM admins",
            }.items():
                cur = await db.execute(query)
                row = await cur.fetchone()
                stats[key] = row[0] if row else 0
            return stats

    async def get_users_page(self, offset: int = 0, limit: int = 10) -> list[dict]:
        async with await self.connect() as db:
            cur = await db.execute(
                """
                SELECT u.*,
                    (SELECT expires_at FROM subscriptions s
                     WHERE s.user_id = u.user_id AND s.status = 'active'
                     ORDER BY expires_at DESC LIMIT 1) as expires_at
                FROM users u
                ORDER BY u.last_active DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def count_users(self) -> int:
        async with await self.connect() as db:
            cur = await db.execute("SELECT COUNT(*) FROM users")
            row = await cur.fetchone()
            return row[0] if row else 0
