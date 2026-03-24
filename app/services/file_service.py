from fastapi import UploadFile, HTTPException
from pathlib import Path
import os
import uuid
from app.schemas.user_schema import SavedFile

class FileService:

    @staticmethod
    async def validate_file(file: UploadFile) -> None:
        threshold = 5 * 1024 * 1024

        if file.content_type != "application/pdf":
            raise HTTPException(status_code=422, detail="Only pdf files are allowed")

        content = await file.read()

        if not content:
            raise HTTPException(422, "Empty pdf file")

        if not content.startswith(b"%PDF"):
            raise HTTPException(422, "This file is not a valid pdf")

        await file.seek(0)

        if file.size > threshold:
            raise HTTPException(status_code=422, detail="The file exceeds 5 MB.")

    @staticmethod
    async def save_file(file: UploadFile, subdir: str | None = None) -> SavedFile:
        base_dir = Path(os.getenv("FILES_PATH", "app/storage/documents")).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename or "").suffix.lower() or ".pdf"
        filename = f"{uuid.uuid4()}{ext}"

        relative_dir = Path(subdir) if subdir else Path()
        target_dir = (base_dir / relative_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        relative_path = str((relative_dir / filename).as_posix())

        return SavedFile(
            filename=filename,
            relative_path=relative_path,
            size=len(content),
            mime_type=file.content_type,
        )