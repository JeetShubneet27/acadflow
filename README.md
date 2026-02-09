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
pip install -r requirements-dev.txt
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
- **faculty**: submit reviews when assigned and manage admin dashboard actions

## Plagiarism workflow

1. Author uploads a manuscript
2. Job is created with `queued` status (ETA = 6 hours)
3. Faculty performs external Turnitin review
4. Faculty uploads a report to mark job `completed`

### Authenticated plagiarism submissions

Plagiarism checks now require authentication. Users submit manuscripts from a
project workspace, and faculty upload the final report once the review is
complete. Pricing is stored per job and report access is gated on payment.

To re-enable public submissions, set `PUBLIC_PLAGIARISM_ENABLED=true` in the
backend environment.

### Payments (India)

- Razorpay integration for UPI/cards/netbanking
- Payment is verified automatically and report access is gated on payment
- Webhook: `POST /plagiarism/razorpay/webhook`

### Email verification (OTP)

AcadFlow requires OTP verification during signup only. Configure SMTP or Resend:

```
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=no-reply@acadflow.com
SMTP_USE_TLS=true
EMAIL_PROVIDER=smtp
RESEND_API_KEY=
```

Resend setup:

```
EMAIL_PROVIDER=resend
RESEND_API_KEY=your_resend_key
SMTP_FROM=verified@your-domain.com
```

### Faculty verification

- Faculty roles require official institutional email domains
- Public email providers (e.g. Gmail/Yahoo/Outlook) are blocked for faculty

## Workspace documents

AcadFlow includes a workspace for Word (DOC/DOCX) and LaTeX manuscripts:

- Word documents can be edited live or versioned by uploading new revisions.
- LaTeX documents are edited in a shared text workspace with version history and live co-editing.
- Workspace documents support locks to avoid conflicting edits.
- PDF previews for LaTeX/Word require server-side compilers (see below).

### LaTeX PDF preview

To enable PDF previews, install the `tectonic` binary in your backend runtime and set:

```
LATEX_PREVIEW_PROVIDER=tectonic
LATEX_PREVIEW_TIMEOUT_SECONDS=30
```

### Word PDF preview

Word previews require either HTML-to-PDF rendering or LibreOffice:

```
WORD_PREVIEW_PROVIDER=weasyprint
WORD_PREVIEW_TIMEOUT_SECONDS=30
```

Alternatively, set `WORD_PREVIEW_PROVIDER=libreoffice` and ensure the `soffice`
binary is available for DOCX-to-PDF conversion.

## Deployment

- Backend is designed for Render and PostgreSQL
- Frontend is designed for Vercel

## Tests

```bash
cd backend
pytest
```

## Migrations

Alembic is configured under `backend/alembic`.

For a new database:
```bash
cd backend
alembic upgrade head
```

If the database already exists, stamp the current revision before upgrading:
```bash
alembic stamp head
```
