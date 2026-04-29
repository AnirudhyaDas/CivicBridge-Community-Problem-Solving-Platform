from pydantic import BaseModel

class SolutionCreate(BaseModel):
    solution_text: str
    resources_required: str
    estimated_cost: str
    time_to_implement: str
    risks: str
    impact_score: int
    feasibility_score: int

class SolutionOut(SolutionCreate):
    id: int
    final_score: float
    is_adopted: bool

class SolutionView(BaseModel):
    id: int
    solution_text: str
    resources_required: str | None
    estimated_cost: str | None
    time_to_implement: str | None
    risks: str | None
    impact_score: int
    feasibility_score: int
    cost_efficiency_score: int
    is_adopted: bool
    final_score: float

    class Config:
        from_attributes = True

