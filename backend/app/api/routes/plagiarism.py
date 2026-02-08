from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
from app.models.enums import PaymentStatus, PlagiarismStatus
from app.models.plagiarism import PlagiarismJob
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.plagiarism import (
    PaymentUpdate,
    PlagiarismJobOut,
    PublicPlagiarismJobOut,
    PublicPlagiarismStatusOut,
)
from app.utils.files import save_upload_file, validate_upload_file


router = APIRouter(tags=["plagiarism"])


def _ensure_project_access(db: Session, project: Project, user: User) -> None:
    if user.role.value == "faculty":
        return
    is_member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id)
        .first()
        is not None
    )
    if project.owner_id != user.id and not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


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


@router.get("/plagiarism/public-jobs/{job_id}", response_model=PublicPlagiarismStatusOut)
def get_public_job_status(
    job_id: int,
    access_token: str,
    db: Session = Depends(get_db),
) -> PlagiarismJob:
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
    if current_user.role.value != "faculty" and job.payment_status == PaymentStatus.pending:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment required")
    if not job.report_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not available")
    return FileResponse(job.report_file_path, filename=job.report_filename)
