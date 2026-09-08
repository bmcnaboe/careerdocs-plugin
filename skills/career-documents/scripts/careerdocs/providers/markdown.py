"""Structured-Markdown provider (the reference implementation).

Layout under the provider directory (``providers.markdown.path``, default ``profile/``):

* ``profile.md`` — the index (frontmatter = the ``CareerProfile`` index fields).
* ``<type>/<id>.md`` — one file per entity: frontmatter is every field except the body
  field (``statement`` for achievements, ``summary`` for experiences and projects); the
  body is that text.
* ``sources.jsonl`` — the source ledger; ``approvals.jsonl`` — the append-only approval
  ledger; ``diffs/<diff_id>.json`` — proposed diffs.

Frontmatter is written as JSON (a valid YAML subset) so nested fields round-trip exactly
without a YAML dependency. The content hash is SHA-256 over the canonical JSON of the
sorted entities plus the index, so it is stable regardless of file order.
"""

from __future__ import annotations

import json
from pathlib import Path

from .. import schema, util
from ..errors import CareerDocsError, ProfileInvalid, SchemaTooNew
from ..ids import ENTITY_TYPES
from .base import INDEX_FIELDS, NotAuthoritative, Provider, hash_profile

# Which entity field is stored as the Markdown body rather than in the frontmatter.
BODY_FIELD = {"achievement": "statement", "experience": "summary", "project": "summary"}


def _write_frontmatter_file(path: Path, frontmatter: dict, body: str = "") -> None:
    text = "---\n" + json.dumps(frontmatter, indent=2, ensure_ascii=False, sort_keys=True) + "\n---\n"
    if body:
        text += "\n" + body.rstrip("\n") + "\n"
    path.write_text(text, encoding="utf-8")


