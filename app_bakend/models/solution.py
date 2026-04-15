from sqlalchemy import String, Column,VARCHAR, Integer, Text, ForeignKey, Float, Boolean
from app_backend.database import Base

class Solution(Base):
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, index=True)
    after_image_path = Column(String, nullable=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    proposed_by = Column(Integer, ForeignKey("users.id"))
    solution_text = Column(Text)
    resources_required = Column(Text)
    estimated_cost = Column(VARCHAR(50))
    time_to_implement = Column(VARCHAR(50))
    risks = Column(Text)
    impact_score = Column(Integer)
    feasibility_score = Column(Integer)
    cost_efficiency_score = Column(Integer)
    final_score = Column(Float)
    is_adopted = Column(Boolean, default=False)
