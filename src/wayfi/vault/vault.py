"""AES-256-GCM encrypted credential store backed by SQLite."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

from argon2.low_level import Type as Argon2Type
from argon2.low_level import hash_secret_raw
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


DEFAULT_DB_PATH = Path("/var/lib/wayfi/vault.db")
KEY_CACHE_TTL = 86400  # 24 hours


@dataclass
class Credential:
    name: str
    value: str
    updated_at: float = 0.0


@dataclass
class VaultState:
    key: bytes | None = None
    key_created_at: float = 0.0
    salt: bytes = field(default_factory=lambda: b"")


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from passphrase using Argon2id."""
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Argon2Type.ID,
    )


def _encrypt(plaintext: str, key: bytes) -> bytes:
    """Encrypt plaintext with AES-256-GCM. Returns nonce + ciphertext + tag."""
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    return nonce + ciphertext + tag


def _decrypt(blob: bytes, key: bytes) -> str:
    """Decrypt AES-256-GCM blob (nonce + ciphertext + tag)."""
    nonce = blob[:12]
    tag = blob[-16:]
    ciphertext = blob[12:-16]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode("utf-8")


class Vault:
    """Encrypted credential store using AES-256-GCM + Argon2id + SQLite."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._state = VaultState()
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                name TEXT PRIMARY KEY,
                value BLOB NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _require_unlocked(self) -> bytes:
        if self._state.key is None:
            raise VaultLockedError("Vault is locked. Call unlock() first.")
        if time.time() - self._state.key_created_at > KEY_CACHE_TTL:
            self._state.key = None
            raise VaultLockedError("Key cache expired. Call unlock() again.")
        return self._state.key

    def is_unlocked(self) -> bool:
        if self._state.key is None:
            return False
        if time.time() - self._state.key_created_at > KEY_CACHE_TTL:
            self._state.key = None
            return False
        return True

    def is_initialized(self) -> bool:
        """Check if vault has been set up with a passphrase."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM meta WHERE key = 'salt'"
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def initialize(self, passphrase: str) -> None:
        """Set up the vault with an initial passphrase. Only call once."""
        if self.is_initialized():
            raise VaultError("Vault is already initialized.")
        salt = get_random_bytes(32)
        key = _derive_key(passphrase, salt)
        # Store salt and a verification token
        verification = _encrypt("wayfi-vault-ok", key)
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                ("salt", salt),
            )
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                ("verification", verification),
            )
            conn.commit()
        finally:
            conn.close()
        self._state.key = key
        self._state.key_created_at = time.time()
        self._state.salt = salt

    def unlock(self, passphrase: str) -> None:
        """Unlock the vault with passphrase. Caches derived key for 24h."""
        conn = self._get_conn()
        try:
            salt_row = conn.execute(
                "SELECT value FROM meta WHERE key = 'salt'"
            ).fetchone()
            verify_row = conn.execute(
                "SELECT value FROM meta WHERE key = 'verification'"
            ).fetchone()
        finally:
            conn.close()

        if salt_row is None:
            raise VaultError("Vault not initialized. Call initialize() first.")

        salt = salt_row[0]
        key = _derive_key(passphrase, salt)

        # Verify passphrase by trying to decrypt the verification token
        try:
            result = _decrypt(verify_row[0], key)
            if result != "wayfi-vault-ok":
                raise VaultAuthError("Bad passphrase.")
        except (ValueError, KeyError):
            raise VaultAuthError("Bad passphrase.")

        self._state.key = key
        self._state.key_created_at = time.time()
        self._state.salt = salt

    def lock(self) -> None:
        """Clear the cached key."""
        self._state.key = None
        self._state.key_created_at = 0.0

    def set_credential(self, name: str, value: str) -> None:
        """Store or update an encrypted credential."""
        key = self._require_unlocked()
        blob = _encrypt(value, key)
        now = time.time()
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO credentials (name, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (name, blob, now),
            )
            conn.commit()
        finally:
            conn.close()

    def get_credential(self, name: str) -> str | None:
        """Retrieve and decrypt a credential by name. Returns None if not found."""
        key = self._require_unlocked()
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM credentials WHERE name = ?", (name,)
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return _decrypt(row[0], key)

    def delete_credential(self, name: str) -> bool:
        """Delete a credential. Returns True if it existed."""
        self._require_unlocked()
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM credentials WHERE name = ?", (name,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_all(self) -> list[Credential]:
        """List all credential names and metadata (values decrypted)."""
        key = self._require_unlocked()
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT name, value, updated_at FROM credentials ORDER BY name"
            ).fetchall()
        finally:
            conn.close()
        results = []
        for name, blob, updated_at in rows:
            value = _decrypt(blob, key)
            results.append(Credential(name=name, value=value, updated_at=updated_at))
        return results

    def set_room_number(self, room_number: str, nights: int = 1) -> None:
        """Store room number with expiry based on stay duration."""
        key = self._require_unlocked()
        expiry = time.time() + (nights * 86400)
        payload = json.dumps({"room": room_number, "expiry": expiry})
        blob = _encrypt(payload, key)
        now = time.time()
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO credentials (name, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                ("room_number", blob, now),
            )
            conn.commit()
        finally:
            conn.close()

    def get_room_number(self) -> str | None:
        """Get room number if not expired. Returns None if missing or expired."""
        key = self._require_unlocked()
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM credentials WHERE name = 'room_number'"
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        payload = json.loads(_decrypt(row[0], key))
        if time.time() > payload["expiry"]:
            self.delete_credential("room_number")
            return None
        return payload["room"]


class VaultError(Exception):
    pass


class VaultLockedError(VaultError):
    pass


class VaultAuthError(VaultError):
    pass
