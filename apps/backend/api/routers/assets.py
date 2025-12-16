"""Assets endpoints (branding/logo)."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.app_asset import AppAsset


router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("/logo")
async def get_logo(db: Session = Depends(get_db)):
    """Return AXDATA product logo stored in DB."""
    asset = db.query(AppAsset).filter(AppAsset.key == "logo").first()
    if not asset:
        raise HTTPException(status_code=404, detail="Logo not found")
    return Response(content=asset.data, media_type=asset.content_type, headers={"Cache-Control": "public, max-age=3600"})

