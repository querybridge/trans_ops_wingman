"""Load SOP markdown files from procedures/ into ProcedureDocument/ProcedureChunk.

File format: a `---` front-matter block of `key: value` lines, then `## Section`
headings. Each section becomes one chunk with a stable ID, so re-ingesting
never duplicates content (the same IDs will be used as vector IDs).
"""

import re
from datetime import date
from pathlib import Path

from django.conf import settings
from django.db import transaction

from operations.models import Customer, ProcedureChunk, ProcedureDocument

from .models import IngestionRecord

PROCEDURES_DIR = Path(settings.BASE_DIR) / "procedures"
REQUIRED_KEYS = {"document_id", "version", "title", "customer", "issue_type", "effective_from"}


class ProcedureFormatError(ValueError):
    pass


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_procedure(path):
    text = Path(path).read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        raise ProcedureFormatError(f"{path}: missing front matter")
    meta = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    missing = REQUIRED_KEYS - meta.keys()
    if missing:
        raise ProcedureFormatError(f"{path}: missing keys {sorted(missing)}")
    if meta["issue_type"] not in ProcedureDocument.IssueType.values:
        raise ProcedureFormatError(f"{path}: unknown issue_type {meta['issue_type']!r}")

    sections = []
    for block in re.split(r"^## ", match.group(2), flags=re.M)[1:]:
        heading, _, body = block.partition("\n")
        body = " ".join(body.split())
        if body:
            sections.append((heading.strip(), body))
    if not sections:
        raise ProcedureFormatError(f"{path}: no sections")
    return meta, sections


@transaction.atomic
def ingest_procedures(directory=PROCEDURES_DIR):
    customers = {c.customer_id: c for c in Customer.objects.all()}
    seen = set()
    chunk_count = 0
    for path in sorted(Path(directory).glob("*.md")):
        meta, sections = parse_procedure(path)
        scope = meta["customer"]
        if scope != "shared" and scope not in customers:
            raise ProcedureFormatError(f"{path}: unknown customer {scope!r}")
        doc, _ = ProcedureDocument.objects.update_or_create(
            document_id=meta["document_id"],
            version=meta["version"],
            defaults={
                "title": meta["title"],
                "customer": None if scope == "shared" else customers[scope],
                "issue_type": meta["issue_type"],
                "region": meta.get("region", ""),
                "effective_from": date.fromisoformat(meta["effective_from"]),
                "effective_to": date.fromisoformat(meta["effective_to"]) if meta.get("effective_to") else None,
                "source_path": str(path.relative_to(settings.BASE_DIR)),
            },
        )
        seen.add(doc.pk)
        doc.chunks.all().delete()
        ProcedureChunk.objects.bulk_create(
            ProcedureChunk(
                chunk_id=f"{doc.document_id}@{doc.version}#{slugify(heading)}",
                document=doc,
                ordinal=i,
                section=heading,
                text=body,
            )
            for i, (heading, body) in enumerate(sections, start=1)
        )
        chunk_count += len(sections)
    removed, _ = ProcedureDocument.objects.exclude(pk__in=seen).delete()
    IngestionRecord.objects.create(
        kind=IngestionRecord.Kind.PROCEDURES,
        source_name=str(Path(directory).relative_to(settings.BASE_DIR)) if Path(directory).is_relative_to(settings.BASE_DIR) else str(directory),
        rows_accepted=len(seen),
    )
    return {"documents": len(seen), "chunks": chunk_count, "removed": removed}
