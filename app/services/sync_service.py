from app.domain.interfaces import ICalendarProvider
from datetime import datetime, timedelta

class SyncRoadmapService:
    def __init__(self, calendar: ICalendarProvider):
        self.calendar = calendar

    def sync_to_calendar(self, roadmap_data: dict) -> dict:
        """
        Toma los nodos del roadmap y los agenda en días consecutivos.
        """
        # 1. El Agente lee tu calendario real (o simulado)
        existing_events = self.calendar.get_upcoming_events()
        
        results = []
        base_date = datetime.now()
        
        # 2. Iteramos sobre las tarjetas del Grafo de Conocimiento
        for index, node in enumerate(roadmap_data.get("nodes", [])):
            # Distribuimos una tarea por día
            target_date = (base_date + timedelta(days=index + 1)).strftime("%Y-%m-%d")
            
            # 3. El Agente ejecuta la herramienta (Tool) sobre Notion
            response = self.calendar.schedule_event(
                title=f"Estudiar: {node['title']}",
                description=node['description'],
                date=target_date
            )
            
            results.append({
                "node_id": node["id"],
                "title": node["title"],
                "date": target_date,
                "notion_url": response["notion_url"]
            })
            
        return {
            "message": "Ruta de aprendizaje sincronizada con éxito en tu Notion",
            "events_created": len(results),
            "details": results
        }