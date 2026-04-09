from __future__ import annotations

import re
from pathlib import Path

import fitz

from app.models.schemas import ResumeData


class ResumeParsingError(Exception):
    """Raised when the resume cannot be parsed."""


class ResumeParser:
    """Extract structured information from a resume PDF."""

    LABEL_PATTERNS = {
        "name": [r"^성명\s*[:：]?\s*(.+)$", r"^이름\s*[:：]?\s*(.+)$", r"^name\s*[:：]?\s*(.+)$"],
        "english_name": [r"^영문성명\s*[:：]?\s*(.+)$", r"^english\s+name\s*[:：]?\s*(.+)$"],
        "title": [
            r"^직무\s*[:：]?\s*(.+)$",
            r"^희망직무\s*[:：]?\s*(.+)$",
            r"^직책\s*[:：]?\s*(.+)$",
            r"^title\s*[:：]?\s*(.+)$",
            r"^position\s*[:：]?\s*(.+)$",
        ],
        "organization": [r"^소속\s*[:：]?\s*(.+)$", r"^회사\s*[:：]?\s*(.+)$", r"^company\s*[:：]?\s*(.+)$"],
    }
    FIELD_LABEL_STOPWORDS = {"이력서", "성명", "영문성명", "이름", "name", "title", "position", "소속", "회사"}

    def parse(self, pdf_path: str | Path) -> ResumeData:
        path = Path(pdf_path)
        if not path.exists():
            raise ResumeParsingError(f"Resume file not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise ResumeParsingError("Resume file must be a PDF.")

        raw_text = self.extract_text(path)
        if not raw_text.strip():
            raise ResumeParsingError("No extractable text found in resume PDF.")

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        language = self._detect_language(raw_text)
        labeled = self._extract_labeled_values(lines)
        name = labeled.get("name") or labeled.get("english_name") or self._extract_name(lines)
        title = labeled.get("title") or self._extract_title(lines, name)
        organization = labeled.get("organization") or self._extract_organization(lines)
        experience = self._extract_bullets(lines)
        specialties = self._extract_specialties(raw_text)
        keywords = self._extract_keywords(raw_text)

        return ResumeData(
            name=name,
            english_name=labeled.get("english_name"),
            title=title,
            organization=organization,
            experience=experience[:5],
            specialties=specialties[:6],
            keywords=keywords[:12],
            language=language,
            raw_text=raw_text,
            summary="",
        )

    def extract_text(self, pdf_path: Path) -> str:
        text_chunks: list[str] = []
        try:
            with fitz.open(pdf_path) as document:
                for page in document:
                    text_chunks.append(page.get_text("text"))
        except Exception as exc:  # pragma: no cover - library exceptions vary
            raise ResumeParsingError(f"Failed to read PDF: {exc}") from exc
        return "\n".join(text_chunks)

    def _detect_language(self, text: str) -> str:
        has_ko = bool(re.search(r"[가-힣]", text))
        has_en = bool(re.search(r"[A-Za-z]", text))
        if has_ko and has_en:
            return "mixed"
        if has_ko:
            return "ko"
        return "en"

    def _extract_name(self, lines: list[str]) -> str:
        for line in lines[:8]:
            if line in self.FIELD_LABEL_STOPWORDS:
                continue
            if self._looks_like_name(line):
                return line
        return lines[0][:60] if lines else "Unknown"

    def _extract_title(self, lines: list[str], name: str) -> str:
        for line in lines[:12]:
            if line == name:
                continue
            lower = line.lower()
            if any(keyword in lower for keyword in ["engineer", "designer", "manager", "lead", "director", "researcher", "developer", "consultant", "마케터", "개발자", "디자이너", "대표", "연구원"]):
                return line
        return "Professional"

    def _extract_organization(self, lines: list[str]) -> str | None:
        patterns = [
            re.compile(r"(?:at|@)\s+(.+)$", re.IGNORECASE),
            re.compile(r"(?:회사|소속)\s*[:：]?\s*(.+)$"),
        ]
        for line in lines[:20]:
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    return match.group(1).strip()
        return None

    def _extract_bullets(self, lines: list[str]) -> list[str]:
        bullets: list[str] = []
        for line in lines:
            if line.startswith(("-", "•", "▪")) or re.match(r"^\d+\.", line):
                bullets.append(line.lstrip("-•▪0123456789. ").strip())
        return bullets

    def _extract_specialties(self, text: str) -> list[str]:
        matches = re.findall(
            r"\b(?:AI|ML|LLM|NLP|CV|Computer Vision|Product|Growth|Strategy|Marketing|Branding|Frontend|Backend|Full[- ]?Stack|Leadership|Data|Automation)\b",
            text,
            flags=re.IGNORECASE,
        )
        normalized = []
        for match in matches:
            label = match.strip()
            if label.lower() == "computer vision":
                label = "Computer Vision"
            elif label.lower() == "full stack":
                label = "Full Stack"
            else:
                label = label.upper() if len(label) <= 3 else label.title()
            if label not in normalized:
                normalized.append(label)
        return normalized

    def _extract_keywords(self, text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z가-힣][A-Za-z가-힣0-9+#.-]{1,30}", text)
        blacklist = {"resume", "curriculum", "vitae", "experience", "education", "skills", "이력서", "성명", "영문성명", "이름", "학력", "경력", "자기소개"}
        keywords: list[str] = []
        for token in tokens:
            cleaned = token.strip(".,:;()[]{}")
            if cleaned.lower() in blacklist or len(cleaned) < 2:
                continue
            if cleaned in self.FIELD_LABEL_STOPWORDS:
                continue
            if "@" in cleaned or cleaned.isdigit():
                continue
            if re.search(r"\d{2,}", cleaned):
                continue
            if cleaned not in keywords:
                keywords.append(cleaned)
            if len(keywords) >= 20:
                break
        return keywords

    def _extract_labeled_values(self, lines: list[str]) -> dict[str, str]:
        values: dict[str, str] = {}
        for line in lines[:30]:
            for field, patterns in self.LABEL_PATTERNS.items():
                for pattern in patterns:
                    match = re.match(pattern, line, flags=re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value and value not in self.FIELD_LABEL_STOPWORDS:
                            values[field] = value
                            break
                if field in values:
                    break
        return values

    def _looks_like_name(self, line: str) -> bool:
        if len(line) > 40 or "@" in line or "http" in line.lower():
            return False
        if re.search(r"\d", line):
            return False
        if ":" in line or "：" in line:
            return False
        if line in self.FIELD_LABEL_STOPWORDS:
            return False
        return bool(re.fullmatch(r"[A-Za-z .'-]+|[가-힣]{2,8}", line))
