from pathlib import Path
from typing import List, Dict, Any
import pymupdf as fitz  # PyMuPDF

class DocumentParser:
    """Extracts structured text and location metadata from PDF and TXT files."""

    @staticmethod
    def parse_pdf(file_path: Path) -> Dict[str, Any]:
        """
        Parses a PDF file using PyMuPDF (fitz).
        Returns total page count and page-level extracted text segments.
        """
        doc = fitz.open(file_path)
        pages_data = []
        total_pages = len(doc)

        for page_idx in range(total_pages):
            page = doc[page_idx]
            text = page.get_text("text") or ""
            # Basic cleanup: strip trailing whitespace while preserving paragraphs
            clean_text = text.strip()
            if clean_text:
                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": clean_text
                })

        doc.close()
        return {
            "page_count": total_pages,
            "segments": pages_data
        }

    @staticmethod
    def parse_txt(file_path: Path) -> Dict[str, Any]:
        """
        Parses a TXT file, preserving line numbers and content.
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        segments = []
        # Group lines into logical segments or retain entire document
        full_text = "".join(lines).strip()
        if full_text:
            segments.append({
                "page_number": None,
                "line_start": 1,
                "line_end": len(lines),
                "text": full_text
            })

        return {
            "page_count": None,
            "line_count": len(lines),
            "segments": segments
        }

    @classmethod
    def parse_file(cls, file_path: Path, file_type: str) -> Dict[str, Any]:
        if file_type == "pdf":
            return cls.parse_pdf(file_path)
        elif file_type == "txt":
            return cls.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
