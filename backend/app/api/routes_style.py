"""View/edit the caption style guide, and import real examples from this
account's own past Instagram posts."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.posting.style import CaptionStyle
from app.posting.style_import import StyleImportError, fetch_own_captions

router = APIRouter(prefix="/api/style", tags=["style"])


class StyleOut(BaseModel):
    tone_notes: str
    example_captions: list[str]


class StyleUpdateRequest(BaseModel):
    tone_notes: str
    example_captions: list[str]


class ImportResult(BaseModel):
    imported_count: int
    total_example_count: int


@router.get("", response_model=StyleOut)
def get_style() -> StyleOut:
    style = CaptionStyle.load(settings.caption_style_file)
    return StyleOut(tone_notes=style.tone_notes, example_captions=style.example_captions)


@router.put("", response_model=StyleOut)
def update_style(request: StyleUpdateRequest) -> StyleOut:
    style = CaptionStyle(tone_notes=request.tone_notes, example_captions=request.example_captions)
    style.save(settings.caption_style_file)
    return StyleOut(tone_notes=style.tone_notes, example_captions=style.example_captions)


@router.post("/import-from-instagram", response_model=ImportResult)
def import_from_instagram() -> ImportResult:
    """Pull this account's own past captions via the Graph API and merge
    them into the style guide's example captions."""
    try:
        imported = fetch_own_captions(
            settings.meta_access_token,
            settings.ig_business_account_id,
            graph_api_base_url=settings.graph_api_base_url,
        )
    except StyleImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    style = CaptionStyle.load(settings.caption_style_file)
    existing = set(style.example_captions)
    new_captions = [c for c in imported if c not in existing]
    style.example_captions = style.example_captions + new_captions
    style.save(settings.caption_style_file)

    return ImportResult(imported_count=len(new_captions), total_example_count=len(style.example_captions))
