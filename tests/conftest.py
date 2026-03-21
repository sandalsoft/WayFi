"""Shared test fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from wayfi.vault.vault import Vault


@pytest.fixture
def tmp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def vault(tmp_dir):
    """Initialized and unlocked vault for testing."""
    db_path = tmp_dir / "test_vault.db"
    v = Vault(db_path=db_path)
    v.initialize("test-passphrase")
    return v


@pytest.fixture
def locked_vault(tmp_dir):
    """Initialized but locked vault."""
    db_path = tmp_dir / "test_vault.db"
    v = Vault(db_path=db_path)
    v.initialize("test-passphrase")
    v.lock()
    return v


@pytest.fixture
def portal_patterns_dir():
    """Path to the portal patterns directory."""
    return Path(__file__).parent.parent / "src" / "wayfi" / "portal" / "patterns"


@pytest.fixture
def mock_portals_dir():
    """Path to mock portal HTML fixtures."""
    return Path(__file__).parent / "mock_portal" / "portals"
