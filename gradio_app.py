from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
from PIL import Image

from app.services.pipeline import BrandingPipeline

REPO_ROOT = Path(__file__).resolve().parent
SAMPLE_IMAGE = REPO_ROOT / "sample_inputs" / "lenna_test_image.png"
SAMPLE_RESUME = REPO_ROOT / "sample_inputs" / "lenna_resume_sample.pdf"

pipeline = BrandingPipeline()


def _generate(photo_path: str | None, resume_path: str | None) -> tuple[Image.Image, str, str, dict]:
    if not photo_path or not resume_path:
        raise gr.Error("Portrait image and resume PDF are both required.")

    try:
        with tempfile.TemporaryDirectory(prefix="branding-space-") as tmp_dir:
            result = pipeline.run(photo_path, resume_path, output_dir=tmp_dir)
            poster = Image.open(result.poster_path).copy()
            metadata = result.metadata.model_dump()
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        raise gr.Error(f"Poster generation failed: {exc}") from exc

    hashtags = " ".join(metadata["hashtags"])
    return poster, metadata["summary"], hashtags, metadata


def generate_from_uploads(photo_path: str, resume_path: str) -> tuple[Image.Image, str, str, dict]:
    return _generate(photo_path, resume_path)


def generate_sample() -> tuple[Image.Image, str, str, dict]:
    return _generate(str(SAMPLE_IMAGE), str(SAMPLE_RESUME))


with gr.Blocks(title="Personal Branding Poster Generator") as demo:
    gr.Markdown(
        """
        # Personal Branding Poster Generator
        Upload one portrait image and one resume PDF to create a square branding poster.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            photo_input = gr.Image(
                type="filepath",
                label="Portrait Image",
                sources=["upload"],
            )
            resume_input = gr.File(
                type="filepath",
                label="Resume PDF",
                file_types=[".pdf"],
            )
            with gr.Row():
                generate_button = gr.Button("Generate Poster", variant="primary")
                sample_button = gr.Button("Run Sample Demo")

            gr.Examples(
                examples=[[str(SAMPLE_IMAGE), str(SAMPLE_RESUME)]],
                inputs=[photo_input, resume_input],
                label="Sample Inputs",
            )

        with gr.Column(scale=1):
            poster_output = gr.Image(label="Generated Poster")
            summary_output = gr.Textbox(label="Summary", lines=4)
            hashtags_output = gr.Textbox(label="Hashtags", lines=2)
            metadata_output = gr.JSON(label="Metadata")

    generate_button.click(
        fn=generate_from_uploads,
        inputs=[photo_input, resume_input],
        outputs=[poster_output, summary_output, hashtags_output, metadata_output],
    )
    sample_button.click(
        fn=generate_sample,
        outputs=[poster_output, summary_output, hashtags_output, metadata_output],
    )


if __name__ == "__main__":
    demo.launch()
