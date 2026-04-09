---
name: personal-branding-poster
description: Generate a personal branding poster from one portrait photo and one PDF resume by running the bundled FastAPI and Python pipeline in this repository, then return the poster image plus metadata in the conversation.
---

# Personal Branding Poster

Use this skill when the user wants you to generate a poster from:

- 1 portrait photo (`jpg`, `jpeg`, `png`)
- 1 resume PDF (`pdf`)

## Default Behavior

When the user supplies the input files, run:

```bash
python scripts/run_branding_poster.py \
  --image /path/to/photo.jpg \
  --resume /path/to/resume.pdf \
  --output-dir output
```

The script should:

1. Create a local virtual environment if needed.
2. Install the repository requirements if needed.
3. Run the bundled CLI generator.
4. Return the generated poster and metadata paths in chat.

## Response Format

After generation finishes, answer with:

- a short success summary
- the absolute path to the poster
- the absolute path to the metadata JSON
- an inline local image preview using Markdown
- the generated summary and hashtags

## Notes

- This repository is both the app and the skill bundle.
- Prefer `scripts/run_branding_poster.py` for execution so the environment is prepared consistently.
- If the user asks for code changes or customization, edit this repository directly rather than creating another copy.
