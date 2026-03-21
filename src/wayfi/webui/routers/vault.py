"""Vault credential management API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["vault"])


class UnlockRequest(BaseModel):
    passphrase: str


class InitializeRequest(BaseModel):
    passphrase: str


class CredentialRequest(BaseModel):
    name: str
    value: str


class RoomNumberRequest(BaseModel):
    room_number: str
    nights: int = 1


def _get_vault(request: Request):
    vault = request.app.state.vault
    if not vault:
        raise HTTPException(status_code=503, detail="Vault not configured")
    return vault


@router.post("/vault/initialize")
async def initialize_vault(body: InitializeRequest, request: Request) -> dict:
    """Initialize the vault with a passphrase (first-time setup)."""
    vault = _get_vault(request)
    if vault.is_initialized():
        raise HTTPException(status_code=400, detail="Vault already initialized")
    vault.initialize(body.passphrase)
    return {"status": "initialized"}


@router.post("/vault/unlock")
async def unlock_vault(body: UnlockRequest, request: Request) -> dict:
    """Unlock the vault with passphrase."""
    vault = _get_vault(request)
    try:
        vault.unlock(body.passphrase)
        return {"status": "unlocked"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/vault/lock")
async def lock_vault(request: Request) -> dict:
    """Lock the vault (clear cached key)."""
    vault = _get_vault(request)
    vault.lock()
    return {"status": "locked"}


@router.get("/vault/status")
async def vault_status(request: Request) -> dict:
    """Check vault lock status."""
    vault = _get_vault(request)
    return {
        "initialized": vault.is_initialized(),
        "unlocked": vault.is_unlocked(),
    }


@router.get("/vault/credentials")
async def list_credentials(request: Request) -> dict:
    """List all stored credentials."""
    vault = _get_vault(request)
    if not vault.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")
    creds = vault.get_all()
    return {
        "credentials": [
            {"name": c.name, "value": c.value, "updated_at": c.updated_at}
            for c in creds
        ]
    }


@router.post("/vault/credentials")
async def set_credential(body: CredentialRequest, request: Request) -> dict:
    """Store or update a credential."""
    vault = _get_vault(request)
    if not vault.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")
    vault.set_credential(body.name, body.value)
    return {"status": "saved", "name": body.name}


@router.delete("/vault/credentials/{name}")
async def delete_credential(name: str, request: Request) -> dict:
    """Delete a credential by name."""
    vault = _get_vault(request)
    if not vault.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")
    deleted = vault.delete_credential(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"status": "deleted", "name": name}


@router.post("/vault/room-number")
async def set_room_number(body: RoomNumberRequest, request: Request) -> dict:
    """Store room number with stay duration."""
    vault = _get_vault(request)
    if not vault.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")
    vault.set_room_number(body.room_number, body.nights)
    return {"status": "saved", "room_number": body.room_number, "nights": body.nights}


@router.get("/vault/room-number")
async def get_room_number(request: Request) -> dict:
    """Get current room number (if not expired)."""
    vault = _get_vault(request)
    if not vault.is_unlocked():
        raise HTTPException(status_code=403, detail="Vault is locked")
    room = vault.get_room_number()
    return {"room_number": room}
