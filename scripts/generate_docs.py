"""Generate VitePress markdown documentation using pydoc-markdown.

This script runs pydoc-markdown to generate API documentation
from the tadoasync Python source code.

Usage:
    python scripts/generate_docs.py
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

MODULES = {
    "models.md": {
        "module": "tadoasync.models",
        "title": "Models Reference",
        "description": (
            "All models are dataclasses with JSON"
            " serialization support via `mashumaro`."
        ),
    },
    "api.md": {
        "module": "tadoasync.tadoasync",
        "title": "API Reference",
        "description": (
            "The main `Tado` class is the entry point"
            " for interacting with the Tado API."
        ),
    },
    "exceptions.md": {
        "module": "tadoasync.exceptions",
        "title": "Exceptions Reference",
        "description": "Exception classes raised by the Tado API client.",
    },
}


def _find_pydoc_markdown() -> str:
    """Find pydoc-markdown binary or raise."""
    pydoc_md = shutil.which("pydoc-markdown")
    if pydoc_md is None:
        msg = "pydoc-markdown not found. Install it with: pip install pydoc-markdown"
        raise RuntimeError(msg)
    return pydoc_md


def generate(filename: str, config: dict[str, str], pydoc_md: str) -> None:
    """Generate a single documentation page."""
    try:
        result = subprocess.run(
            [  # noqa: S603
                pydoc_md,
                "-I",
                "src",
                "-m",
                config["module"],
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        msg = f"Failed to generate docs for {config['module']}: {exc.stderr}"
        raise RuntimeError(msg) from exc

    header = f"# {config['title']}\n\n{config['description']}\n\n"
    content = header + result.stdout

    output = DOCS_DIR / filename
    output.write_text(content)
    print(f"Generated {output}")  # noqa: T201


def main() -> None:
    """Generate all documentation pages."""
    pydoc_md = _find_pydoc_markdown()
    for filename, config in MODULES.items():
        generate(filename, config, pydoc_md)


if __name__ == "__main__":
    main()
