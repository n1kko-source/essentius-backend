from app.domain.interfaces import IDocumentProcessor, IGraphGenerator

class GraphService:
    def __init__(self, processor: IDocumentProcessor, generator: IGraphGenerator):
        self.processor = processor
        self.generator = generator

    def create_graph_from_file(self, file_path: str) -> dict:
        # 1. Extraemos el texto del PDF
        text = self.processor.extract_text(file_path)
        
        # 2. Generamos la estructura del grafo con IA
        graph_data = self.generator.generate_roadmap(text)
        
        return graph_data