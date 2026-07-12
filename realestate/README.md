# Curb — Real Estate Daily Brief

A daily brief app for real estate agents: checklists for showings, listing
appointments, open houses, and closings; a lightweight contact/lead CRM with
follow-up tracking; and an industry news feed, all in one dashboard.

## Stack

- **Backend**: FastAPI + SQLite (`aiosqlite`), no auth (single-user, local tool)
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **News**: pulled from public real estate RSS feeds (Inman, HousingWire, RISMedia) — no API key required

## Running locally

### Backend

```bash
cd realestate/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd realestate/frontend
npm install
npm run dev
```

Then open http://localhost:5174. The Vite dev server proxies `/api` requests
to the backend on port 8001.

## Features

- **Daily Brief** — today's checklists, contacts due for follow-up, and top
  news headlines in one view.
- **Checklists** — five built-in templates (Home Showing, New Buyer
  Consultation, Listing Appointment, Open House, Closing Day / Final
  Walkthrough), each with a real-world 10-step list. Start a checklist for a
  specific date, optionally link it to a contact, and check off items as you go.
- **Contacts** — track buyers, sellers, leads, past clients, and vendors with
  status, follow-up dates, and a per-contact activity log (calls, texts,
  emails, showings, meetings, notes).
- **News** — real estate industry headlines, refreshed automatically every 30
  minutes (or on demand).
