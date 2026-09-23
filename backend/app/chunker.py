import uuid
from typing import List, Dict, Any
from app.models import ChunkMetadata
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

class TextChunker:
    """Splits structured document segments into overlapping chunks with citation metadata."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text(self, text: str) -> List[str]:
        """Splits a single text block into chunks with overlap, prioritizing natural paragraph/sentence breaks."""
        text = text.strip()
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Look for a clean delimiter before the hard boundary
            best_split = -1
            delimiters = ["\n\n", "\n", ". ", "? ", "! ", "; ", " "]
            search_window = text[start + int(self.chunk_size * 0.7):end]
            
            for delim in delimiters:
                pos = search_window.rfind(delim)
                if pos != -1:
                    best_split = start + int(self.chunk_size * 0.7) + pos + len(delim)
                    break

            if best_split == -1:
                best_split = end

            chunk = text[start:best_split].strip()
            if chunk:
                chunks.append(chunk)

            # Advance start index accounting for overlap
            start = max(start + 1, best_split - self.chunk_overlap)

        return chunks

    def chunk_document(
        self,
        doc_id: str,
        filename: str,
        file_type: str,
        parsed_data: Dict[str, Any]
    ) -> List[ChunkMetadata]:
        """Creates ChunkMetadata objects for each chunk extracted from parsed segments."""
        chunks: List[ChunkMetadata] = []
        segments = parsed_data.get("segments", [])

        for seg in segments:
            seg_text = seg.get("text", "")
            page_number = seg.get("page_number")
            line_start = seg.get("line_start")
            line_end = seg.get("line_end")

            sub_chunks = self._split_text(seg_text)
            for idx, text_block in enumerate(sub_chunks):
                chunk_id = f"{doc_id}_c{len(chunks) + 1}"
                
                # Approximate line boundaries if txt
                approx_line_start = line_start
                approx_line_end = line_end
                if file_type == "txt" and line_start is not None and len(sub_chunks) > 1:
                    total_lines = (line_end - line_start + 1) if line_end else 1
                    est_start = line_start + int(idx * (total_lines / len(sub_chunks)))
                    est_end = min(line_end, est_start + int(total_lines / len(sub_chunks)) + 1)
                    approx_line_start = est_start
                    approx_line_end = est_end

                chunk = ChunkMetadata(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    filename=filename,
                    file_type=file_type,
                    page_number=page_number,
                    line_start=approx_line_start,
                    line_end=approx_line_end,
                    text=text_block,
                    char_length=len(text_block)
                )
                chunks.append(chunk)

        return chunks
