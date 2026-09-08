"""Secure document extraction and tender-to-standard analysis."""

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.schemas.search import (
    ComplianceAnalysis,
    DocumentAnalysisResponse,
    DocumentStandardMatch,
    TenderFinding,
)
from app.schemas.standard import Standard as StandardSchema
from app.services.ai_engine import get_engine
from app.services.search_svc import SearchService
from app.utils.text_processing import chunk_text, clean_text

MAX_DOCUMENT_BYTES = 15 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


@dataclass
class ExtractedChunk:
    text: str
    page: int | None = None
    section: str | None = None
    clause: str | None = None


def _validate_upload(filename: str, content_type: str | None, contents: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=415, detail="Only PDF and DOCX files are supported")
    if not contents:
        raise HTTPException(status_code=422, detail="The uploaded document is empty")
    if suffix == ".pdf" and not contents.startswith(PDF_SIGNATURE):
        raise HTTPException(status_code=422, detail="The uploaded file is not a valid PDF")
    if suffix == ".docx":
        if not contents.startswith(ZIP_SIGNATURES):
            raise HTTPException(status_code=422, detail="The uploaded file is not a valid DOCX")
        try:
            with zipfile.ZipFile(io.BytesIO(contents)) as archive:
                names = archive.namelist()
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise HTTPException(status_code=422, detail="The uploaded DOCX is corrupted")
                if archive.testzip() is not None:
                    raise HTTPException(status_code=422, detail="The uploaded DOCX is corrupted")
        except zipfile.BadZipFile as exc:
            raise HTTPException(status_code=422, detail="The uploaded DOCX is corrupted") from exc

    allowed_types = {
        ".pdf": {"application/pdf"},
        ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    }
    if content_type not in allowed_types[suffix]:
        raise HTTPException(status_code=415, detail="The uploaded file content type is not supported")
    return suffix


def _metadata(text: str) -> tuple[str | None, str | None]:
    section_match = re.search(r"\b(?:section|chapter)\s+([\w.-]+)", text, re.IGNORECASE)
    clause_match = re.search(r"\b(?:clause|sub-clause)\s+([\w.-]+)", text, re.IGNORECASE)
    return (
        section_match.group(1) if section_match else None,
        clause_match.group(1) if clause_match else None,
    )


def _extract_pdf(contents: bytes) -> list[ExtractedChunk]:
    try:
        import fitz
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="PDF extraction dependency is not installed") from exc

    try:
        document = fitz.open(stream=contents, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=422, detail="The PDF document is corrupted") from exc

    chunks: list[ExtractedChunk] = []
    try:
        for page_number, page in enumerate(document, start=1):
            text = clean_text(page.get_text())
            if not text:
                try:
                    import pytesseract
                    from PIL import Image
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                    text = clean_text(pytesseract.image_to_string(image))
                except ImportError as exc:
                    raise HTTPException(status_code=503, detail="OCR dependencies are not installed") from exc
                except Exception as exc:
                    raise HTTPException(status_code=422, detail="OCR could not read the scanned PDF") from exc
            if text:
                section, clause = _metadata(text)
                for item in chunk_text(text, chunk_size=512, overlap=50, min_chunk_size=20):
                    chunks.append(ExtractedChunk(item, page_number, section, clause))
    finally:
        document.close()
    return chunks


def _extract_docx(contents: bytes) -> list[ExtractedChunk]:
    try:
        from docx import Document
        document = Document(io.BytesIO(contents))
        text = clean_text("\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()))
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="DOCX extraction dependency is not installed") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail="The DOCX document could not be read") from exc
    section, clause = _metadata(text)
    return [ExtractedChunk(item, None, section, clause) for item in chunk_text(text, chunk_size=512, overlap=50, min_chunk_size=20)]


async def extract_chunks(file: UploadFile) -> list[ExtractedChunk]:
    filename = Path(file.filename or "document").name
    contents = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(contents) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document must be smaller than 15 MB")
    suffix = _validate_upload(filename, file.content_type, contents)
    chunks = _extract_pdf(contents) if suffix == ".pdf" else _extract_docx(contents)
    if not chunks:
        raise HTTPException(status_code=422, detail="The document did not contain extractable text")
    return chunks


async def extract_text(file: UploadFile) -> str:
    """Backward-compatible text extraction API."""
    return " ".join(chunk.text for chunk in await extract_chunks(file))


def _sources(result) -> list[dict]:
    source = {
        key: result.payload.get(key)
        for key in ("standard_id", "standard_number", "chunk_id", "source_document", "section", "clause", "page")
        if result.payload.get(key) is not None
    }
    return [source] if source else []


