import uuid
import re
from typing import List, Dict, Any
from app.models import ChunkMetadata
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

class TextChunker:
    """Splits structured document segments into overlapping chunks with citation metadata and context preservation."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text(self, text: str, doc_context: str = "") -> List[str]:
        """
        Splits text into chunks prioritizing paragraph boundaries and structural headers.
        Attaches section/document context prefix to ensure project names & topics remain attached to sub-chunks.
        """
        text = text.strip()
        if not text:
            return []

        lines = text.splitlines()
        paragraphs: List[str] = []
        curr_p: List[str] = []
        active_header = ""

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if curr_p:
                    paragraphs.append("\n".join(curr_p))
                    curr_p = []
                continue

            # Identify structural headers or section titles
            is_header = (
                stripped.startswith("#") or
                stripped.startswith("==") or
                stripped.startswith("Project:") or
                stripped.startswith("Section:") or
                (len(stripped) < 60 and stripped.endswith(":"))
            )

            if is_header:
                if curr_p:
                    paragraphs.append("\n".join(curr_p))
                    curr_p = []
                paragraphs.append(stripped)
            else:
                curr_p.append(line)

        if curr_p:
            paragraphs.append("\n".join(curr_p))

        if not paragraphs:
            return [text]

        chunks = []
        curr_chunk_p: List[str] = []
        curr_len = 0
        current_active_header = ""

        for p in paragraphs:
            is_h = (
                p.startswith("#") or
                p.startswith("Project:") or
                p.startswith("Section:") or
                (len(p) < 60 and p.endswith(":"))
            )
            if is_h:
                current_active_header = p.lstrip("#").strip()

            p_len = len(p)

            if curr_len + p_len > self.chunk_size and curr_chunk_p:
                chunk_body = "\n".join(curr_chunk_p)
                prefix_parts = []
                if doc_context:
                    prefix_parts.append(doc_context)
                if current_active_header and current_active_header.lower() not in chunk_body.lower():
                    prefix_parts.append(current_active_header)

                prefix = f"[{' | '.join(prefix_parts)}]\n" if prefix_parts else ""
                full_text_block = (prefix + chunk_body).strip()
                chunks.append(full_text_block)

                # Maintain paragraph overlap
                if len(curr_chunk_p) > 1:
                    curr_chunk_p = [curr_chunk_p[-1]]
                else:
                    curr_chunk_p = []
                curr_len = sum(len(x) for x in curr_chunk_p)

            curr_chunk_p.append(p)
            curr_len += p_len

        if curr_chunk_p:
            chunk_body = "\n".join(curr_chunk_p)
            prefix_parts = []
            if doc_context:
                prefix_parts.append(doc_context)
            if current_active_header and current_active_header.lower() not in chunk_body.lower():
                prefix_parts.append(current_active_header)

            prefix = f"[{' | '.join(prefix_parts)}]\n" if prefix_parts else ""
            full_text_block = (prefix + chunk_body).strip()
            chunks.append(full_text_block)

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
        clean_doc_title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")

        for seg in segments:
            seg_text = seg.get("text", "")
            page_number = seg.get("page_number")
            line_start = seg.get("line_start")
            line_end = seg.get("line_end")

            doc_context = f"{clean_doc_title}"
            if page_number is not None:
                doc_context += f" Page {page_number}"

            sub_chunks = self._split_text(seg_text, doc_context=doc_context)
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

