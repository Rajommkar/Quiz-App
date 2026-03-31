# MockPrep India

A Flask-based PG exam mock test platform focused on Indian entrance exams such as CAT, XAT, CMAT, SNAP, NMAT, GMAT, GATE, IIT JAM, CUET PG, GPAT, and CLAT PG.

## Features

- MongoDB-ready backend using `pymongo`
- Automatic `mongomock` fallback when a real Mongo server is not configured
- Per-exam PYQ pass, mock pass, complete pass, and all-access pricing
- Timed test engine with question palette, mark for review, autosave, and post-test analytics
- WhatsApp support CTA

## Run locally

1. Install dependencies with `pip install -r requirements.txt`
2. Optional: set `MONGO_URI` for a real MongoDB instance
3. Run with `python app.py`
4. Open `http://127.0.0.1:5000`

## Demo account

- Email: `demo@mockprep.local`
- Password: `password123`

## Notes

- If `MONGO_URI` is unavailable, the app falls back to `mongomock` so the demo still works locally.
- Seeded question sets are representative exam-style content and can be replaced with verified PYQ imports later.
