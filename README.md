# AcadFlow

AcadFlow is a production-focused academic research workflow platform that
supports project collaboration, draft versioning, reviewer assignment, and
human-in-the-loop plagiarism checks.

## Architecture

- **Backend**: FastAPI + SQLAlchemy (SQLite for local dev, PostgreSQL in prod)
- **Frontend**: Next.js (App Router) + TypeScript + TailwindCSS
- **Auth**: JWT stored in `localStorage`

## Repository structure

```
/backend   FastAPI service
/frontend  Next.js app
```

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Environment variables (see `backend/.env.example`):

- `DATABASE_URL` defaults to SQLite
- `JWT_SECRET` must be changed in production
- `CORS_ORIGINS` should include the frontend URL in production
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` required for payments
- `RAZORPAY_WEBHOOK_SECRET` required for webhook verification

## Frontend setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Environment variables (see `frontend/.env.example`):

- `NEXT_PUBLIC_API_BASE_URL` should point to the FastAPI server

## Roles

- **student**: create projects, upload drafts, request plagiarism checks
- **reviewer**: submit reviews for assigned projects
- **faculty**: manage roles, assign reviewers, upload plagiarism reports

## Plagiarism workflow

1. Author uploads a manuscript
2. Job is created with `queued` status (ETA = 6 hours)
3. Faculty performs external Turnitin review
4. Faculty uploads a report to mark job `completed`

### Public plagiarism submissions

AcadFlow supports public (non-authenticated) plagiarism submissions. The system
issues a job ID and access token so the submitter can check status and download
the report later. Pricing is stored per job and faculty can update payment
status (pending/paid/waived) as needed.

### Payments (India)

- Razorpay integration for UPI/cards/netbanking
- Payment is verified automatically and report access is gated on payment

### Faculty verification

- Faculty roles require official institutional email domains
- Public email providers (e.g. Gmail/Yahoo/Outlook) are blocked for faculty

## Deployment

- Backend is designed for Render and PostgreSQL
- Frontend is designed for Vercel
