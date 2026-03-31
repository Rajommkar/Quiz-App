# RankBridge PG Entrance Mock Tests and PYQs

A PG-exam-focused mock test platform built with Flask and MongoDB-style storage.

This project is designed for postgraduate entrance preparation in India and includes timed mock tests, PYQ-style papers, exam-wise access plans, student dashboards, analytics, and a cleaner product-style landing page inspired by major edtech platforms while staying strictly focused on PG exams only.

## Overview

RankBridge is not a generic quiz app. It is positioned as a focused test-series portal for exams such as:

- CAT
- XAT
- CMAT
- SNAP
- NMAT
- GMAT Focus
- GATE CSE
- GATE DA
- IIT JAM
- CUET PG
- GPAT
- CLAT PG

## Features

- PG-only exam catalog with separate exam detail pages
- PYQ-style papers and full mock tests for each exam
- Adaptive timer logic for demo/sample tests based on official exam patterns
- Question palette, mark-for-review, autosave, and timed submission flow
- Result and review pages with performance breakdown
- Exam-wise pricing plans plus all-access pass
- Student dashboard with purchases, attempts, and unlocked exams
- MongoDB-ready backend with automatic `mongomock` fallback for local demo use
- WhatsApp support CTA integrated into the UI

## Tech Stack

- Python
- Flask
- PyMongo
- Mongomock
- HTML / Jinja templates
- Bootstrap 5
- Custom CSS and JavaScript

## Project Structure

```text
QUIZ APP/
├── app.py
├── models.py
├── routes.py
├── requirements.txt
├── static/
│   ├── css/
│   └── js/
└── templates/
```

## Run Locally

1. Clone the repository

```bash
git clone <your-repo-url>
cd "QUIZ APP"
```

2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Start the app

```bash
python app.py
```

5. Open in browser

```text
http://127.0.0.1:5000
```

## Environment Variables

The app works without extra configuration because it falls back to `mongomock`, but you can set these if needed:

```env
SECRET_KEY=your-secret-key
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB_NAME=mockprep_india
WHATSAPP_NUMBER=919999999999
```

## Demo Login

- Email: `demo@mockprep.local`
- Password: `password123`

## Notes

- Seeded test content is representative demo content and can later be replaced with verified PYQs and production-grade question banks.
- The app automatically seeds exams, tests, plans, and a demo user on startup.
- If MongoDB is not available, the app still runs locally using `mongomock`.

## Why This Project Stands Out

- It solves a real product problem instead of being a simple CRUD project.
- The platform is domain-specific, which makes it stronger for portfolio use.
- It combines backend logic, data modeling, pricing flows, exam workflow UX, and frontend design in one project.

## Future Improvements

- Admin panel for uploading real PYQs and mocks
- Section-wise timing controls for exams that require them
- Payment gateway integration
- Better analytics and percentile estimation
- User authentication with password reset and email verification
- Responsive test-taking improvements for mobile users

## License

This project is for educational and portfolio use.
