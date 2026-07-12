import json
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import aiosqlite

DB_PATH = os.getenv("DB_PATH", "realestate.db")

DEFAULT_TEMPLATES = [
    {
        "id": "home_showing",
        "name": "Home Showing",
        "description": "Walking a buyer through a property",
        "icon": "Home",
        "items": [
            "Confirm showing time with listing agent/seller",
            "Review property details, comps, and disclosures beforehand",
            "Bring business cards, lockbox key/code, and buyer questionnaire",
            "Arrive 10-15 min early to open up and turn on lights",
            "Walk through interior, exterior, and special features with buyer",
            "Note buyer's likes/dislikes and objections",
            "Ask buyer for feedback and gauge interest level",
            "Lock up, reset thermostat/lights, confirm alarm code",
            "Send follow-up message within 24 hours",
            "Log showing feedback in contact notes",
        ],
    },
    {
        "id": "buyer_consultation",
        "name": "New Buyer Consultation",
        "description": "First meeting with a new buyer client",
        "icon": "Users",
        "items": [
            "Send pre-meeting questionnaire / wants & needs list",
            "Confirm pre-approval or discuss lender referrals",
            "Prepare buyer representation agreement",
            "Review current market conditions and price ranges",
            "Explain the home buying process step by step",
            "Discuss budget, financing, and closing costs",
            "Set up MLS search / auto alerts for buyer",
            "Get signed buyer agreement",
            "Schedule first showings",
            "Add buyer to CRM with follow-up reminders",
        ],
    },
    {
        "id": "listing_appointment",
        "name": "Listing Appointment",
        "description": "Meeting with a seller to list their property",
        "icon": "ClipboardList",
        "items": [
            "Research comps and prepare CMA (Comparative Market Analysis)",
            "Review property history, tax records, and disclosures",
            "Prepare listing presentation / marketing plan",
            "Bring listing agreement and disclosure forms",
            "Tour the property and note repairs/staging needs",
            "Discuss pricing strategy with seller",
            "Explain marketing plan (photos, MLS, social, open houses)",
            "Review commission and contract terms",
            "Get listing agreement signed",
            "Schedule professional photos and measurements",
        ],
    },
    {
        "id": "open_house",
        "name": "Open House",
        "description": "Hosting an open house event",
        "icon": "DoorOpen",
        "items": [
            "Confirm date/time and get seller approval",
            "Post open house on MLS and social media",
            "Prepare sign-in sheet and business cards",
            "Stage key rooms, open blinds, turn on lights",
            "Set up directional signs and balloons",
            "Print flyers with property details and QR code",
            "Arrive 30 min early to prep",
            "Greet visitors and collect contact info",
            "Follow up with all visitors within 48 hours",
            "Report feedback and turnout to seller",
        ],
    },
    {
        "id": "closing_day",
        "name": "Closing Day / Final Walkthrough",
        "description": "Final steps before and at closing",
        "icon": "KeyRound",
        "items": [
            "Schedule final walkthrough 24-48 hrs before closing",
            "Confirm all repairs from inspection were completed",
            "Verify utilities are on for walkthrough",
            "Check closing disclosure figures with client",
            "Confirm closing time, location, and documents needed",
            "Remind client to bring ID and cashier's check/wire confirmation",
            "Do final walkthrough with buyer",
            "Attend closing / signing",
            "Hand over keys, garage remotes, warranties, manuals",
            "Send closing gift and request review/referral",
        ],
    },
]

