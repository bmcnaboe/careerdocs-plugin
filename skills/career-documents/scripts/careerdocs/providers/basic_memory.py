"""Basic Memory provider (the first MCP provider).

Writes each entity as a Basic Memory note under ``<vault>/<folder>/<type>/<id>.md``:
frontmatter carries ``title``, ``type``, ``permalink`` (``<folder>/<type>/<id>``),
``tags``, and every schema field; the body carries ``## Statement`` (the text),
``## Observations`` (one ``- [<type>] <label> #<id>`` per fact), and ``## Relations``
(``- part_of [[…]]`` for an achievement's parent, ``- evidences [[…]]`` for each skill).

Writes are plain file writes to the vault; Basic Memory's watcher indexes them, so the
MCP tools are for retrieval only and never the sole write path. The index and the source,
approval, and diff ledgers reuse the Markdown provider's layout; only the per-entity note
format differs. Export produces the structured-Markdown layout with ``derived: true``.
"""

from __future__ import annotations

from pathlib import Path

from ..errors import ProviderUnreachable
from .markdown import MarkdownProvider, _write_frontmatter_file

_STATEMENT_MAX = 120

# Entity types whose own ``title`` schema field doubles as the note title, so the note
# title key must not be added or stripped for them (it would clobber real data).
TITLE_FIELD_TYPES = {"experience", "patent", "publication"}


def _truncate(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _STATEMENT_MAX else text[: _STATEMENT_MAX - 1].rstrip() + "…"


def entity_title(entity: dict) -> str:
    etype = entity["type"]
    if etype in TITLE_FIELD_TYPES:
        return entity.get("title") or etype.capitalize()
    if etype == "contact":
        return entity.get("name") or entity.get("headline") or "Contact"
    if etype == "achievement":
        return _truncate(entity.get("statement", "Achievement"))
    if etype == "education":
        return entity.get("institution") or entity.get("degree") or "Education"
    if etype in ("skill", "project", "credential"):
        return entity.get("name") or etype.capitalize()
    return etype


class BasicMemoryProvider(MarkdownProvider):
    PROVIDER_NAME = "basic_memory"

    def __init__(self, workspace, config: dict):
        providers = config.get("providers", {})
        if "basic_memory" not in providers:
            raise ProviderUnreachable("config selects basic_memory but has no basic_memory block")
        settings = providers["basic_memory"]
        self.project = settings["project"]
        self.folder = settings.get("folder", "career")
        self._set_base(Path(settings["vault_path"]) / self.folder)

    @classmethod
    def at(cls, vault_path, project: str, folder: str = "career") -> "BasicMemoryProvider":
        instance = cls.__new__(cls)
        instance.project = project
        instance.folder = folder
        instance._set_base(Path(vault_path) / folder)
        return instance

    def capabilities(self) -> dict:
        return {"authoritative_ok": True, "search": True, "context": True}

    def _note_body(self, entity: dict) -> str:
        by_id = getattr(self, "_by_id", {})
        lines: list[str] = []
        statement = entity.get("statement") or entity.get("summary")
        if statement:
            lines += ["## Statement", "", statement, ""]
        lines += [
            "## Observations",
            "",
            f"- [{entity['type']}] {entity_title(entity)} #{entity['id']}",
            "",
        ]
        relations: list[str] = []
        if entity["type"] == "achievement":
            parent = by_id.get(entity.get("parent_id"))
            if parent is not None:
                relations.append(f"- part_of [[{entity_title(parent)}]]")
        for skill_id in entity.get("skill_ids", []):
            skill = by_id.get(skill_id)
            if skill is not None:
                relations.append(f"- evidences [[{entity_title(skill)}]]")
        if relations:
            lines += ["## Relations", ""] + relations + [""]
        return "\n".join(lines).rstrip("\n") + "\n"

    def _write_entity(self, entity: dict) -> None:
        path = self.base_dir / entity["type"] / f"{entity['id']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = {**entity, "permalink": f"{self.folder}/{entity['type']}/{entity['id']}"}
        # Add a note title only when the entity has no native `title` field to serve as one.
        if entity["type"] not in TITLE_FIELD_TYPES:
            frontmatter["title"] = entity_title(entity)
        _write_frontmatter_file(path, frontmatter, body=self._note_body(entity))

    def _read_entity(self, path: Path) -> dict:
        from .markdown import _read_frontmatter_file

        frontmatter, _ = _read_frontmatter_file(path)
        frontmatter.pop("permalink", None)
        if frontmatter.get("type") not in TITLE_FIELD_TYPES:
            frontmatter.pop("title", None)
        return frontmatter
