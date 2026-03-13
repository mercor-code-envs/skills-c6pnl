"""
Tests for SessionStore session management with token rotation.
"""
import pytest
from session_manager import SessionStore


class TestSessionCreate:
    def test_create_returns_token(self):
        store = SessionStore()
        token = store.create("user1")
        assert isinstance(token, str) and len(token) > 10

    def test_create_unique_tokens(self):
        store = SessionStore()
        t1 = store.create("user1")
        t2 = store.create("user2")
        assert t1 != t2

    def test_get_returns_session(self):
        store = SessionStore()
        token = store.create("user1", {"role": "admin"})
        session = store.get(token)
        assert session is not None
        assert session["user_id"] == "user1"
        assert session["data"]["role"] == "admin"


class TestSessionRotation:
    def test_rotate_invalidates_old_token(self):
        store = SessionStore()
        old = store.create("user1")
        new = store.rotate(old)
        assert store.get(old) is None

    def test_rotate_returns_new_valid_token(self):
        store = SessionStore()
        old = store.create("user1")
        new = store.rotate(old)
        session = store.get(new)
        assert session is not None
        assert session["user_id"] == "user1"

    def test_rotate_invalid_token_returns_none(self):
        store = SessionStore()
        assert store.rotate("nonexistent-token") is None


class TestSessionDelete:
    def test_delete_removes_session(self):
        store = SessionStore()
        token = store.create("user1")
        store.delete(token)
        assert store.get(token) is None

    def test_delete_nonexistent_is_safe(self):
        store = SessionStore()
        store.delete("does-not-exist")  # should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
