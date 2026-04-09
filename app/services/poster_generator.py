from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from app.models.schemas import PosterMetadata, PosterResult, ResumeData
from app.services.hashtag_generator import HashtagGenerator
from app.services.image_processor import ImageProcessor


class PosterGenerationError(Exception):
    """Raised when poster generation fails."""


class PosterGenerator:
    """Compose the final poster and metadata."""

    def __init__(
        self,
        image_processor: ImageProcessor | None = None,
        hashtag_generator: HashtagGenerator | None = None,
    ) -> None:
        self.image_processor = image_processor or ImageProcessor()
        self.hashtag_generator = hashtag_generator or HashtagGenerator()
        self.default_colors = ["#D6FF1F", "#FF7A1A"]

    def generate(
        self,
        image_path: str | Path,
        resume: ResumeData,
        output_dir: str | Path = "output",
    ) -> PosterResult:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not resume.summary:
            resume.summary = self.hashtag_generator.generate_summary(resume)
        hashtags = self.hashtag_generator.generate_hashtags(resume)

        original = self.image_processor.load_image(image_path)
        processed = self.image_processor.isolate_subject(original)
        portrait = self.image_processor.create_desaturated_portrait(processed)
        silhouettes = [
            self.image_processor.create_silhouette(processed, color)
            for color in self.default_colors
        ]

        canvas = self._build_canvas(size=1080)
        self._composite_layers(canvas, silhouettes, portrait)
        self._draw_text(canvas, hashtags, resume)

        poster_path = output_path / "poster.png"
        metadata_path = output_path / "metadata.json"
        canvas.save(poster_path)

        metadata = PosterMetadata(
            name=resume.name,
            title=resume.title,
            summary=resume.summary,
            hashtags=hashtags,
            input_files={"photo": str(image_path), "resume_pdf": ""},
            output_file=str(poster_path),
        )
        metadata_path.write_text(
            json.dumps(metadata.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return PosterResult(
            poster_path=poster_path,
            metadata_path=metadata_path,
            metadata=metadata,
        )

    def _build_canvas(self, size: int) -> Image.Image:
        background = Image.new("RGBA", (size, size), "#C8CBD6")
        overlay = Image.new("RGBA", (size, size), "#AAB0BE")
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=80))
        return Image.blend(background, overlay, alpha=0.35)

    def _composite_layers(
        self,
        canvas: Image.Image,
        silhouettes: list[Image.Image],
        portrait: Image.Image,
    ) -> None:
        size = canvas.size[0]
        placements = [(-80, 45, 1.02), (75, 20, 0.99)]
        for silhouette, (offset_x, offset_y, scale) in zip(silhouettes, placements, strict=False):
            layer = self._resize_to_fit(silhouette, int(size * scale))
            tinted = layer.filter(ImageFilter.GaussianBlur(radius=1))
            canvas.alpha_composite(tinted, dest=self._bottom_center(layer, canvas, offset_x, offset_y))

        portrait_layer = self._resize_to_fit(portrait, int(size * 1.01))
        canvas.alpha_composite(portrait_layer, dest=self._bottom_center(portrait_layer, canvas, 12, 8))

    def _draw_text(self, canvas: Image.Image, hashtags: list[str], resume: ResumeData) -> None:
        draw = ImageDraw.Draw(canvas)
        safe_box = (46, 520, canvas.width - 36, canvas.height - 42)
        text = self._arrange_hashtags(hashtags)

        font = self._fit_font(draw, text, safe_box)
        draw.multiline_text(
            (safe_box[0], safe_box[1]),
            text,
            font=font,
            fill="white",
            spacing=10,
            stroke_width=1,
            stroke_fill=(255, 255, 255, 50),
        )

        display_name = (resume.english_name or resume.name).upper()
        name_font = self._load_font(54)
        draw.text((58, 58), display_name, font=name_font, fill=ImageColor.getrgb("white"))

    def _arrange_hashtags(self, hashtags: list[str]) -> str:
        rows: list[str] = []
        line = ""
        for tag in hashtags:
            candidate = f"{line} {tag}".strip()
            if len(candidate) > 20 and line:
                rows.append(line)
                line = tag
            else:
                line = candidate
        if line:
            rows.append(line)
        return "\n".join(rows[:3])

    def _fit_font(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        box: tuple[int, int, int, int],
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        max_width = box[2] - box[0]
        max_height = box[3] - box[1]
        for size in range(120, 48, -4):
            font = self._load_font(size)
            left, top, right, bottom = draw.multiline_textbbox((0, 0), text, font=font, spacing=10)
            if right - left <= max_width and bottom - top <= max_height:
                return font
        return self._load_font(48)

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        font_candidates = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf",
        ]
        for candidate in font_candidates:
            path = Path(candidate)
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        return ImageFont.load_default()

    def _resize_to_fit(self, image: Image.Image, max_height: int) -> Image.Image:
        ratio = max_height / image.height
        new_size = (int(image.width * ratio), max_height)
        return image.resize(new_size, Image.LANCZOS)

    def _bottom_center(
        self,
        layer: Image.Image,
        canvas: Image.Image,
        offset_x: int,
        offset_y: int,
    ) -> tuple[int, int]:
        x = (canvas.width - layer.width) // 2 + offset_x
        y = canvas.height - layer.height + offset_y
        return x, y