def reconcile_findings(findings: list, matched: list) -> list[dict]:
    """Accept only findings grounded in the retrieved standard results."""
    by_id = {result.standard.id: result for result in matched}
    by_number = {result.standard.standard_number: result for result in matched}
    by_title = {result.standard.title: result for result in matched}
    valid_statuses = {"compliant", "non_compliant", "partially_compliant", "insufficient_evidence"}
    normalized_findings = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        standard_id = finding.get("standard_id")
        standard_number = finding.get("standard_number")
        matched_label = finding.get("matched_standard")
        if standard_id is not None and standard_id not in by_id:
            continue
        if standard_number is not None and standard_number not in by_number:
            continue
        matched_result = by_id.get(standard_id) if standard_id is not None else by_number.get(standard_number)
        if matched_result is None and isinstance(matched_label, str):
            matched_result = by_id.get(matched_label) or by_number.get(matched_label) or by_title.get(matched_label)
        if matched_result is None:
            continue
        actual_sources = _sources(matched_result)
        source_values = {
            field: {source[field] for source in actual_sources if field in source}
            for field in ("clause", "section", "page", "source_document")
        }
        normalized_findings.append({
            "tender_requirement": finding.get("tender_requirement"),
            "matched_standard": matched_result.standard.standard_number,
            "standard_id": matched_result.standard.id,
            "standard_number": matched_result.standard.standard_number,
            "relevance_score": matched_result.similarity_score,
            "clause": finding.get("clause") if finding.get("clause") in source_values["clause"] else None,
            "section": finding.get("section") if finding.get("section") in source_values["section"] else None,
            "page": finding.get("page") if finding.get("page") in source_values["page"] else None,
            "source_document": finding.get("source_document") if finding.get("source_document") in source_values["source_document"] else None,
            "compliance_status": finding.get("compliance_status") if finding.get("compliance_status") in valid_statuses else "insufficient_evidence",
            "explanation": finding.get("explanation") or "The available evidence is insufficient for a definitive conclusion.",
        })
    return normalized_findings


def ground_analysis_items(items: list, matched: list, kind: str) -> list[str]:
    """Keep free-form analysis clearly unverified and reject unknown references."""
    known_standard_refs = [
        str(value).lower()
        for result in matched
        for value in (result.standard.id, result.standard.standard_number)
    ]
    known_metadata = " ".join(
        str(value).lower()
        for result in matched
        for source in _sources(result)
        for value in source.values()
    )
    results = []
    for item in items:
        if not isinstance(item, str) or not item.strip():
            continue
        lowered = item.lower()
        looks_like_standard_reference = bool(re.search(r"\b(?:is|iec|iso|en|din|bs)\s*[\w().:-]+", lowered))
        references_known_standard = any(reference in lowered for reference in known_standard_refs)
        if looks_like_standard_reference and not references_known_standard:
            continue
        if re.search(r"\b(?:clause|sub-clause|section|chapter|page)\s+[\w.-]+", lowered):
            if not any(value and str(value).lower() in lowered and str(value).lower() in known_metadata for value in re.findall(r"[\w.-]+", lowered)):
                continue
        prefix = "Unverified recommendation: " if kind == "recommendations" else "Unverified compliance analysis: "
        results.append(prefix + item.strip())
    return results


async def analyze_document(file: UploadFile, db: Session) -> DocumentAnalysisResponse:
    chunks = await extract_chunks(file)
    tender_text = " ".join(chunk.text for chunk in chunks)
    search_service = SearchService(db)
    matches = {}

    for chunk in chunks[:20]:
        response = search_service.semantic_search(chunk.text, top_k=5)
        for result in response.results:
            current = matches.get(result.standard.id)
            if current is None or result.similarity_score > current.similarity_score:
                matches[result.standard.id] = result

    matched = sorted(matches.values(), key=lambda result: result.similarity_score, reverse=True)[:10]
    matched_payload = [
        {
            "standard_id": result.standard.id,
            "standard_number": result.standard.standard_number,
            "title": result.standard.title,
            "description": result.standard.description,
            "relevance_score": result.similarity_score,
            "sources": _sources(result),
        }
        for result in matched
    ]
    analysis = get_engine().analyze_compliance(tender_text, matched_payload)
    analysis["findings"] = reconcile_findings(analysis.get("findings", []), matched)
    analysis["conflicts"] = ground_analysis_items(analysis.get("conflicts", []), matched, "conflicts")
    grounded_gaps = ground_analysis_items(
        analysis.get("gaps", []) + analysis.get("compliance_gaps", []), matched, "gaps"
    )
    grounded_recommendations = ground_analysis_items(
        analysis.get("recommendations", []) + analysis.get("clauses_to_watch", []), matched, "recommendations"
    )
    analysis["gaps"] = grounded_gaps
    analysis["compliance_gaps"] = grounded_gaps
    analysis["recommendations"] = grounded_recommendations
    analysis["clauses_to_watch"] = grounded_recommendations
    return DocumentAnalysisResponse(
        filename=Path(file.filename or "document").name,
        extracted_text_preview=tender_text[:500],
        matched_standards=[
            DocumentStandardMatch(
                standard=StandardSchema.model_validate(result.standard),
                similarity_score=result.similarity_score,
                sources=_sources(result),
            )
            for result in matched
        ],
        findings=[TenderFinding.model_validate(item) for item in analysis.get("findings", [])],
        compliance_analysis=ComplianceAnalysis.model_validate(analysis),
    )
