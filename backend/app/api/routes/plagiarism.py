from datetime import datetime
from typing import Optional
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import EmailStr
import razorpay
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
from app.models.enums import MemberStatus, PaymentStatus, PlagiarismStatus
from app.models.plagiarism import PlagiarismJob
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.plagiarism import (
    PaymentDetailsOut,
    PaymentReferenceCreate,
    PaymentUpdate,
    PlagiarismJobOut,
    PublicPlagiarismJobOut,
    PublicPlagiarismStatusOut,
    RazorpayOrderOut,
    RazorpayVerifyIn,
)
from app.utils.files import save_upload_file, validate_upload_file


router = APIRouter(tags=["plagiarism"])


def _ensure_project_access(db: Session, project: Project, user: User) -> None:
    if user.role.value == "faculty":
        return
    is_member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
            ProjectMember.status == MemberStatus.active,
        )
        .first()
        is not None
    )
    if project.owner_id != user.id and not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


def _ensure_public_plagiarism_enabled() -> None:
    if not settings.public_plagiarism_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public plagiarism checks are disabled. Please log in.",
        )


def _build_upi_uri(job: PlagiarismJob) -> str:
    amount = f"{job.amount_cents / 100:.2f}"
    params = {
        "pa": settings.payment_upi_vpa,
        "pn": settings.payment_upi_payee_name,
        "am": amount,
        "cu": job.currency,
        "tn": f"AcadFlow plagiarism job {job.id}",
    }
    return f"upi://pay?{urlencode(params)}"


def _get_razorpay_client() -> razorpay.Client:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay is not configured",
        )
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


