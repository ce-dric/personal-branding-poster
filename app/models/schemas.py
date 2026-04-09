from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ResumeData(BaseModel):
    name: str = "Unknown"
    english_name: str | None = None
    title: str = "Professional"
    organization: str | None = None
    experience: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    summary: str = "Professional profile"
    language: Literal["ko", "en", "mixed"] = "mixed"
    raw_text: str = ""


class PosterMetadata(BaseModel):
    name: str
    title: str
    summary: str
    hashtags: list[str]
    input_files: dict[str, str]
    output_file: str


class PosterResult(BaseModel):
    poster_path: Path
    metadata_path: Path
    metadata: PosterMetadata
