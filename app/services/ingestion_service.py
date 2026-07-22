from app.domain.interfaces import IDocumentProcessor, IVectorRepository, IEmbeddingProvider

# Free-tier: menos embeds por PDF (chunks más grandes) + tope duro
MAX_CHUNKS_FREE_TIER = 40


class TooManyChunksError(ValueError):
    """PDF excede el tope de chunks del free-tier local."""


class IngestionService:
    def __init__(
        self,
        processor: IDocumentProcessor,
        repo: IVectorRepository,
        embedder: IEmbeddingProvider,
    ):
        self.processor = processor
        self.repo = repo
        self.embedder = embedder

    def process_and_store(self, file_path: str, source_metadata: dict):
        raw_text = self.processor.extract_text(file_path)
        chunks = self.processor.create_chunks(raw_text)

        if len(chunks) > MAX_CHUNKS_FREE_TIER:
            raise TooManyChunksError(
                f"Este PDF genera {len(chunks)} fragmentos (máx. {MAX_CHUNKS_FREE_TIER} "
                "en free-tier). Divide el archivo en partes más cortas y vuelve a subir."
            )

        title = source_metadata.get("title", "Desconocido")
        document_id = source_metadata.get("document_id")

        for i, chunk in enumerate(chunks):
            vector = self.embedder.create_embedding(chunk)
            metadata = {
                "content": chunk,
                "text": chunk,
                "source": title,
                "document_id": document_id,
                "chunk_index": i,
            }
            self.repo.save_embedding(vector=vector, metadata=metadata)

        return {"status": "success", "chunks_processed": len(chunks)}
