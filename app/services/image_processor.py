from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class ImageProcessingError(Exception):
    """Raised when image processing fails."""


@dataclass
class ProcessedPortrait:
    portrait_rgba: Image.Image
    mask: Image.Image
    bbox: tuple[int, int, int, int]


class ImageProcessor:
    """Handle portrait extraction and stylization."""

    def load_image(self, image_path: str | Path) -> Image.Image:
        path = Path(image_path)
        if not path.exists():
            raise ImageProcessingError(f"Image file not found: {path}")
        try:
            image = Image.open(path).convert("RGBA")
        except Exception as exc:  # pragma: no cover - Pillow exceptions vary
            raise ImageProcessingError(f"Failed to open image: {exc}") from exc
        return image

    def isolate_subject(self, image: Image.Image) -> ProcessedPortrait:
        cutout = self._remove_background_with_rembg(image)
        if cutout is None:
            cutout = self._remove_background_with_grabcut(image)

        alpha = cutout.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            raise ImageProcessingError("Could not isolate person from image.")

        return ProcessedPortrait(portrait_rgba=cutout, mask=alpha, bbox=bbox)

    def _remove_background_with_rembg(self, image: Image.Image) -> Image.Image | None:
        try:
            from rembg import remove
        except Exception:
            return None

        try:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            result = remove(buffer.getvalue())
            return Image.open(BytesIO(result)).convert("RGBA")
        except Exception:
            return None

    def _remove_background_with_grabcut(self, image: Image.Image) -> Image.Image:
        rgba = image.convert("RGBA")
        rgb = np.array(rgba.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        mask = np.zeros(bgr.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        height, width = bgr.shape[:2]
        rect = (
            max(1, int(width * 0.1)),
            max(1, int(height * 0.05)),
            max(1, int(width * 0.8)),
            max(1, int(height * 0.9)),
        )
        cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        foreground = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")

        refined = Image.fromarray(foreground, mode="L").filter(ImageFilter.GaussianBlur(radius=2))
        result = rgba.copy()
        result.putalpha(refined)
        return result

    def create_desaturated_portrait(self, processed: ProcessedPortrait) -> Image.Image:
        grayscale = ImageOps.grayscale(processed.portrait_rgba.convert("RGB"))
        toned = ImageOps.colorize(grayscale, black="#111111", white="#d9d9df").convert("RGBA")
        toned.putalpha(processed.mask)
        toned = ImageEnhance.Contrast(toned).enhance(1.15)
        toned = ImageEnhance.Color(toned).enhance(0.15)
        return self.crop_to_subject(toned, processed.bbox)

    def create_silhouette(self, processed: ProcessedPortrait, color: str) -> Image.Image:
        silhouette = Image.new("RGBA", processed.portrait_rgba.size, color)
        silhouette.putalpha(processed.mask)
        return self.crop_to_subject(silhouette, processed.bbox)

    def crop_to_subject(
        self,
        image: Image.Image,
        bbox: tuple[int, int, int, int],
        padding_ratio: float = 0.12,
    ) -> Image.Image:
        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top
        pad_x = int(width * padding_ratio)
        pad_top = int(height * padding_ratio)
        pad_bottom = int(height * 0.04)
        crop_box = (
            max(0, left - pad_x),
            max(0, top - pad_top),
            min(image.width, right + pad_x),
            min(image.height, bottom + pad_bottom),
        )
        return image.crop(crop_box)
