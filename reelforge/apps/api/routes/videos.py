from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.orchestrator.tasks import generate_script_task
from apps.db.session import get_db
from apps.db.models import Video

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])


@router.get("/")
async def list_videos():
    return {"videos": []}


@router.post("/")
async def create_video(payload: dict, db: Session = Depends(get_db)):
    """Enqueue a script generation task via Celery and persist a Video row.

    Payload keys (optional): `brand`, `niche`, `trend`, `title`.
    """
    brand = payload.get("brand", "AI ProfitLab")
    niche = payload.get("niche", "ai-tools")
    trend = payload.get("trend", "unspecified trend")
    title = payload.get("title")

    video = Video(title=title, brand=brand, niche=niche, status="queued")
    try:
        db.add(video)
        db.commit()
        db.refresh(video)
    except Exception:
        # DB may be unavailable in lightweight demo environments; ignore and continue
        db.rollback()

    # enqueue async task; requires Celery broker configured at runtime
    try:
        generate_script_task.delay(brand, niche, trend)
    except Exception:
        # If broker is unavailable, still return accepted to keep API resilient
        pass

    return {"status": "accepted", "video_id": getattr(video, "id", None)}
