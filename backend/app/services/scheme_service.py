"""
Scheme Service — Sahayak AI (Phase 4 + Lifecycle Management)
=============================================================
All scheme business logic lives here.
Routes stay thin — they call this service only.
"""

import math
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    SchemeNotFoundException,
    DuplicateSchemeNameException,
    DuplicateSchemeCodeException,
)
from app.core.logging import get_logger
from app.models.scheme import Scheme
from app.models.audit_log import AuditLog
from app.repositories.scheme_repository import SchemeRepository
from app.schemas.scheme import (
    SchemeCreate,
    SchemeUpdate,
    SchemeStatusUpdate,
    SchemeSearchRequest,
    AdminSchemeFilters,
    SchemeRead,
    SchemeSummary,
    SchemeListResponse,
    SchemeResponse,
    PaginationMeta,
    TranslationStatusItem,
    TranslationStatusResponse,
    AuditHistoryItem,
    AuditHistoryResponse,
    LANGUAGE_DISPLAY_NAMES,
    TARGET_LANGUAGES,
)

from app.models.enums import LanguageEnum, TranslationStatusEnum
from app.repositories.translation_repository import TranslationRepository
from app.services.translation.translation_service import _extract_translation_fields, _calculate_checksum

logger = get_logger(__name__)


def _make_audit_log(
    action: str,
    target: str,
    admin_id: uuid.UUID | None,
    result: str = "success",
    details: dict | None = None,
) -> AuditLog:
    return AuditLog(
        action=action,
        target=target,
        admin_id=admin_id,
        result=result,
        details=details or {},
    )


