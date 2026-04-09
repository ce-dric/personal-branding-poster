from app.models.schemas import ResumeData
from app.services.hashtag_generator import HashtagGenerator


def test_hashtag_generator_creates_minimum_hashtags() -> None:
    generator = HashtagGenerator()
    resume = ResumeData(
        name="Jane Doe",
        title="AI Product Lead",
        organization="Open Future Labs",
        specialties=["AI", "Product", "Automation"],
        keywords=["LLM", "Startup", "Growth"],
        summary="",
    )

    hashtags = generator.generate_hashtags(resume)
    summary = generator.generate_summary(resume)

    assert len(hashtags) >= 5
    assert "#Ai" in hashtags or "#AI" in hashtags
    assert "AI Product Lead" in summary
