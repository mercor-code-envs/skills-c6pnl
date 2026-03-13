"""
Stateful session token management with automatic rotation.
"""
import secrets
import time


class SessionStore:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._store: dict = {}
        self._ttl = ttl_seconds

    def create(self, user_id: str, data: dict | None = None) -> str:
        """Create a new session, return the session token."""
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        self._store[token] = {
            "user_id": user_id,
            "data": data or {},
            "created_at": now,
            "last_used": now,
        }
        return token

    def get(self, token: str) -> dict | None:
        """Fetch session data. Returns None if not found or expired."""
        session = self._store.get(token)
        if session is None:
            return None
        now = int(time.time())
        if now - session["last_used"] > self._ttl:
            del self._store[token]
            return None
        session["last_used"] = now
        return session

    def rotate(self, old_token: str) -> str | None:
        """Invalidate old token and return a new one."""
        session = self.get(old_token)
        if session is None:
            return None
        del self._store[old_token]
        new_token = secrets.token_urlsafe(32)
        self._store[new_token] = {**session, "last_used": int(time.time())}
        return new_token

    def delete(self, token: str) -> None:
        """Delete (invalidate) a session."""
        self._store.pop(token, None)

    def active_count(self) -> int:
        return len(self._store)