@router.post(
    "/projects/{project_id}/plagiarism/jobs",
    response_model=PlagiarismJobOut,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlagiarismJob:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)

    validate_upload_file(file)
    storage_dir = f"{settings.storage_dir}/plagiarism"
    file_path, original_filename = save_upload_file(file, storage_dir, f"plagiarism-{project_id}")

    job = PlagiarismJob(
        project_id=project_id,
        submitted_by_id=current_user.id,
        requester_email=current_user.email,
        requester_name=current_user.full_name,
        status=PlagiarismStatus.queued,
        eta_hours=6,
        file_path=file_path,
        original_filename=original_filename,
        payment_status=PaymentStatus.pending,
        amount_cents=settings.plagiarism_base_fee_cents,
        currency=settings.plagiarism_currency,
        is_public=False,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/plagiarism/jobs", response_model=list[PlagiarismJobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlagiarismJob]:
    if current_user.role.value == "faculty":
        return db.query(PlagiarismJob).order_by(PlagiarismJob.created_at.desc()).all()
    jobs = (
        db.query(PlagiarismJob)
        .join(Project, Project.id == PlagiarismJob.project_id)
        .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(
            or_(
                PlagiarismJob.submitted_by_id == current_user.id,
                Project.owner_id == current_user.id,
                ProjectMember.user_id == current_user.id,
            )
        )
        .order_by(PlagiarismJob.created_at.desc())
        .all()
    )
    return jobs


@router.post("/plagiarism/public-jobs", response_model=PublicPlagiarismJobOut, status_code=status.HTTP_201_CREATED)
def create_public_job(
    requester_email: EmailStr = Form(...),
    requester_name: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> PublicPlagiarismJobOut:
    _ensure_public_plagiarism_enabled()
    validate_upload_file(file)
    storage_dir = f"{settings.storage_dir}/plagiarism"
    file_path, original_filename = save_upload_file(file, storage_dir, "public-plagiarism")
    access_token = uuid4().hex
    job = PlagiarismJob(
        project_id=None,
        submitted_by_id=None,
        requester_email=requester_email,
        requester_name=requester_name,
        public_access_token=access_token,
        status=PlagiarismStatus.queued,
        eta_hours=6,
        file_path=file_path,
        original_filename=original_filename,
        payment_status=PaymentStatus.pending,
        amount_cents=settings.plagiarism_base_fee_cents,
        currency=settings.plagiarism_currency,
        is_public=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return PublicPlagiarismJobOut(
        id=job.id,
        access_token=access_token,
        status=job.status,
        eta_hours=job.eta_hours,
        amount_cents=job.amount_cents,
        currency=job.currency,
    )


@router.post(
    "/plagiarism/public-jobs/{job_id}/razorpay/order",
    response_model=RazorpayOrderOut,
)
def create_public_razorpay_order(
    job_id: int,
    access_token: str,
    db: Session = Depends(get_db),
) -> RazorpayOrderOut:
    _ensure_public_plagiarism_enabled()
    job = db.get(PlagiarismJob, job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.public_access_token != access_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid access token")
    if job.payment_status != PaymentStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already processed")
    client = _get_razorpay_client()
    order = client.order.create(
        {
            "amount": job.amount_cents,
            "currency": job.currency,
            "receipt": f"acadflow_public_{job.id}",
            "notes": {"job_id": str(job.id), "type": "public"},
        }
    )
    job.payment_provider = "razorpay"
    job.payment_method = "upi"
    job.payment_order_id = order["id"]
    db.commit()
    db.refresh(job)
    return RazorpayOrderOut(
        key_id=settings.razorpay_key_id,
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        job_id=job.id,
    )


@router.post(
    "/plagiarism/public-jobs/{job_id}/razorpay/verify",
    response_model=PublicPlagiarismStatusOut,
)
def verify_public_razorpay_payment(
    job_id: int,
    payload: RazorpayVerifyIn,
    access_token: str,
    db: Session = Depends(get_db),
) -> PlagiarismJob:
    _ensure_public_plagiarism_enabled()
    job = db.get(PlagiarismJob, job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.public_access_token != access_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid access token")
    if job.payment_status == PaymentStatus.paid:
        return job
    if not job.payment_order_id or payload.razorpay_order_id != job.payment_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment order")
    client = _get_razorpay_client()
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature") from exc
    job.payment_status = PaymentStatus.paid
    job.payment_provider = "razorpay"
    job.payment_order_id = payload.razorpay_order_id
    job.payment_payment_id = payload.razorpay_payment_id
    job.payment_signature = payload.razorpay_signature
    job.payment_submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@router.get("/plagiarism/public-jobs/{job_id}/payment-details", response_model=PaymentDetailsOut)
def get_public_payment_details(
    job_id: int,
    access_token: str,
    db: Session = Depends(get_db),
) -> PaymentDetailsOut:
    _ensure_public_plagiarism_enabled()
    job = db.get(PlagiarismJob, job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.public_access_token != access_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid access token")
    if not settings.payment_upi_vpa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UPI not configured")
    return PaymentDetailsOut(
        job_id=job.id,
        amount_cents=job.amount_cents,
        currency=job.currency,
        upi_vpa=settings.payment_upi_vpa,
        payee_name=settings.payment_upi_payee_name,
        upi_uri=_build_upi_uri(job),
    )


@router.post("/plagiarism/public-jobs/{job_id}/payment-reference", response_model=PublicPlagiarismStatusOut)
def submit_public_payment_reference(
    job_id: int,
    payload: PaymentReferenceCreate,
    access_token: str,
    db: Session = Depends(get_db),
) -> PlagiarismJob:
    _ensure_public_plagiarism_enabled()
    job = db.get(PlagiarismJob, job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.public_access_token != access_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid access token")
    if job.payment_status != PaymentStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already processed")
    job.payment_reference = payload.reference
    job.payment_method = payload.method or "upi"
    job.payment_submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@router.post("/plagiarism/jobs/{job_id}/razorpay/order", response_model=RazorpayOrderOut)
def create_razorpay_order(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RazorpayOrderOut:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.is_public:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use public payment endpoint")
    project = db.get(Project, job.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    if job.payment_status != PaymentStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already processed")
    client = _get_razorpay_client()
    order = client.order.create(
        {
            "amount": job.amount_cents,
            "currency": job.currency,
            "receipt": f"acadflow_project_{job.id}",
            "notes": {"job_id": str(job.id), "type": "project"},
        }
    )
    job.payment_provider = "razorpay"
    job.payment_method = "upi"
    job.payment_order_id = order["id"]
    db.commit()
    db.refresh(job)
    return RazorpayOrderOut(
        key_id=settings.razorpay_key_id,
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        job_id=job.id,
    )


@router.post("/plagiarism/jobs/{job_id}/razorpay/verify", response_model=PlagiarismJobOut)
def verify_razorpay_payment(
    job_id: int,
    payload: RazorpayVerifyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlagiarismJob:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.is_public:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use public payment endpoint")
    project = db.get(Project, job.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    if job.payment_status == PaymentStatus.paid:
        return job
    if not job.payment_order_id or payload.razorpay_order_id != job.payment_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment order")
    client = _get_razorpay_client()
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature") from exc
    job.payment_status = PaymentStatus.paid
    job.payment_provider = "razorpay"
    job.payment_order_id = payload.razorpay_order_id
    job.payment_payment_id = payload.razorpay_payment_id
    job.payment_signature = payload.razorpay_signature
    job.payment_submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@router.get("/plagiarism/public-jobs/{job_id}", response_model=PublicPlagiarismStatusOut)
def get_public_job_status(
    job_id: int,
    access_token: str,
    db: Session = Depends(get_db),
) -> PlagiarismJob:
    _ensure_public_plagiarism_enabled()
    job = db.get(PlagiarismJob, job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.public_access_token != access_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid access token")
    return job


@router.get("/plagiarism/public-jobs/{job_id}/report")
def download_public_report(
    job_id: int,
    access_token: str,
    db: Session = Depends(get_db),
):
    _ensure_public_plagiarism_enabled()
    job = db.get(PlagiarismJob, job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.public_access_token != access_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid access token")
    if job.payment_status == PaymentStatus.pending:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment required")
    if not job.report_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not available")
    return FileResponse(job.report_file_path, filename=job.report_filename)


@router.get("/plagiarism/jobs/{job_id}", response_model=PlagiarismJobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlagiarismJob:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.is_public:
        if current_user.role.value != "faculty":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return job
    project = db.get(Project, job.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    return job


@router.get("/plagiarism/jobs/{job_id}/payment-details", response_model=PaymentDetailsOut)
def get_payment_details(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentDetailsOut:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.is_public:
        if current_user.role.value != "faculty":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    else:
        project = db.get(Project, job.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        _ensure_project_access(db, project, current_user)
    if not settings.payment_upi_vpa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UPI not configured")
    return PaymentDetailsOut(
        job_id=job.id,
        amount_cents=job.amount_cents,
        currency=job.currency,
        upi_vpa=settings.payment_upi_vpa,
        payee_name=settings.payment_upi_payee_name,
        upi_uri=_build_upi_uri(job),
    )


@router.post("/plagiarism/jobs/{job_id}/payment-reference", response_model=PlagiarismJobOut)
def submit_payment_reference(
    job_id: int,
    payload: PaymentReferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlagiarismJob:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.is_public:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use public payment endpoint")
    project = db.get(Project, job.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    if job.payment_status != PaymentStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already processed")
    job.payment_reference = payload.reference
    job.payment_method = payload.method or "upi"
    job.payment_submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@router.post("/plagiarism/jobs/{job_id}/report", response_model=PlagiarismJobOut)
def upload_report(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["faculty"])),
) -> PlagiarismJob:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    validate_upload_file(file)
    storage_dir = f"{settings.storage_dir}/plagiarism-reports"
    file_path, original_filename = save_upload_file(file, storage_dir, f"report-{job_id}")
    job.report_file_path = file_path
    job.report_filename = original_filename
    job.status = PlagiarismStatus.completed
    job.completed_at = datetime.utcnow()
    job.reviewed_by_id = current_user.id
    db.commit()
    db.refresh(job)
    return job


@router.put("/plagiarism/jobs/{job_id}/payment", response_model=PlagiarismJobOut)
def update_payment_status(
    job_id: int,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["faculty"])),
) -> PlagiarismJob:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job.payment_status = payload.status
    db.commit()
    db.refresh(job)
    return job


@router.post("/plagiarism/razorpay/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.razorpay_webhook_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook not configured")
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")
    client = _get_razorpay_client()
    try:
        client.utility.verify_webhook_signature(body, signature, settings.razorpay_webhook_secret)
    except razorpay.errors.SignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature") from exc

    payload = await request.json()
    event = payload.get("event")
    if event != "payment.captured":
        return {"status": "ignored"}

    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")
    if not order_id:
        return {"status": "ignored"}

    job = db.query(PlagiarismJob).filter(PlagiarismJob.payment_order_id == order_id).first()
    if not job:
        return {"status": "ignored"}
    if job.payment_status != PaymentStatus.paid:
        job.payment_status = PaymentStatus.paid
        job.payment_provider = "razorpay"
        job.payment_payment_id = payment_id
        job.payment_submitted_at = datetime.utcnow()
        db.commit()
    return {"status": "ok"}


@router.get("/plagiarism/jobs/{job_id}/report")
def download_report(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.is_public:
        if current_user.role.value != "faculty":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        if job.payment_status == PaymentStatus.pending:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment required")
        if not job.report_file_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not available")
        return FileResponse(job.report_file_path, filename=job.report_filename)
    project = db.get(Project, job.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    if job.payment_status == PaymentStatus.pending:
        if current_user.role.value != "faculty" or current_user.id == job.submitted_by_id:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment required")
    if not job.report_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not available")
    return FileResponse(job.report_file_path, filename=job.report_filename)
