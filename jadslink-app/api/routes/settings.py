from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import Settings
from .auth import require_admin

router = APIRouter(prefix="/api/settings", tags=["settings"])


class AlertSettings(BaseModel):
    alert_enabled:       str = "false"
    alert_email:         str = ""
    alert_threshold_min: str = "5"


@router.get("")
def get_settings(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    rows = db.query(Settings).all()
    return {r.key: r.value for r in rows}


@router.post("")
def update_settings(payload: AlertSettings, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    for k, v in payload.model_dump().items():
        row = db.query(Settings).filter(Settings.key == k).first()
        if row:
            row.value = v
        else:
            db.add(Settings(key=k, value=v))
    db.commit()
    return {"ok": True}
