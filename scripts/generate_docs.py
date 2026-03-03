"""Generate VitePress markdown documentation using pydoc-markdown.

This script runs pydoc-markdown to generate API documentation
from the tadoasync Python source code, then enriches the output
with inherited members discovered via runtime introspection.

Usage:
    python scripts/generate_docs.py
"""

from __future__ import annotations

import importlib
import inspect
import re
import shutil
import subprocess
import sys
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


def _get_inherited_members(cls: type) -> list[dict[str, str]]:
    """Get public inherited members not defined in cls itself."""
    own = set(cls.__dict__)
    members = []
    for name in sorted(dir(cls)):
        if name.startswith("_") or name in own:
            continue
        attr = getattr(cls, name, None)
        if attr is None:
            continue
        sig = ""
        doc = inspect.getdoc(attr) or ""
        if callable(attr):
            try:
                sig = str(inspect.signature(attr))
            except (ValueError, TypeError):
                sig = "(...)"
        members.append({"name": name, "sig": sig, "doc": doc})
    return members


def _format_inherited_section(
    module_name: str, class_name: str, members: list[dict[str, str]]
) -> str:
    """Format inherited members as markdown."""
    lines = ["\n**Inherited from base class:**\n"]
    for m in members:
        anchor = f'<a id="{module_name}.{class_name}.{m["name"]}"></a>\n\n'
        if m["sig"]:
            lines.append(
                f'{anchor}#### {m["name"]}\n\n```python\n'
                f'def {m["name"]}{m["sig"]}\n```\n'
            )
        else:
            lines.append(f'{anchor}#### {m["name"]}\n')
        if m["doc"]:
            lines.append(f'\n{m["doc"]}\n')
    return "\n".join(lines)


def _enrich_with_inherited(content: str, module_name: str) -> str:
    """Add inherited members to each class in the markdown."""
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        return content

    # Find class sections: "## ClassName Objects" pattern
    class_pattern = re.compile(r"^## (\w+) Objects\s*$", re.MULTILINE)
    matches = list(class_pattern.finditer(content))

    if not matches:
        return content

    # Process in reverse to preserve positions
    for match in reversed(matches):
        class_name = match.group(1)
        cls = getattr(mod, class_name, None)
        if cls is None or not isinstance(cls, type):
            continue
        inherited = _get_inherited_members(cls)
        if not inherited:
            continue
        section = _format_inherited_section(module_name, class_name, inherited)
        # Insert before the next class section or at end
        insert_pos = len(content)
        for other in matches:
            if other.start() > match.start():
                insert_pos = other.start()
                break
        content = content[:insert_pos] + section + "\n" + content[insert_pos:]

    return content


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
    content = header + _enrich_with_inherited(result.stdout, config["module"])

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