FEEDS = [
    ("Inman", "https://www.inman.com/feed/"),
    ("HousingWire", "https://www.housingwire.com/feed/"),
    ("RISMedia", "https://www.rismedia.com/feed/"),
]


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS checklist_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                items TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT,
                template_name TEXT NOT NULL,
                title TEXT NOT NULL,
                contact_id INTEGER,
                event_date TEXT NOT NULL,
                items TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                type TEXT NOT NULL DEFAULT 'lead',
                status TEXT NOT NULL DEFAULT 'new',
                address TEXT,
                source TEXT,
                notes TEXT,
                follow_up_date TEXT,
                last_contact_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contact_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                source TEXT,
                summary TEXT,
                published_at TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_checklists_status ON checklists(status);
            CREATE INDEX IF NOT EXISTS idx_checklists_event_date ON checklists(event_date);
            CREATE INDEX IF NOT EXISTS idx_contacts_follow_up ON contacts(follow_up_date);
            CREATE INDEX IF NOT EXISTS idx_activities_contact ON contact_activities(contact_id);
            CREATE INDEX IF NOT EXISTS idx_news_published ON news_cache(published_at);
            """
        )
        await db.commit()
        await _seed_templates(db)


async def _seed_templates(db: aiosqlite.Connection):
    async with db.execute("SELECT COUNT(*) FROM checklist_templates") as cursor:
        row = await cursor.fetchone()
        count = row[0] if row else 0
    if count > 0:
        return
    for tpl in DEFAULT_TEMPLATES:
        await db.execute(
            """INSERT INTO checklist_templates (id, name, description, icon, items, is_default)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (tpl["id"], tpl["name"], tpl["description"], tpl["icon"], json.dumps(tpl["items"])),
        )
    await db.commit()


def _row_to_dict(row: aiosqlite.Row) -> Dict[str, Any]:
    return dict(row)


# ── Checklist templates ──────────────────────────────────────────────────────


async def list_templates() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM checklist_templates ORDER BY is_default DESC, created_at ASC") as cursor:
            rows = await cursor.fetchall()
            out = []
            for row in rows:
                d = _row_to_dict(row)
                d["items"] = json.loads(d["items"])
                out.append(d)
            return out


async def create_template(name: str, description: Optional[str], icon: Optional[str], items: List[str]) -> Dict:
    template_id = f"custom_{int(datetime.utcnow().timestamp() * 1000)}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO checklist_templates (id, name, description, icon, items, is_default)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (template_id, name, description, icon or "ListChecks", json.dumps(items)),
        )
        await db.commit()
    return {"id": template_id, "name": name, "description": description, "icon": icon or "ListChecks", "items": items, "is_default": 0}


async def delete_template(template_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM checklist_templates WHERE id = ? AND is_default = 0", (template_id,))
        await db.commit()
        return cursor.rowcount > 0


# ── Checklist instances ──────────────────────────────────────────────────────


async def create_checklist(template_id: Optional[str], template_name: str, title: str, event_date: str, items: List[str], contact_id: Optional[int]) -> Dict:
    item_objs = [{"text": text, "done": False} for text in items]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO checklists (template_id, template_name, title, contact_id, event_date, items, status)
               VALUES (?, ?, ?, ?, ?, ?, 'active')""",
            (template_id, template_name, title, contact_id, event_date, json.dumps(item_objs)),
        )
        await db.commit()
        checklist_id = cursor.lastrowid
    return await get_checklist(checklist_id)


async def list_checklists(status: Optional[str] = None, days: int = 30) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            query = "SELECT * FROM checklists WHERE status = ? ORDER BY event_date DESC, id DESC"
            params: tuple = (status,)
        else:
            query = "SELECT * FROM checklists ORDER BY event_date DESC, id DESC LIMIT ?"
            params = (days,)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            out = []
            for row in rows:
                d = _row_to_dict(row)
                d["items"] = json.loads(d["items"])
                out.append(d)
            return out


async def get_checklist(checklist_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM checklists WHERE id = ?", (checklist_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            d = _row_to_dict(row)
            d["items"] = json.loads(d["items"])
            return d


async def update_checklist(checklist_id: int, items: Optional[List[Dict]] = None, status: Optional[str] = None, title: Optional[str] = None) -> Optional[Dict]:
    existing = await get_checklist(checklist_id)
    if not existing:
        return None

    new_items = items if items is not None else existing["items"]
    new_status = status if status is not None else existing["status"]
    new_title = title if title is not None else existing["title"]
    completed_at = existing.get("completed_at")
    if new_status == "completed" and existing["status"] != "completed":
        completed_at = datetime.utcnow().isoformat()
    elif new_status != "completed":
        completed_at = None

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE checklists SET items = ?, status = ?, title = ?, completed_at = ? WHERE id = ?",
            (json.dumps(new_items), new_status, new_title, completed_at, checklist_id),
        )
        await db.commit()
    return await get_checklist(checklist_id)


async def delete_checklist(checklist_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM checklists WHERE id = ?", (checklist_id,))
        await db.commit()
        return cursor.rowcount > 0


# ── Contacts ──────────────────────────────────────────────────────────────────


async def create_contact(data: Dict[str, Any]) -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO contacts (name, phone, email, type, status, address, source, notes, follow_up_date, last_contact_date)
               VALUES (:name, :phone, :email, :type, :status, :address, :source, :notes, :follow_up_date, :last_contact_date)""",
            data,
        )
        await db.commit()
        contact_id = cursor.lastrowid
    return await get_contact(contact_id)


