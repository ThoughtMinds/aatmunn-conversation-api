from pydantic import BaseModel, computed_field

class DashboardStats(BaseModel):
    total_intents: int
    total_summaries: int
    total_tasks: int
    
    @computed_field
    @property
    def total_queries(self) -> int:
        return self.total_intents + self.total_summaries + self.total_tasks
    
    