from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PdfPage:
    source: str
    page: int
    text: str


def load_pdf_pages(pdf_dir: Path) -> tuple[list[PdfPage], int, int]:
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    pdf_paths = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in: {pdf_dir}")

    pages: list[PdfPage] = []
    skipped_empty_pages = 0

    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                skipped_empty_pages += 1
                continue

            pages.append(PdfPage(source=pdf_path.name, page=index, text=text))

    return pages, len(pdf_paths), skipped_empty_pages
