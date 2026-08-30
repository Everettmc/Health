import logging
from contextlib import asynccontextmanager
from datetime import date
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    add_activity,
    create_checklist,
    create_contact,
    create_template,
    delete_checklist,
    delete_contact,
    delete_template,
    get_checklist,
    get_contact,
    get_follow_ups,
    get_news,
    init_db,
    list_activities,
    list_checklists,
    list_contacts,
    list_templates,
    update_checklist,
    update_contact,
)
from news import fetch_all_feeds, refresh_if_stale

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        await refresh_if_stale()
    except Exception as e:
        logger.warning(f"Initial news refresh failed: {e}")
    yield


app = FastAPI(title="Real Estate Daily Brief API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ──────────────────────────────────────────────────────────────────


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    items: List[str]


class ChecklistCreate(BaseModel):
    template_id: Optional[str] = None
    title: str
    event_date: Optional[str] = None
    contact_id: Optional[int] = None
    items: Optional[List[str]] = None


class ChecklistItem(BaseModel):
    text: str
    done: bool


class ChecklistUpdate(BaseModel):
    items: Optional[List[ChecklistItem]] = None
    status: Optional[str] = None
    title: Optional[str] = None


class ContactCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    type: str = "lead"
    status: str = "new"
    address: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None
    last_contact_date: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None
    last_contact_date: Optional[str] = None


class ActivityCreate(BaseModel):
    activity_type: str
    notes: Optional[str] = None


# ── Health ───────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ── Checklist templates ──────────────────────────────────────────────────────


@app.get("/api/checklist-templates")
async def get_templates() -> List[Dict]:
    return await list_templates()


@app.post("/api/checklist-templates")
async def add_template(template: TemplateCreate) -> Dict:
    return await create_template(template.name, template.description, template.icon, template.items)


@app.delete("/api/checklist-templates/{template_id}")
async def remove_template(template_id: str):
    deleted = await delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found or is a default template")
    return {"status": "deleted"}


# ── Checklists ────────────────────────────────────────────────────────────────


@app.get("/api/checklists")
async def get_checklists(status: Optional[str] = None, days: int = 30) -> List[Dict]:
    return await list_checklists(status=status, days=days)


@app.post("/api/checklists")
async def start_checklist(payload: ChecklistCreate) -> Dict:
    template_name = payload.title
    items = payload.items or []

    if payload.template_id:
        templates = await list_templates()
        tpl = next((t for t in templates if t["id"] == payload.template_id), None)
        if not tpl:
            raise HTTPException(status_code=404, detail="Template not found")
        template_name = tpl["name"]
        items = tpl["items"]

    if not items:
        raise HTTPException(status_code=400, detail="Checklist must have at least one item")

    return await create_checklist(
        template_id=payload.template_id,
        template_name=template_name,
        title=payload.title,
        event_date=payload.event_date or str(date.today()),
        items=items,
        contact_id=payload.contact_id,
    )


@app.get("/api/checklists/{checklist_id}")
async def get_one_checklist(checklist_id: int) -> Dict:
    checklist = await get_checklist(checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return checklist


@app.patch("/api/checklists/{checklist_id}")
async def patch_checklist(checklist_id: int, payload: ChecklistUpdate) -> Dict:
    items = [item.model_dump() for item in payload.items] if payload.items is not None else None
    updated = await update_checklist(checklist_id, items=items, status=payload.status, title=payload.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return updated


@app.delete("/api/checklists/{checklist_id}")
async def remove_checklist(checklist_id: int):
    deleted = await delete_checklist(checklist_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return {"status": "deleted"}


# ── Contacts ──────────────────────────────────────────────────────────────────


@app.get("/api/contacts")
async def get_contacts(status: Optional[str] = None, type: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
    return await list_contacts(status=status, contact_type=type, search=search)


@app.post("/api/contacts")
async def add_contact(contact: ContactCreate) -> Dict:
    return await create_contact(contact.model_dump())


@app.get("/api/contacts/follow-ups")
async def follow_ups() -> List[Dict]:
    return await get_follow_ups()


@app.get("/api/contacts/{contact_id}")
async def get_one_contact(contact_id: int) -> Dict:
    contact = await get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.patch("/api/contacts/{contact_id}")
async def patch_contact(contact_id: int, contact: ContactUpdate) -> Dict:
    updated = await update_contact(contact_id, contact.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated


@app.delete("/api/contacts/{contact_id}")
async def remove_contact(contact_id: int):
    deleted = await delete_contact(contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"status": "deleted"}


@app.get("/api/contacts/{contact_id}/activities")
async def get_activities(contact_id: int) -> List[Dict]:
    return await list_activities(contact_id)


@app.post("/api/contacts/{contact_id}/activities")
async def add_contact_activity(contact_id: int, activity: ActivityCreate) -> Dict:
    contact = await get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return await add_activity(contact_id, activity.activity_type, activity.notes)


# ── News ──────────────────────────────────────────────────────────────────────


@app.get("/api/news")
async def get_news_feed(limit: int = 30) -> List[Dict]:
    await refresh_if_stale()
    return await get_news(limit=limit)


@app.post("/api/news/refresh")
async def refresh_news():
    count = await fetch_all_feeds()
    return {"status": "refreshed", "items_fetched": count}


# ── Daily brief ───────────────────────────────────────────────────────────────


@app.get("/api/brief")
async def daily_brief() -> Dict[str, Any]:
    active_checklists = await list_checklists(status="active")
    today_str = str(date.today())
    todays_checklists = [c for c in active_checklists if c["event_date"] == today_str]

    due_follow_ups = await get_follow_ups()
    overdue = [c for c in due_follow_ups if c["follow_up_date"] < today_str]
    due_today = [c for c in due_follow_ups if c["follow_up_date"] == today_str]

    await refresh_if_stale()
    news = await get_news(limit=6)

    return {
        "date": today_str,
        "todays_checklists": todays_checklists,
        "active_checklist_count": len(active_checklists),
        "follow_ups_due_today": due_today,
        "follow_ups_overdue": overdue,
        "news": news,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
