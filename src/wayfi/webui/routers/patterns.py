"""Portal pattern management API routes."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["patterns"])

PATTERNS_DIR = Path(__file__).parent.parent.parent / "portal" / "patterns"


class PatternRequest(BaseModel):
    name: str
    vendor: str
    yaml_content: str


@router.get("/patterns")
async def list_patterns() -> dict:
    """List all portal patterns."""
    patterns = []
    if PATTERNS_DIR.exists():
        for f in sorted(PATTERNS_DIR.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text())
                patterns.append({
                    "filename": f.name,
                    "name": data.get("name", f.stem),
                    "vendor": data.get("vendor", "Unknown"),
                })
            except Exception:
                patterns.append({
                    "filename": f.name,
                    "name": f.stem,
                    "vendor": "Parse error",
                })
    return {"patterns": patterns}


@router.get("/patterns/{filename}")
async def get_pattern(filename: str) -> dict:
    """Get a pattern's full YAML content."""
    path = PATTERNS_DIR / filename
    if not path.exists() or not path.suffix == ".yaml":
        raise HTTPException(status_code=404, detail="Pattern not found")
    content = path.read_text()
    return {"filename": filename, "content": content}


@router.post("/patterns")
async def create_pattern(body: PatternRequest) -> dict:
    """Create a new custom portal pattern."""
    # Validate YAML
    try:
        yaml.safe_load(body.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    filename = f"{body.name}.yaml"
    path = PATTERNS_DIR / filename
    path.write_text(body.yaml_content)
    return {"status": "created", "filename": filename}


@router.put("/patterns/{filename}")
async def update_pattern(filename: str, body: PatternRequest) -> dict:
    """Update an existing portal pattern."""
    path = PATTERNS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Pattern not found")

    try:
        yaml.safe_load(body.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    path.write_text(body.yaml_content)
    return {"status": "updated", "filename": filename}


@router.delete("/patterns/{filename}")
async def delete_pattern(filename: str) -> dict:
    """Delete a portal pattern."""
    path = PATTERNS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Pattern not found")
    path.unlink()
    return {"status": "deleted", "filename": filename}