class SchemeService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = SchemeRepository(db)
        self._trans_repo = TranslationRepository(db)

    async def _inject_translation(self, scheme: Scheme, lang: str) -> None:
        """Inject translated fields into the scheme if available and requested lang is not EN."""
        if not lang or lang == "en":
            return
            
        # Ensure it's a valid language enum value
        valid_langs = [l.value for l in LanguageEnum]
        if lang not in valid_langs:
            return
            
        translation = await self._trans_repo.get_by_scheme_and_lang(scheme.id, lang, only_published=True)
        if translation and translation.translated_content:
            content = translation.translated_content
            # Override fields — only when translated value is non-empty (fallback to English if empty)
            if content.get("name", "").strip():
                scheme.name = content["name"].strip()
            if content.get("short_description", "").strip():
                scheme.short_description = content["short_description"].strip()
            if content.get("full_description", "").strip():
                scheme.full_description = content["full_description"].strip()
            if content.get("benefits", "").strip():
                scheme.benefits = content["benefits"].strip()

    async def _inject_translations_bulk(self, schemes: list[Scheme], lang: str) -> None:
        """Inject translated fields into multiple schemes."""
        logger.info(f"DEBUG: Injecting bulk for lang: {lang}, count: {len(schemes)}")
        if not lang or lang == "en" or not schemes:
            return
            
        valid_langs = [l.value for l in LanguageEnum]
        if lang not in valid_langs:
            logger.info(f"DEBUG: Lang {lang} not in valid_langs")
            return
            
        scheme_ids = [s.id for s in schemes]
        logger.info(f"DEBUG: Fetching translations for IDs: {scheme_ids}")
        translations = await self._trans_repo.get_by_scheme_ids_and_lang(scheme_ids, lang, only_published=True)
        logger.info(f"DEBUG: Found {len(translations)} translations")
        
        # Build lookup
        trans_map = {t.scheme_id: t for t in translations}
        
        for scheme in schemes:
            t = trans_map.get(scheme.id)
            if t and t.translated_content:
                content = t.translated_content
                # Only inject non-empty translations (fallback to English if empty)
                if content.get("name", "").strip():
                    scheme.name = content["name"].strip()
                if content.get("short_description", "").strip():
                    scheme.short_description = content["short_description"].strip()
                if content.get("full_description", "").strip():
                    scheme.full_description = content["full_description"].strip()
                if content.get("benefits", "").strip():
                    scheme.benefits = content["benefits"].strip()

    async def _enqueue_translations(self, scheme_id: uuid.UUID) -> None:
        """Async helper: enqueue a scheme for IndicTrans2 translation (fire-and-forget)."""
        from app.services.translation.executor import TranslationExecutor
        from app.services.translation.indictrans2_provider import IndicTrans2Provider
        executor = TranslationExecutor(provider=IndicTrans2Provider())
        await executor.enqueue_scheme(scheme_id)

    # ── Create ────────────────────────────────────────────────────────────

    async def create_scheme(
        self, payload: SchemeCreate, created_by: uuid.UUID | None = None
    ) -> SchemeResponse:
        """
        Validate uniqueness, then persist a new scheme.
        If published, write AuditLog and queue translations.
        """
        # Duplicate code check
        if await self._repo.code_exists(payload.scheme_code):
            raise DuplicateSchemeCodeException()

        # Duplicate name+state check
        if await self._repo.name_exists(payload.name, payload.state):
            raise DuplicateSchemeNameException()

        scheme = Scheme(
            scheme_code=payload.scheme_code,
            name=payload.name,
            short_description=payload.short_description,
            full_description=payload.full_description,
            benefits=payload.benefits,
            required_documents=payload.required_documents,
            application_process=payload.application_process,
            scheme_type=payload.scheme_type,
            category=payload.category,
            ministry=payload.ministry,
            department=payload.department,
            state=payload.state,
            district=payload.district,
            application_mode=payload.application_mode,
            application_start_date=payload.application_start_date,
            application_end_date=payload.application_end_date,
            official_url=payload.official_url,
            official_pdf_url=payload.official_pdf_url,
            contact_email=payload.contact_email,
            contact_phone=payload.contact_phone,
            is_active=payload.is_active,
            is_featured=payload.is_featured,
            created_by=created_by,
            updated_by=created_by,
        )
        saved = await self._repo.create(scheme)
        logger.info("Scheme created: %s by user %s", saved.scheme_code, created_by)

        action = "PUBLISH_SCHEME" if saved.is_active else "SAVE_DRAFT"
        self._repo._db.add(_make_audit_log(action, saved.scheme_code, created_by))
        await self._repo._db.commit()

        if saved.is_active:
            await self._enqueue_translations(saved.id)

        return SchemeResponse(
            message="Scheme created successfully.",
            data=SchemeRead.model_validate(saved),
        )

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_scheme_by_id(
        self, scheme_id: uuid.UUID, *, increment_view: bool = True, lang: str = "en"
    ) -> SchemeResponse:
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()
        if increment_view and scheme.is_active:
            await self._repo.increment_view_count(scheme_id)
            await self._repo._db.refresh(scheme)
            
        await self._inject_translation(scheme, lang)
        return SchemeResponse(data=SchemeRead.model_validate(scheme))

    async def get_scheme_by_id_admin(self, scheme_id: uuid.UUID) -> SchemeResponse:
        """Admin read — no view increment, includes inactive/draft/archived."""
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()
        return SchemeResponse(data=SchemeRead.model_validate(scheme))

    async def get_scheme_by_code(self, scheme_code: str, lang: str = "en") -> SchemeResponse:
        scheme = await self._repo.get_by_code(scheme_code)
        if not scheme:
            raise SchemeNotFoundException(f"No scheme found with code '{scheme_code}'.")
        await self._repo.increment_view_count(scheme.id)
        await self._repo._db.refresh(scheme)
        
        await self._inject_translation(scheme, lang)
        return SchemeResponse(data=SchemeRead.model_validate(scheme))

    # ── Search / list ─────────────────────────────────────────────────────

    async def search_schemes(self, req: SchemeSearchRequest, lang: str = "en") -> SchemeListResponse:
        items, total = await self._repo.search(
            query=req.query,
            category=req.category,
            scheme_type=req.scheme_type,
            application_mode=req.application_mode,
            state=req.state,
            ministry=req.ministry,
            is_featured=req.is_featured,
            is_active=req.is_active,
            date_from=req.date_from,
            date_to=req.date_to,
            sort=req.sort,
            page=req.page,
            page_size=req.page_size,
        )
        total_pages = math.ceil(total / req.page_size) if total > 0 else 1
        
        await self._inject_translations_bulk(list(items), lang)
        
        return SchemeListResponse(
            data=[SchemeSummary.model_validate(s) for s in items],
            meta=PaginationMeta(
                total=total,
                page=req.page,
                page_size=req.page_size,
                total_pages=total_pages,
            ),
        )

    async def get_admin_schemes(self, filters: AdminSchemeFilters) -> SchemeListResponse:
        """Admin-only: returns ALL schemes regardless of is_active status."""
        items, total = await self._repo.search(
            query=filters.query,
            category=filters.category,
            scheme_type=filters.scheme_type,
            application_mode=filters.application_mode,
            state=filters.state,
            ministry=filters.ministry,
            is_featured=filters.is_featured,
            is_active=filters.is_active,  # None = all schemes
            sort=filters.sort,
            page=filters.page,
            page_size=filters.page_size,
        )
        total_pages = math.ceil(total / filters.page_size) if total > 0 else 1
        return SchemeListResponse(
            data=[SchemeSummary.model_validate(s) for s in items],
            meta=PaginationMeta(
                total=total,
                page=filters.page,
                page_size=filters.page_size,
                total_pages=total_pages,
            ),
        )

    async def get_featured_schemes(self, limit: int = 10, lang: str = "en") -> SchemeListResponse:
        items = await self._repo.get_featured(limit=limit)
        await self._inject_translations_bulk(list(items), lang)
        return SchemeListResponse(
            data=[SchemeSummary.model_validate(s) for s in items],
            meta=PaginationMeta(total=len(items), page=1, page_size=limit, total_pages=1),
        )

    async def get_recent_schemes(self, limit: int = 10, lang: str = "en") -> SchemeListResponse:
        items = await self._repo.get_recent(limit=limit)
        await self._inject_translations_bulk(list(items), lang)
        return SchemeListResponse(
            data=[SchemeSummary.model_validate(s) for s in items],
            meta=PaginationMeta(total=len(items), page=1, page_size=limit, total_pages=1),
        )

    async def get_categories(self) -> dict:
        from app.models.enums import SchemeCategoryEnum
        return {
            "success": True,
            "data": [
                {"value": e.value, "label": e.value.replace("_", " ").title()}
                for e in SchemeCategoryEnum
            ],
        }

    async def get_states(self) -> dict:
        states = await self._repo.get_distinct_states()
        return {"success": True, "data": states}

    # ── Update (with translation invalidation) ────────────────────────────

    async def update_scheme(
        self,
        scheme_id: uuid.UUID,
        payload: SchemeUpdate,
        updated_by: uuid.UUID | None = None,
    ) -> SchemeResponse:
        """
        Update a scheme. If translatable content changed, mark existing
        translations OUTDATED and re-queue for IndicTrans2.
        """
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()

        # Capture checksum BEFORE update for comparison
        old_source = _extract_translation_fields(scheme)
        old_checksum = _calculate_checksum(old_source)

        update_data = payload.model_dump(exclude_unset=True)

        # Duplicate name check only if name or state changed
        new_name = update_data.get("name", scheme.name)
        new_state = update_data.get("state", scheme.state)
        if "name" in update_data or "state" in update_data:
            if await self._repo.name_exists(new_name, new_state, exclude_id=scheme_id):
                raise DuplicateSchemeNameException()

        if updated_by:
            update_data["updated_by"] = updated_by

        updated = await self._repo.update(scheme, update_data)

        # Checksum comparison — detect translatable content change
        new_source = _extract_translation_fields(updated)
        new_checksum = _calculate_checksum(new_source)
        content_changed = old_checksum != new_checksum

        if content_changed:
            logger.info(
                "Translatable content changed for scheme %s — marking translations OUTDATED",
                updated.scheme_code,
            )
            await self._trans_repo.mark_outdated(scheme_id)

        self._repo._db.add(_make_audit_log(
            "UPDATE_SCHEME",
            updated.scheme_code,
            updated_by,
            details={"content_changed": content_changed},
        ))
        await self._repo._db.commit()

        if content_changed and updated.is_active:
            # Re-queue translations asynchronously
            await self._enqueue_translations(updated.id)

        logger.info("Scheme updated: %s by user %s", scheme.scheme_code, updated_by)
        return SchemeResponse(
            message="Scheme updated successfully.",
            data=SchemeRead.model_validate(updated),
        )

    # ── Status toggle (Publish / Unpublish) ───────────────────────────────

    async def update_status(
        self, scheme_id: uuid.UUID, payload: SchemeStatusUpdate, updated_by: uuid.UUID | None = None
    ) -> SchemeResponse:
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()

        was_active = scheme.is_active
        updated = await self._repo.update(scheme, {"is_active": payload.is_active})

        action = "PUBLISH_SCHEME" if payload.is_active else "UNPUBLISH_SCHEME"
        self._repo._db.add(_make_audit_log(action, updated.scheme_code, updated_by))
        await self._repo._db.commit()

        # If newly published, enqueue translations if any are outdated or missing
        if not was_active and payload.is_active:
            await self._enqueue_translations(updated.id)

        status_word = "published" if payload.is_active else "unpublished"
        return SchemeResponse(
            message=f"Scheme {status_word} successfully.",
            data=SchemeRead.model_validate(updated),
        )

    # ── Archive (Soft delete) ─────────────────────────────────────────────

    async def delete_scheme(
        self, scheme_id: uuid.UUID, deleted_by: uuid.UUID | None = None
    ) -> dict:
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()
        code = scheme.scheme_code
        await self._repo.soft_delete(scheme)
        self._repo._db.add(_make_audit_log("ARCHIVE_SCHEME", code, deleted_by))
        await self._repo._db.commit()
        return {"success": True, "message": "Scheme archived successfully."}

    # ── Restore ───────────────────────────────────────────────────────────

    async def restore_scheme(
        self, scheme_id: uuid.UUID, restored_by: uuid.UUID | None = None
    ) -> SchemeResponse:
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()
        restored = await self._repo.restore(scheme)
        self._repo._db.add(_make_audit_log("RESTORE_SCHEME", restored.scheme_code, restored_by))
        await self._repo._db.commit()

        # Re-queue if translations are missing or outdated after restore
        from app.models.translation import SchemeTranslation
        from sqlalchemy import select as sa_select
        result = await self._repo._db.execute(
            sa_select(SchemeTranslation).where(
                SchemeTranslation.scheme_id == scheme_id,
                SchemeTranslation.status.in_([
                    TranslationStatusEnum.OUTDATED,
                ])
            )
        )
        outdated = result.scalars().all()
        if outdated:
            await self._enqueue_translations(scheme_id)

        return SchemeResponse(
            message="Scheme restored successfully.",
            data=SchemeRead.model_validate(restored),
        )

    # ── Translation Status ────────────────────────────────────────────────

    async def get_translation_status(self, scheme_id: uuid.UUID) -> TranslationStatusResponse:
        """Return per-language translation status for a scheme."""
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()

        from app.models.translation import SchemeTranslation
        result = await self._repo._db.execute(
            select(SchemeTranslation).where(SchemeTranslation.scheme_id == scheme_id)
        )
        existing = {t.language_code: t for t in result.scalars().all()}

        items: list[TranslationStatusItem] = []
        for lang_code, lang_name in LANGUAGE_DISPLAY_NAMES.items():
            trans = existing.get(lang_code)
            if trans is None:
                status = "missing"
                is_published = False
                version = None
                updated_at = None
                review_status = None
            elif trans.status == TranslationStatusEnum.PUBLISHED:
                status = "published"
                is_published = True
                version = trans.version
                updated_at = trans.updated_at
                review_status = trans.review_status.value if trans.review_status else None
            elif trans.status == TranslationStatusEnum.OUTDATED:
                status = "outdated"
                is_published = trans.is_published
                version = trans.version
                updated_at = trans.updated_at
                review_status = trans.review_status.value if trans.review_status else None
            else:
                status = "processing"
                is_published = False
                version = trans.version
                updated_at = trans.updated_at
                review_status = trans.review_status.value if trans.review_status else None

            items.append(TranslationStatusItem(
                language_code=lang_code,
                language_name=lang_name,
                status=status,
                is_published=is_published,
                version=version,
                updated_at=updated_at,
                review_status=review_status,
            ))

        return TranslationStatusResponse(
            scheme_id=scheme_id,
            scheme_code=scheme.scheme_code,
            translations=items,
        )

    # ── Audit History ─────────────────────────────────────────────────────

    async def get_audit_history(
        self, scheme_id: uuid.UUID, limit: int = 50
    ) -> AuditHistoryResponse:
        """Return sorted audit events for a scheme."""
        scheme = await self._repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()

        result = await self._repo._db.execute(
            select(AuditLog)
            .where(AuditLog.target == scheme.scheme_code)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        events = [
            AuditHistoryItem(
                id=log.id,
                action=log.action,
                admin_email=log.admin.email if log.admin else None,
                admin_name=log.admin.full_name if log.admin else None,
                result=log.result,
                details=log.details,
                timestamp=log.timestamp,
            )
            for log in logs
        ]

        return AuditHistoryResponse(
            scheme_id=scheme_id,
            scheme_code=scheme.scheme_code,
            events=events,
            total=len(events),
        )

    # ── Translation Feedback ──────────────────────────────────────────────
    
    async def submit_translation_feedback(
        self,
        scheme_id: uuid.UUID,
        language_code: str,
        is_helpful: bool,
        comment: str | None = None,
        user_id: uuid.UUID | None = None,
    ):
        from app.models.translation_feedback import TranslationFeedback
        
        feedback = TranslationFeedback(
            scheme_id=scheme_id,
            language_code=language_code,
            is_helpful=is_helpful,
            comment=comment,
            user_id=user_id,
            status="open"
        )
        self._repo._db.add(feedback)
        await self._repo._db.commit()
        return feedback
