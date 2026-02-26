"""Generate VitePress markdown documentation using pydoc-markdown.

This script runs pydoc-markdown to generate API documentation
from the tadoasync Python source code.

Usage:
    python scripts/generate_docs.py
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
SRC_DIR = str(ROOT_DIR / "src")

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

FILTER_EXPRESSION = (
    "not name.startswith('_')"
    " and (obj.docstring or"
    " (obj.parent and not isinstance(obj.parent,"
    " __import__('docspec').Module)))"
)


def _find_pydoc_markdown() -> str:
    """Find pydoc-markdown binary or raise."""
    pydoc_md = shutil.which("pydoc-markdown")
    if pydoc_md is None:
        msg = (
            "pydoc-markdown not found."
            " Install it with: uv pip install pydoc-markdown"
        )
        raise RuntimeError(msg)
    return pydoc_md


def _build_config(module: str) -> str:
    """Build a pydoc-markdown YAML config for a module."""
    return f"""\
loaders:
  - type: python
    search_path: ["{SRC_DIR}"]
    modules: ["{module}"]
processors:
  - type: filter
    expression: "{FILTER_EXPRESSION}"
    documented_only: false
  - type: smart
  - type: crossref
renderer:
  type: markdown
  render_module_header: true
  descriptive_class_title: true
  render_typehint_in_data_header: true
"""


def generate(filename: str, config: dict[str, str], pydoc_md: str) -> None:
    """Generate a single documentation page."""
    yaml_content = _build_config(config["module"])

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(yaml_content)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [pydoc_md, tmp_path],  # noqa: S603
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        msg = f"Failed to generate docs for {config['module']}: {exc.stderr}"
        raise RuntimeError(msg) from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    header = f"# {config['title']}\n\n{config['description']}\n\n"
    content = header + result.stdout

    output = DOCS_DIR / filename
    output.write_text(content, encoding="utf-8")
    print(f"Generated {output}")  # noqa: T201


def main() -> None:
    """Generate all documentation pages."""
    pydoc_md = _find_pydoc_markdown()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, config in MODULES.items():
        generate(filename, config, pydoc_md)


if __name__ == "__main__":
    main()
