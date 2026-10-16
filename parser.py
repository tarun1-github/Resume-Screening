"""
FITMENT.AI - Parser Module
Robust PDF Resume Extraction and Job Description Sanitization.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO, Union
from pypdf import PdfReader
from pypdf.errors import PdfReadError


class DocumentProcessingError(Exception):
    """Base exception for document processing errors."""
    pass


class PDFParsingError(DocumentProcessingError):
    """Raised when a PDF file cannot be parsed or read."""
    pass


class EmptyDocumentError(DocumentProcessingError):
    """Raised when extracted document text is empty or contains insufficient content."""
    pass


def extract_text_from_pdf(
    file_source: Union[BinaryIO, bytes, str, Path],
    min_characters: int = 40,
) -> tuple[str, int]:
    """
    Extracts, normalizes, and cleans plain text from a PDF resume file.

    Args:
        file_source: A file-like object, raw bytes, or path to the PDF file.
        min_characters: Minimum characters expected for a valid parsed document.

    Returns:
        tuple[str, int]: A tuple containing (cleaned_text, total_pages).

    Raises:
        PDFParsingError: If the PDF cannot be opened or is password-protected/corrupted.
        EmptyDocumentError: If extracted text is below min_characters.
    """
    try:
        if isinstance(file_source, (str, Path)):
            pdf_path = Path(file_source)
            if not pdf_path.is_file():
                raise PDFParsingError(f"File not found: {pdf_path}")
            reader = PdfReader(str(pdf_path))
        elif isinstance(file_source, bytes):
            reader = PdfReader(io.BytesIO(file_source))
        else:
            # Handles Streamlit's UploadedFile or any io.BytesIO / BinaryIO
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            reader = PdfReader(file_source)

        if reader.is_encrypted:
            try:
                # Attempt empty password decryption if applicable
                reader.decrypt("")
            except Exception as decrypt_err:
                raise PDFParsingError(
                    "The PDF file is encrypted and password-protected."
                ) from decrypt_err

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise EmptyDocumentError("The uploaded PDF file contains 0 pages.")

        extracted_chunks: list[str] = []
        for index, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                if page_text:
                    extracted_chunks.append(page_text)
            except Exception as page_err:
                # Log or tolerate single-page parsing failures if others succeed
                continue

        raw_text = "\n\n".join(extracted_chunks)
        cleaned_text = clean_text(raw_text)

        if len(cleaned_text.strip()) < min_characters:
            raise EmptyDocumentError(
                f"Extracted content is too short or empty ({len(cleaned_text.strip())} chars). "
                "Ensure the PDF contains selectable text (not flattened scanned images)."
            )

        return cleaned_text, total_pages

    except DocumentProcessingError:
        raise
    except PdfReadError as pdf_err:
        raise PDFParsingError(f"Corrupted or invalid PDF format: {pdf_err}") from pdf_err
    except Exception as general_err:
        raise PDFParsingError(f"Unexpected error while reading PDF: {general_err}") from general_err


def sanitize_job_description(jd_text: str, min_characters: int = 30) -> str:
    """
    Cleans, validates, and normalizes a Job Description string.

    Args:
        jd_text: The raw job description string input by the user.
        min_characters: Minimum characters required for meaningful evaluation.

    Returns:
        str: Sanitized job description text.

    Raises:
        EmptyDocumentError: If the job description is missing or too brief.
    """
    if not jd_text or not isinstance(jd_text, str):
        raise EmptyDocumentError("Job description cannot be empty.")

    cleaned_jd = clean_text(jd_text)

    if len(cleaned_jd) < min_characters:
        raise EmptyDocumentError(
            f"Job description is too brief ({len(cleaned_jd)} chars). "
            f"Please provide at least {min_characters} characters for an accurate evaluation."
        )

    return cleaned_jd


def clean_text(text: str) -> str:
    """
    Normalizes whitespace, removes null bytes, and standardizes line breaks.
    """
    if not text:
        return ""

    # Remove null bytes and non-printable control characters (except newline, tab)
    text = text.replace("\x00", " ")
    text = re.sub(r"[\r\f\v]", "\n", text)
    # Replace multiple spaces with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace more than 3 consecutive newlines with two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_document_statistics(text: str) -> dict[str, int]:
    """
    Calculates summary metadata and stats for processed text.
    """
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    char_count = len(text)
    # Average adult reading speed ~200 words per minute
    estimated_read_minutes = max(1, round(word_count / 200))

    return {
        "word_count": word_count,
        "character_count": char_count,
        "estimated_reading_minutes": estimated_read_minutes,
    }
