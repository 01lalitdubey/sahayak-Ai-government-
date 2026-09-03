"""
Scheme → vector index ingestion — Sahayak AI RAG
================================================
Builds one English document per active scheme (name, classification,
descriptions, benefits, documents, process, and a plain-text summary of the
deterministic eligibility rules), embeds it with all-MiniLM-L6-v2 and upserts
it into ChromaDB.

Run as a script:   python -m app.services.rag.ingest
Or via the API:     POST /api/v1/rag/ingest   (admin)
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.database.database import AsyncSessionLocal
from app.models.eligibility_rule import EligibilityRule
from app.models.scheme import Scheme
from app.services.rag import embeddings, vector_store

logger = get_logger(__name__)

_MAX_DOC_CHARS = 3500


def _rules_to_text(rules: list[EligibilityRule]) -> str:
    if not rules:
        return "Eligibility: no specific restrictions recorded — open to all applicants."
    parts: list[str] = []
    for r in rules:
        bits: list[str] = []
        if r.minimum_age is not None or r.maximum_age is not None:
            lo = r.minimum_age if r.minimum_age is not None else "any"
            hi = r.maximum_age if r.maximum_age is not None else "any"
            bits.append(f"age {lo}-{hi}")
        if r.minimum_income is not None or r.maximum_income is not None:
            lo = r.minimum_income if r.minimum_income is not None else 0
            hi = r.maximum_income if r.maximum_income is not None else "no cap"
            bits.append(f"annual income {lo}-{hi} INR")
        if getattr(r, "gender", None):
            bits.append(f"gender {r.gender.value}")
        if getattr(r, "occupation", None):
            bits.append(f"occupation {r.occupation.value}")
        if getattr(r, "category", None):
            bits.append(f"social category {r.category.value.upper()}")
        if getattr(r, "education", None):
            bits.append(f"minimum education {r.education.value}")
        if getattr(r, "state", None):
            bits.append(f"resident of {r.state}")
        if getattr(r, "district", None):
            bits.append(f"district {r.district}")
        if getattr(r, "require_farmer", None) is True:
            bits.append("must be a farmer")
        if getattr(r, "require_disabled", None) is True:
            bits.append("must have a disability")
        if bits:
            parts.append("; ".join(bits))
    if not parts:
        return "Eligibility: criteria defined but unstructured."
    return "Eligibility criteria: " + " | ".join(parts)


def _scheme_to_document(scheme: Scheme) -> str:
    lines: list[str] = [f"Scheme: {scheme.name} (code {scheme.scheme_code})"]
    if scheme.scheme_type:
        lines.append(f"Type: {scheme.scheme_type.value} government scheme")
    if scheme.category:
        lines.append(f"Category: {scheme.category.value}")
    if scheme.ministry:
        lines.append(f"Ministry: {scheme.ministry}")
    if scheme.department:
        lines.append(f"Department: {scheme.department}")
    lines.append(f"Applicable area: {scheme.state or 'All of India (central scheme)'}")
    if scheme.short_description:
        lines.append(f"Summary: {scheme.short_description}")
    if scheme.full_description:
        lines.append(f"Details: {scheme.full_description}")
    if scheme.benefits:
        lines.append(f"Benefits: {scheme.benefits}")
    if scheme.required_documents:
        lines.append(f"Required documents: {scheme.required_documents}")
    if scheme.application_process:
        lines.append(f"How to apply: {scheme.application_process}")
    if scheme.application_mode:
        lines.append(f"Application mode: {scheme.application_mode.value}")
    lines.append(_rules_to_text(list(scheme.eligibility_rules or [])))
    doc = "\n".join(lines)
    return doc[:_MAX_DOC_CHARS]


def _scheme_to_metadata(scheme: Scheme) -> dict[str, Any]:
    return {
        "scheme_id": str(scheme.id),
        "scheme_code": scheme.scheme_code or "",
        "scheme_name": scheme.name or "",
        "category": scheme.category.value if scheme.category else "",
        "state": scheme.state or "",
        "ministry": scheme.ministry or "",
        "official_url": scheme.official_url or "",
        "official_pdf_url": scheme.official_pdf_url or "",
        "scheme_type": scheme.scheme_type.value if scheme.scheme_type else "",
    }


async def build_index(*, rebuild: bool = True) -> dict[str, int]:
    """(Re)build the whole vector index from active schemes. Returns counts."""
    if rebuild:
        vector_store.reset()

    total = 0
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Scheme)
            .options(selectinload(Scheme.eligibility_rules))
            .where(Scheme.is_active == True)  # noqa: E712
            .order_by(Scheme.created_at)
        )
        schemes = list(result.scalars().all())

    if not schemes:
        logger.warning("Ingestion: no active schemes found.")
        return {"schemes": 0, "chunks": 0}

    BATCH = 64
    for i in range(0, len(schemes), BATCH):
        batch = schemes[i : i + BATCH]
        docs = [_scheme_to_document(s) for s in batch]
        metas = [_scheme_to_metadata(s) for s in batch]
        ids = [f"scheme::{s.id}" for s in batch]
        vecs = await embeddings.embed(docs)
        vector_store.upsert(ids=ids, embeddings=vecs, documents=docs, metadatas=metas)
        total += len(batch)
        logger.info("Ingestion progress: %d/%d schemes", total, len(schemes))

    count = vector_store.count()
    logger.info("Ingestion complete: %d schemes, collection size %d", total, count)
    return {"schemes": total, "chunks": count}


if __name__ == "__main__":  # pragma: no cover
    out = asyncio.run(build_index(rebuild=True))
    print(out)
