"""Tests for the FastAPI web UI."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wayfi.vault.vault import Vault
from wayfi.webui.app import create_app


@pytest.fixture
def client(tmp_dir):
    vault = Vault(db_path=tmp_dir / "test.db")
    app = create_app(vault_instance=vault)
    return TestClient(app)


@pytest.fixture
def client_with_vault(tmp_dir):
    vault = Vault(db_path=tmp_dir / "test.db")
    vault.initialize("testpass")
    app = create_app(vault_instance=vault)
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestStatusEndpoint:
    def test_status_no_orchestrator(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        assert resp.json()["state"] == "unknown"


class TestVaultEndpoints:
    def test_vault_status_uninitialized(self, client):
        resp = client.get("/api/vault/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["initialized"] is False

    def test_vault_initialize(self, client):
        resp = client.post("/api/vault/initialize", json={"passphrase": "mypass"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "initialized"

    def test_vault_double_initialize(self, client_with_vault):
        resp = client_with_vault.post(
            "/api/vault/initialize", json={"passphrase": "another"}
        )
        assert resp.status_code == 400

    def test_vault_unlock(self, client_with_vault):
        resp = client_with_vault.post(
            "/api/vault/unlock", json={"passphrase": "testpass"}
        )
        assert resp.status_code == 200

    def test_vault_unlock_wrong_pass(self, client_with_vault):
        resp = client_with_vault.post(
            "/api/vault/unlock", json={"passphrase": "wrong"}
        )
        assert resp.status_code == 401

    def test_credential_crud(self, client_with_vault):
        # Unlock first
        client_with_vault.post(
            "/api/vault/unlock", json={"passphrase": "testpass"}
        )

        # Create
        resp = client_with_vault.post(
            "/api/vault/credentials",
            json={"name": "email", "value": "test@example.com"},
        )
        assert resp.status_code == 200

        # Read
        resp = client_with_vault.get("/api/vault/credentials")
        assert resp.status_code == 200
        creds = resp.json()["credentials"]
        assert len(creds) == 1
        assert creds[0]["name"] == "email"

        # Delete
        resp = client_with_vault.delete("/api/vault/credentials/email")
        assert resp.status_code == 200

        # Verify deleted
        resp = client_with_vault.get("/api/vault/credentials")
        assert len(resp.json()["credentials"]) == 0

    def test_room_number(self, client_with_vault):
        client_with_vault.post(
            "/api/vault/unlock", json={"passphrase": "testpass"}
        )
        resp = client_with_vault.post(
            "/api/vault/room-number",
            json={"room_number": "1412", "nights": 3},
        )
        assert resp.status_code == 200

        resp = client_with_vault.get("/api/vault/room-number")
        assert resp.json()["room_number"] == "1412"


class TestPatternsEndpoint:
    def test_list_patterns(self, client):
        resp = client.get("/api/patterns")
        assert resp.status_code == 200
        patterns = resp.json()["patterns"]
        assert len(patterns) >= 11


class TestLogsEndpoint:
    def test_get_logs(self, client):
        resp = client.get("/api/logs")
        assert resp.status_code == 200
        assert "logs" in resp.json()