def _read_frontmatter_file(path: Path) -> tuple[dict, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ProfileInvalid(f"{path} is missing its frontmatter fence")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ProfileInvalid(f"{path} has an unterminated frontmatter fence")
    frontmatter = json.loads("\n".join(lines[1:end]))
    body = "\n".join(lines[end + 1:])
    return frontmatter, body


class MarkdownProvider(Provider):
    PROVIDER_NAME = "markdown"

    def __init__(self, workspace, config: dict):
        base = Path(workspace) / config["providers"]["markdown"]["path"]
        self._set_base(base)

    @classmethod
    def at(cls, base_dir) -> "MarkdownProvider":
        instance = cls.__new__(cls)
        instance._set_base(Path(base_dir))
        return instance

    def _set_base(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.index_file = base_dir / "profile.md"
        self.sources_file = base_dir / "sources.jsonl"
        self.approvals_file = base_dir / "approvals.jsonl"
        self.diffs_dir = base_dir / "diffs"

    # --- profile ---

    def _empty_profile(self) -> dict:
        return {
            "schema_version": schema.profile_schema_version(),
            "applicant_ref": "applicant",
            "authoritative_provider": self.PROVIDER_NAME,
            "derived": False,
            "updated_at": util.now(),
            "entities": [],
            "sources": self.read_sources(),
        }

    @staticmethod
    def _too_new(stored: str) -> bool:
        def as_tuple(version: str) -> tuple[int, ...]:
            return tuple(int(part) for part in version.split("."))

        try:
            return as_tuple(stored) > as_tuple(schema.profile_schema_version())
        except ValueError:
            return False

    def _read_entity(self, path: Path) -> dict:
        frontmatter, body = _read_frontmatter_file(path)
        body_field = BODY_FIELD.get(frontmatter.get("type"))
        if body_field and body.strip():
            frontmatter[body_field] = body.strip()
        return frontmatter

    def _write_entity(self, entity: dict) -> None:
        path = self.base_dir / entity["type"] / f"{entity['id']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = dict(entity)
        body = ""
        body_field = BODY_FIELD.get(entity["type"])
        if body_field and body_field in frontmatter:
            body = str(frontmatter.pop(body_field) or "")
        _write_frontmatter_file(path, frontmatter, body=body)

    def _read_entities(self) -> list[dict]:
        entities: list[dict] = []
        for type_name in ENTITY_TYPES:
            type_dir = self.base_dir / type_name
            if not type_dir.is_dir():
                continue
            for entity_file in sorted(type_dir.glob("*.md")):
                entities.append(self._read_entity(entity_file))
        return entities

    def read(self) -> dict:
        if not self.index_file.exists():
            return self._empty_profile()
        index, _ = _read_frontmatter_file(self.index_file)
        stored_version = index.get("schema_version", "0.0.0")
        if self._too_new(stored_version):
            raise SchemaTooNew(
                f"profile schema {stored_version} is newer than supported "
                f"{schema.profile_schema_version()}"
            )
        profile = {**index, "entities": self._read_entities(), "sources": self.read_sources()}
        schema.assert_valid_profile(profile)
        return profile

    def write(self, profile: dict) -> str:
        schema.assert_valid_profile(profile)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._by_id = {e["id"]: e for e in profile["entities"]}

        index = {field: profile[field] for field in INDEX_FIELDS}
        _write_frontmatter_file(self.index_file, index, body="# Career profile")

        desired = {f"{e['type']}/{e['id']}.md": e for e in profile["entities"]}
        for type_name in ENTITY_TYPES:
            type_dir = self.base_dir / type_name
            if type_dir.is_dir():
                for entity_file in type_dir.glob("*.md"):
                    if f"{type_name}/{entity_file.name}" not in desired:
                        entity_file.unlink()
        for entity in profile["entities"]:
            self._write_entity(entity)

        self._write_sources(profile.get("sources", []))
        return hash_profile(profile)

    def capabilities(self) -> dict:
        return {"authoritative_ok": True, "search": False, "context": False}

    def export(self, target: dict) -> dict:
        from .. import visibility

        profile = visibility.filter_visible(self.read(), for_export=True)
        profile = {**profile, "derived": True}
        provider_name = target.get("provider", "markdown")
        if provider_name == "markdown":
            dest = MarkdownProvider.at(target["path"])
            dest.write(profile)
            return {
                "provider": "markdown",
                "location": str(dest.base_dir),
                "derived": True,
                "entities": len(profile["entities"]),
            }
        if provider_name == "basic_memory":
            from .basic_memory import BasicMemoryProvider

            dest = BasicMemoryProvider.at(
                target["vault_path"], target["project"], target.get("folder", "career")
            )
            dest.write(profile)
            return {
                "provider": "basic_memory",
                "location": str(dest.base_dir),
                "derived": True,
                "entities": len(profile["entities"]),
            }
        raise NotAuthoritative(f"cannot export to provider {provider_name!r}")

    # --- ledgers ---

    def read_sources(self) -> list[dict]:
        if not self.sources_file.exists():
            return []
        return [json.loads(line) for line in self.sources_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _write_sources(self, sources: list[dict]) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sources_file.write_text(
            "".join(json.dumps(s, sort_keys=True, ensure_ascii=False) + "\n" for s in sources),
            encoding="utf-8",
        )

    def append_source(self, source: dict) -> None:
        if any(s["source_id"] == source["source_id"] for s in self.read_sources()):
            return
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with self.sources_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(source, sort_keys=True, ensure_ascii=False) + "\n")

    def store_diff(self, diff: dict) -> None:
        self.diffs_dir.mkdir(parents=True, exist_ok=True)
        (self.diffs_dir / f"{diff['diff_id']}.json").write_text(
            json.dumps(diff, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def load_diff(self, diff_id: str) -> dict:
        path = self.diffs_dir / f"{diff_id}.json"
        if not path.exists():
            raise CareerDocsError(f"diff {diff_id} not found", code="DIFF_NOT_FOUND")
        return json.loads(path.read_text(encoding="utf-8"))

    def append_approval(self, approval: dict) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with self.approvals_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(approval, sort_keys=True, ensure_ascii=False) + "\n")

    def read_approvals(self) -> list[dict]:
        if not self.approvals_file.exists():
            return []
        return [json.loads(line) for line in self.approvals_file.read_text(encoding="utf-8").splitlines() if line.strip()]
