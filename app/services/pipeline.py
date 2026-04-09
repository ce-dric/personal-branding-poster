from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import PosterResult
from app.services.hashtag_generator import HashtagGenerator
from app.services.poster_generator import PosterGenerator
from app.services.resume_parser import ResumeParser


class BrandingPipeline:
    """Coordinates validation, resume parsing, and poster generation."""

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    PDF_EXTENSIONS = {".pdf"}

    def __init__(
        self,
        resume_parser: ResumeParser | None = None,
        poster_generator: PosterGenerator | None = None,
        hashtag_generator: HashtagGenerator | None = None,
    ) -> None:
        self.resume_parser = resume_parser or ResumeParser()
        self.hashtag_generator = hashtag_generator or HashtagGenerator()
        self.poster_generator = poster_generator or PosterGenerator(
            hashtag_generator=self.hashtag_generator
        )

    def run(
        self,
        image_path: str | Path,
        resume_path: str | Path,
        output_dir: str | Path = "output",
    ) -> PosterResult:
        image = Path(image_path)
        resume = Path(resume_path)
        self.validate_image_file(image)
        self.validate_pdf_file(resume)
        image = image.resolve()
        resume = resume.resolve()

        resume_data = self.resume_parser.parse(resume)
        resume_data.summary = self.hashtag_generator.generate_summary(resume_data)

        result = self.poster_generator.generate(image, resume_data, output_dir=output_dir)
        metadata = result.metadata.model_copy(
            update={
                "input_files": {"photo": str(image), "resume_pdf": str(resume)},
            }
        )
        result.metadata_path.write_text(
            json.dumps(metadata.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return result.model_copy(update={"metadata": metadata})

    def validate_image_file(self, image_path: Path) -> None:
        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_path}")
        if image_path.suffix.lower() not in self.IMAGE_EXTENSIONS:
            raise ValueError("Image file must be one of: .jpg, .jpeg, .png")

    def validate_pdf_file(self, pdf_path: Path) -> None:
        if not pdf_path.exists():
            raise ValueError(f"PDF file not found: {pdf_path}")
        if pdf_path.suffix.lower() not in self.PDF_EXTENSIONS:
            raise ValueError("Resume file must be a PDF.")
