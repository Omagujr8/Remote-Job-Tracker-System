"""
Storage abstraction for job-application attachments.

Free-tier hosts (Render/Railway) typically use ephemeral disks — anything
written locally is wiped on redeploy or restart. So this module exposes one
interface with two implementations:

- LocalStorage: writes to disk, fine for local development.
- CloudinaryStorage: persists across redeploys, use in production.

Switch via the STORAGE_BACKEND env var. No router/model code needs to change.
"""
import os
import shutil
import uuid
from dataclasses import dataclass

from fastapi import UploadFile

from app.config import settings


@dataclass
class StoredFile:
    filepath: str  # what we persist in the DB (path or URL)
    storage_backend: str


class StorageError(Exception):
    pass


class LocalStorage:
    backend_name = "local"

    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def save(self, file: UploadFile, job_id: int) -> StoredFile:
        ext = os.path.splitext(file.filename or "")[1]
        unique_name = f"{job_id}_{uuid.uuid4().hex}{ext}"
        destination = os.path.join(self.upload_dir, unique_name)
        try:
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except OSError as exc:
            raise StorageError(f"Failed to save file locally: {exc}") from exc
        return StoredFile(filepath=destination, storage_backend=self.backend_name)

    def delete(self, filepath: str) -> None:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError:
            # Non-fatal: DB row deletion should still proceed.
            pass

    def url_for(self, filepath: str) -> str:
        # Served via the /attachments/{id}/download endpoint, not directly.
        return filepath


class CloudinaryStorage:
    backend_name = "cloudinary"

    def __init__(self):
        try:
            import cloudinary
            import cloudinary.uploader
        except ImportError as exc:
            raise StorageError(
                "cloudinary package not installed. Run: pip install cloudinary"
            ) from exc

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        self._cloudinary = cloudinary

    def save(self, file: UploadFile, job_id: int) -> StoredFile:
        try:
            result = self._cloudinary.uploader.upload(
                file.file,
                folder=f"m4-job-tracker/{job_id}",
                resource_type="auto",
            )
        except Exception as exc:  # cloudinary raises its own error types
            raise StorageError(f"Failed to upload to Cloudinary: {exc}") from exc
        return StoredFile(filepath=result["secure_url"], storage_backend=self.backend_name)

    def delete(self, filepath: str) -> None:
        # Best-effort; not critical path for the app to function.
        pass

    def url_for(self, filepath: str) -> str:
        return filepath


def get_storage():
    if settings.STORAGE_BACKEND == "cloudinary":
        return CloudinaryStorage()
    return LocalStorage(settings.LOCAL_UPLOAD_DIR)
