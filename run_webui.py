"""Start the WayFi web UI with vault configured.

Usage:
    uvicorn run_webui:app --host 0.0.0.0 --port 8080
"""
from pathlib import Path

from wayfi.vault.vault import Vault
from wayfi.webui.app import create_app

DB_PATH = Path.home() / ".wayfi" / "vault.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

vault = Vault(db_path=DB_PATH)
app = create_app(vault_instance=vault)
