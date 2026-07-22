import fitz  # PyMuPDF (muy rápido para PDFs) o puedes usar langchain_community.document_loaders
from app.domain.interfaces import IDocumentProcessor
from typing import List

class PDFProcessor(IDocumentProcessor):
    def extract_text(self, file_path: str) -> str:
        """Extrae el texto de un archivo PDF."""
        text = ""
        try:
            # Abrimos el documento con PyMuPDF
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise ValueError(f"Error procesando el PDF: {str(e)}")

    def create_chunks(self, text: str, chunk_size: int = 1800) -> List[str]:
        """Divide el texto en fragmentos (chunks) para la base de datos vectorial."""
        # Free-tier: chunks más grandes → menos llamadas a embeddings.
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks