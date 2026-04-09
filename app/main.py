from __future__ import annotations

import argparse

from fastapi import FastAPI

from app.routes.poster import router as poster_router
from app.services.pipeline import BrandingPipeline

app = FastAPI(title="Personal Branding Poster Generator", version="0.1.0")
app.include_router(poster_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a branding poster from a photo and resume PDF.")
    parser.add_argument("--image", required=False, help="Path to portrait image (.jpg/.jpeg/.png)")
    parser.add_argument("--resume", required=False, help="Path to resume PDF")
    parser.add_argument("--output-dir", default="output", help="Directory for generated files")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.image or not args.resume:
        parser.print_help()
        return

    pipeline = BrandingPipeline()
    result = pipeline.run(args.image, args.resume, output_dir=args.output_dir)
    print(f"Poster saved to: {result.poster_path}")
    print(f"Metadata saved to: {result.metadata_path}")


if __name__ == "__main__":
    main()