async def list_contacts(status: Optional[str] = None, contact_type: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
    query = "SELECT * FROM contacts WHERE 1=1"
    params: List[Any] = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if contact_type:
        query += " AND type = ?"
        params.append(contact_type)
    if search:
        query += " AND (name LIKE ? OR email LIKE ? OR phone LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])
    query += " ORDER BY updated_at DESC"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(row) for row in rows]


async def get_contact(contact_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)) as cursor:
            row = await cursor.fetchone()
            return _row_to_dict(row) if row else None


async def update_contact(contact_id: int, data: Dict[str, Any]) -> Optional[Dict]:
    existing = await get_contact(contact_id)
    if not existing:
        return None
    merged = {**existing, **{k: v for k, v in data.items() if v is not None}}
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE contacts SET name=:name, phone=:phone, email=:email, type=:type, status=:status,
               address=:address, source=:source, notes=:notes, follow_up_date=:follow_up_date,
               last_contact_date=:last_contact_date, updated_at=CURRENT_TIMESTAMP WHERE id=:id""",
            {**merged, "id": contact_id},
        )
        await db.commit()
    return await get_contact(contact_id)


async def delete_contact(contact_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_follow_ups(days_ahead: int = 0) -> List[Dict]:
    cutoff = str(date.today())
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM contacts WHERE follow_up_date IS NOT NULL AND follow_up_date <= ?
               AND status NOT IN ('closed', 'lost') ORDER BY follow_up_date ASC""",
            (cutoff,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(row) for row in rows]


# ── Contact activities ────────────────────────────────────────────────────────


async def add_activity(contact_id: int, activity_type: str, notes: Optional[str]) -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO contact_activities (contact_id, activity_type, notes) VALUES (?, ?, ?)",
            (contact_id, activity_type, notes),
        )
        await db.execute(
            "UPDATE contacts SET last_contact_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (str(date.today()), contact_id),
        )
        await db.commit()
        activity_id = cursor.lastrowid
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contact_activities WHERE id = ?", (activity_id,)) as c:
            row = await c.fetchone()
            return _row_to_dict(row)


async def list_activities(contact_id: int) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM contact_activities WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(row) for row in rows]


# ── News ──────────────────────────────────────────────────────────────────────


async def upsert_news_items(items: List[Dict[str, Any]]):
    if not items:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """INSERT OR IGNORE INTO news_cache (title, link, source, summary, published_at)
               VALUES (:title, :link, :source, :summary, :published_at)""",
            items,
        )
        await db.commit()


async def get_news(limit: int = 30) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM news_cache ORDER BY published_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(row) for row in rows]


async def get_latest_news_fetch_time() -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT MAX(fetched_at) FROM news_cache") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
