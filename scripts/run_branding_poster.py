#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare the local environment and generate a branding poster.",
    )
    parser.add_argument("--image", required=True, help="Path to portrait image")
    parser.add_argument("--resume", required=True, help="Path to PDF resume")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for generated poster and metadata",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter to use for virtualenv creation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    image_path = Path(args.image).expanduser().resolve()
    resume_path = Path(args.resume).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    validate_inputs(image_path, resume_path)
    python_bin = ensure_virtualenv(repo_root, args.python)
    install_requirements(repo_root, python_bin)
    run_generator(repo_root, python_bin, image_path, resume_path, output_dir)

    metadata_path = output_dir / "metadata.json"
    poster_path = output_dir / "poster.png"
    payload = {
        "poster_path": str(poster_path),
        "metadata_path": str(metadata_path),
        "metadata": json.loads(metadata_path.read_text(encoding="utf-8")),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def validate_inputs(image_path: Path, resume_path: Path) -> None:
    if not image_path.exists():
        raise SystemExit(f"Image file not found: {image_path}")
    if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise SystemExit("Image file must be .jpg, .jpeg, or .png")
    if not resume_path.exists():
        raise SystemExit(f"Resume file not found: {resume_path}")
    if resume_path.suffix.lower() != ".pdf":
        raise SystemExit("Resume file must be a PDF")


def ensure_virtualenv(repo_root: Path, python_executable: str) -> Path:
    venv_dir = repo_root / ".venv"
    python_bin = venv_dir / "bin" / "python"
    if python_bin.exists():
        return python_bin
    run([python_executable, "-m", "venv", str(venv_dir)], cwd=repo_root)
    return python_bin


def install_requirements(repo_root: Path, python_bin: Path) -> None:
    marker = repo_root / ".deps-installed"
    requirements = repo_root / "requirements.txt"
    if marker.exists() and marker.stat().st_mtime >= requirements.stat().st_mtime:
        return
    run([str(python_bin), "-m", "pip", "install", "-r", str(requirements)], cwd=repo_root)
    marker.write_text("ok\n", encoding="utf-8")


def run_generator(
    repo_root: Path,
    python_bin: Path,
    image_path: Path,
    resume_path: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            str(python_bin),
            "-m",
            "app.main",
            "--image",
            str(image_path),
            "--resume",
            str(resume_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
    )


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, env=os.environ.copy(), check=False)
    if completed.returncode != 0:
        raise SystemExit(f"Command failed ({completed.returncode}): {' '.join(command)}")


if __name__ == "__main__":
    main()
