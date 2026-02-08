from pathlib import Path
from shutil import copyfileobj
from typing import Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


def ensure_directory(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_upload_file(upload: UploadFile) -> None:
    filename = upload.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload PDF or DOCX.",
        )
    if upload.content_type and upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported content type. Upload PDF or DOCX.",
        )


def save_upload_file(upload: UploadFile, storage_dir: str, prefix: str) -> Tuple[str, str]:
    ensure_directory(storage_dir)
    safe_name = f"{prefix}-{uuid4().hex}"
    file_path = Path(storage_dir) / safe_name
    with file_path.open("wb") as buffer:
        copyfileobj(upload.file, buffer)
    return str(file_path), upload.filename
