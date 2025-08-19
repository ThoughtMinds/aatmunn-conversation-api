from pydantic import BaseModel, computed_field

class DashboardStats(BaseModel):
    """
    Pydantic model for dashboard statistics.

    Attributes:
        total_intents (int): The total number of intents.
        total_summaries (int): The total number of summaries.
        total_tasks (int): The total number of tasks.
        total_queries (int): The total number of queries, computed from the other fields.
    """

    total_intents: int
    total_summaries: int
    total_tasks: int
    
    @computed_field
    @property
    def total_queries(self) -> int:
        return self.total_intents + self.total_summaries + self.total_tasks
    
    