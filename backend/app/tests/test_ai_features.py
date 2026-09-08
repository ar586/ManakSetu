"""Focused tests for AI feature hardening."""

import asyncio
import io
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from app.services.document_svc import (
    MAX_DOCUMENT_BYTES,
    _validate_upload,
    extract_text,
    ground_analysis_items,
    reconcile_findings,
)
from app.services.llm_service import LLMConfigurationError, LLMService


def upload(name: str, content: bytes, content_type: str | None = None) -> UploadFile:
    return UploadFile(file=io.BytesIO(content), filename=name, headers={"content-type": content_type} if content_type else None)


def test_upload_rejects_unsupported_type():
    with pytest.raises(HTTPException) as error:
        _validate_upload("notes.txt", "text/plain", b"text")
    assert error.value.status_code == 415


def test_upload_rejects_fake_pdf():
    with pytest.raises(HTTPException) as error:
        _validate_upload("notes.pdf", "application/pdf", b"not a pdf")
    assert error.value.status_code == 422


def test_upload_rejects_empty_document():
    with pytest.raises(HTTPException) as error:
        _validate_upload("notes.pdf", "application/pdf", b"")
    assert error.value.status_code == 422


def test_upload_rejects_invalid_mime():
    with pytest.raises(HTTPException) as error:
        _validate_upload("notes.pdf", "text/plain", b"%PDF-1.7")
    assert error.value.status_code == 415


def test_upload_rejects_corrupt_docx():
    with pytest.raises(HTTPException) as error:
        _validate_upload("notes.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK\x03\x04bad")
    assert error.value.status_code == 422


def test_valid_pdf_signature_is_accepted():
    assert _validate_upload("notes.pdf", "application/pdf", b"%PDF-1.7") == ".pdf"


def test_valid_docx_container_is_accepted():
    import zipfile

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    assert _validate_upload(
        "notes.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        output.getvalue(),
    ) == ".docx"


def test_upload_rejects_oversized_document():
    async def run():
        with pytest.raises(HTTPException) as error:
            await extract_text(upload("large.pdf", b"%PDF-" + b"x" * MAX_DOCUMENT_BYTES, "application/pdf"))
        assert error.value.status_code == 413

    asyncio.run(run())


def test_llm_missing_configuration_is_explicit(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMConfigurationError, match="not configured"):
        LLMService().generate("system", "user")


def test_no_retrieved_context_has_grounded_chat_message():
    from app.services.ai_engine import AIEngine

    answer = AIEngine().answer_from_context([], [], "What is clause 9?")
    assert "does not provide enough information" in answer


def test_rag_context_preserves_citations(monkeypatch):
    from app.services.search_svc import SearchService

    service = SearchService(None)
    service.ai_engine = SimpleNamespace(embed=lambda query: [0.1, 0.2])
    service.vector_store = SimpleNamespace(search=lambda **kwargs: [SimpleNamespace(
        payload={
            "text": "Concrete requirement",
            "standard_id": "std-1",
            "standard_number": "IS 456:2000",
            "source_document": "is456.pdf",
            "clause": "5",
            "page": 12,
            "chunk_id": "std-1:0",
        },
        score=0.88,
        standard_id="std-1",
        standard_number="IS 456:2000",
        title="Concrete",
    )])
    context = service.retrieve_context("concrete", "std-1")
    assert context[0]["source_document"] == "is456.pdf"
    assert context[0]["page"] == 12


def test_reconcile_findings_rejects_invented_standard_and_metadata():
    class Standard:
        id = "std-1"
        standard_number = "IS 456:2000"
        title = "Concrete"

    class Result:
        standard = Standard()
        similarity_score = 0.91
        payload = {"standard_id": "std-1", "clause": "5"}

    findings = [
        {"matched_standard": "IS 999", "clause": "99", "page": 100, "compliance_status": "compliant", "explanation": "bad"},
        {"matched_standard": "IS 456:2000", "clause": "99", "page": 100, "compliance_status": "unknown", "explanation": "grounded"},
    ]
    result = reconcile_findings(findings, [Result()])
    assert len(result) == 1
    assert result[0]["relevance_score"] == 0.91
    assert result[0]["clause"] is None
    assert result[0]["page"] is None
    assert result[0]["compliance_status"] == "insufficient_evidence"


def test_reconcile_findings_validates_metadata_by_field():
    class Standard:
        id = "std-1"
        standard_number = "IS 456:2000"
        title = "Concrete"

    class Result:
        standard = Standard()
        similarity_score = 0.91
        payload = {
            "standard_id": "std-1",
            "standard_number": "IS 456:2000",
            "source_document": "is456.pdf",
            "section": "5",
            "clause": "5.2",
            "page": 12,
        }

    result = reconcile_findings([{
        "standard_id": "std-1",
        "standard_number": "IS 456:2000",
        "clause": "5",
        "section": "5.2",
        "page": 12,
        "source_document": "is456.pdf",
        "compliance_status": "compliant",
        "explanation": "evidence",
    }], [Result()])[0]
    assert result["clause"] is None
    assert result["section"] is None
    assert result["page"] == 12
    assert result["source_document"] == "is456.pdf"


def test_hallucinated_analysis_items_are_removed_or_marked_unverified():
    class Standard:
        id = "std-1"
        standard_number = "IS 456:2000"
        title = "Concrete"

    class Result:
        standard = Standard()
        payload = {"standard_id": "std-1", "standard_number": "IS 456:2000", "clause": "5"}

    items = ground_analysis_items([
        "Conflict with IS 999 clause 4",
        "Gap at clause 99",
        "Review concrete testing requirements",
    ], [Result()], "conflicts")
    assert len(items) == 1
    assert items[0].startswith("Unverified compliance analysis:")


def test_legacy_analysis_aliases_cannot_bypass_grounding():
    from app.services.document_svc import ground_analysis_items

    assert ground_analysis_items(["IS 999 clause 8"], [], "gaps") == []


def test_legacy_full_text_chat_path_is_removed():
    from app.services.ai_engine import AIEngine

    assert not hasattr(AIEngine, "answer_standard_question")
