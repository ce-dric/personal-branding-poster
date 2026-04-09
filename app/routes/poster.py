from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.pipeline import BrandingPipeline

router = APIRouter(prefix="/poster", tags=["poster"])
pipeline = BrandingPipeline()


@router.post("/generate")
async def generate_poster(
    photo: UploadFile = File(...),
    resume_pdf: UploadFile = File(...),
) -> dict[str, object]:
    try:
        with TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            photo_path = temp_dir / photo.filename
            pdf_path = temp_dir / resume_pdf.filename
            await _save_upload(photo, photo_path)
            await _save_upload(resume_pdf, pdf_path)

            result = pipeline.run(photo_path, pdf_path, output_dir="output")
            return {
                "poster_path": str(result.poster_path),
                "metadata_path": str(result.metadata_path),
                "metadata": result.metadata.model_dump(),
            }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    if not upload.filename:
        raise ValueError("Uploaded file must have a filename.")
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
