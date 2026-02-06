from fastapi import UploadFile, HTTPException
from pathlib import Path
import os
import uuid
from app.schemas.user_schema import SavedFile

class FileService:
    
    @staticmethod
    async def validate_file(file: UploadFile) -> None:
        """Valida se o arquivo é um PDF válido e respeita o tamanho máximo"""
        threshold = 5 * 1024 * 1024  # 5 MB
        
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
    async def save_file(file: UploadFile) -> SavedFile:
        """Salva o arquivo no sistema de arquivos e retorna informações sobre o arquivo salvo"""
        base_dir = Path(os.getenv("FILES_PATH"))
        base_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename).suffix.lower()
        filename = f"{uuid.uuid4()}{ext}"

        file_path = base_dir / filename

        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        return SavedFile(
            filename=filename,
            size=len(content),
            mime_type=file.content_type,
            base_path=base_dir
        )
