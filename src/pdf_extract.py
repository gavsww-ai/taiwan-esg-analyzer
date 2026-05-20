from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class PDFPageText:
    source_document: str
    page: int
    text: str


def extract_pages_from_pdf(pdf_path: str | Path) -> List[PDFPageText]:
    """
    Extract text from a PDF page by page using pdfplumber.

    The extraction stays local and intentionally avoids API calls, vector
    databases, or agent-based processing.
    """
    try:
        import pdfplumber
    except ImportError as exc:
        raise ImportError("Install pdfplumber first: pip install pdfplumber") from exc

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages: List[PDFPageText] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(
                PDFPageText(
                    source_document=path.name,
                    page=page_number,
                    text=text,
                )
            )
    return pages


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Return a single string with page markers for quick manual review."""
    chunks = []
    for page in extract_pages_from_pdf(pdf_path):
        chunks.append(f"\n\n--- PAGE {page.page} ---\n{page.text}")
    return "".join(chunks)
