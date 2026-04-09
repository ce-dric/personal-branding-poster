from __future__ import annotations

import re
from collections import Counter

from app.models.schemas import ResumeData


STOPWORDS = {
    "and",
    "the",
    "with",
    "for",
    "from",
    "using",
    "over",
    "into",
    "that",
    "have",
    "has",
    "will",
    "your",
    "you",
    "this",
    "about",
    "대한",
    "및",
    "에서",
    "으로",
    "하는",
    "있습니다",
    "경력",
    "프로젝트",
    "업무",
    "이력서",
    "성명",
    "영문성명",
    "이름",
    "직무",
    "직책",
    "소속",
    "회사",
    "name",
    "title",
    "position",
    "생년월일",
    "핸드폰",
    "이메일",
    "주소",
    "주",
    "소",
    "학력",
    "사항",
    "구분",
    "입학연월",
    "졸업연월",
    "학교명",
    "전공",
    "소재지",
    "대학교",
    "대학원",
    "gmail",
    "gmailcom",
    "com",
    "email",
}


class HashtagGenerator:
    """Rule-based summary and hashtag generation."""

    def generate_summary(self, resume: ResumeData) -> str:
        specialties = ", ".join(self._english_tokens(resume.specialties)[:3]) or "AI and computer vision"
        organization = f" at {resume.organization}" if resume.organization else ""
        return f"{resume.title}{organization} focused on {specialties}."

    def generate_hashtags(self, resume: ResumeData, limit: int = 8) -> list[str]:
        candidates: list[str] = []

        source_values = [
            resume.title,
            resume.organization or "",
            *resume.specialties,
            *resume.keywords,
        ]
        for value in source_values:
            candidates.extend(self._tokenize(value))

        counter = Counter(token for token in candidates if token)
        hashtags: list[str] = []
        for token, _ in counter.most_common(limit * 2):
            formatted = self._to_hashtag(token)
            if formatted and formatted not in hashtags:
                hashtags.append(formatted)
            if len(hashtags) >= limit:
                break

        if len(hashtags) < 5:
            fallback = ["#AI", "#ComputerVision", "#Research", "#MachineLearning", "#DeepLearning"]
            for tag in fallback:
                if tag not in hashtags:
                    hashtags.append(tag)
                if len(hashtags) >= max(limit, 5):
                    break

        return hashtags[:limit]

    def _tokenize(self, text: str) -> list[str]:
        normalized = re.sub(r"[^0-9A-Za-z#+.-]+", " ", text)
        return [
            token.strip()
            for token in normalized.split()
            if len(token.strip()) > 1
            and token.lower() not in STOPWORDS
            and re.search(r"[A-Za-z]", token)
            and "@" not in token
            and "." not in token
            and token.lower() not in {"song", "changwoo", "professional", "personalbrand", "profile"}
        ]

    def _to_hashtag(self, token: str) -> str:
        cleaned = re.sub(r"[^0-9A-Za-z]+", "", token)
        if not cleaned:
            return ""
        if cleaned.isupper() and len(cleaned) <= 5:
            return f"#{cleaned}"
        parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+", cleaned)
        if parts:
            return "#" + "".join(part.capitalize() for part in parts)
        return f"#{cleaned.capitalize()}"

    def _english_tokens(self, values: list[str]) -> list[str]:
        results: list[str] = []
        for value in values:
            if re.search(r"[A-Za-z]", value):
                results.append(value)
        return results
