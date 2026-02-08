from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
from app.models.enums import PlagiarismStatus
from app.models.plagiarism import PlagiarismJob
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.plagiarism import PlagiarismJobOut
from app.utils.files import save_upload_file


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

    storage_dir = f"{settings.storage_dir}/plagiarism"
    file_path, original_filename = save_upload_file(file, storage_dir, f"plagiarism-{project_id}")

    job = PlagiarismJob(
        project_id=project_id,
        submitted_by_id=current_user.id,
        status=PlagiarismStatus.queued,
        eta_hours=6,
        file_path=file_path,
        original_filename=original_filename,
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


@router.get("/plagiarism/jobs/{job_id}", response_model=PlagiarismJobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlagiarismJob:
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
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


@router.get("/plagiarism/jobs/{job_id}/report")
def download_report(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.get(PlagiarismJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    project = db.get(Project, job.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    if not job.report_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not available")
    return FileResponse(job.report_file_path, filename=job.report_filename)
