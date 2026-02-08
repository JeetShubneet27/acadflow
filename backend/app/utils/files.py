import os
from pathlib import Path
from typing import Tuple
from uuid import uuid4

from fastapi import UploadFile


def ensure_directory(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def save_upload_file(upload: UploadFile, storage_dir: str, prefix: str) -> Tuple[str, str]:
    ensure_directory(storage_dir)
    safe_name = f"{prefix}-{uuid4().hex}"
    file_path = Path(storage_dir) / safe_name
    with file_path.open("wb") as buffer:
        buffer.write(upload.file.read())
    return str(file_path), upload.filename
