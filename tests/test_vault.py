"""Tests for the encrypted vault module."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from wayfi.vault.vault import Vault, VaultAuthError, VaultLockedError


class TestVaultInitialization:
    def test_initialize_creates_db(self, tmp_dir):
        db = tmp_dir / "vault.db"
        v = Vault(db_path=db)
        assert not v.is_initialized()
        v.initialize("mypass")
        assert v.is_initialized()
        assert db.exists()

    def test_double_initialize_raises(self, vault):
        with pytest.raises(Exception, match="already initialized"):
            vault.initialize("another-pass")

    def test_unlock_with_correct_passphrase(self, locked_vault):
        assert not locked_vault.is_unlocked()
        locked_vault.unlock("test-passphrase")
        assert locked_vault.is_unlocked()

    def test_unlock_with_wrong_passphrase(self, locked_vault):
        with pytest.raises(VaultAuthError):
            locked_vault.unlock("wrong-pass")

    def test_lock_clears_key(self, vault):
        assert vault.is_unlocked()
        vault.lock()
        assert not vault.is_unlocked()


class TestCredentialCRUD:
    def test_set_and_get(self, vault):
        vault.set_credential("email", "user@example.com")
        assert vault.get_credential("email") == "user@example.com"

    def test_get_nonexistent_returns_none(self, vault):
        assert vault.get_credential("nonexistent") is None

    def test_update_credential(self, vault):
        vault.set_credential("email", "old@example.com")
        vault.set_credential("email", "new@example.com")
        assert vault.get_credential("email") == "new@example.com"

    def test_delete_credential(self, vault):
        vault.set_credential("email", "user@example.com")
        assert vault.delete_credential("email") is True
        assert vault.get_credential("email") is None

    def test_delete_nonexistent_returns_false(self, vault):
        assert vault.delete_credential("nonexistent") is False

    def test_get_all(self, vault):
        vault.set_credential("email", "user@example.com")
        vault.set_credential("last_name", "Smith")
        creds = vault.get_all()
        assert len(creds) == 2
        names = {c.name for c in creds}
        assert names == {"email", "last_name"}

    def test_locked_vault_raises_on_crud(self, locked_vault):
        with pytest.raises(VaultLockedError):
            locked_vault.set_credential("email", "test")
        with pytest.raises(VaultLockedError):
            locked_vault.get_credential("email")


class TestRoomNumber:
    def test_set_and_get_room_number(self, vault):
        vault.set_room_number("1412", nights=3)
        assert vault.get_room_number() == "1412"

    def test_expired_room_number_returns_none(self, vault):
        vault.set_room_number("1412", nights=0)
        # Room with 0 nights should expire immediately
        # (expiry = now + 0 * 86400 = now, which is already past)
        time.sleep(0.1)
        assert vault.get_room_number() is None


class TestEncryptionRoundtrip:
    def test_different_vaults_same_passphrase(self, tmp_dir):
        """Data encrypted by one vault instance can be read by another."""
        db = tmp_dir / "shared.db"
        v1 = Vault(db_path=db)
        v1.initialize("shared-pass")
        v1.set_credential("secret", "the-value")
        v1.lock()

        v2 = Vault(db_path=db)
        v2.unlock("shared-pass")
        assert v2.get_credential("secret") == "the-value"
