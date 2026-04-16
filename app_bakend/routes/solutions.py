from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app_backend.schemas.solution import SolutionView
from app_backend.database import get_db
from app_backend.models.solution import Solution
from app_backend.schemas.solution import SolutionCreate
from app_backend.services.scoring import calculate_final_score
from app_backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/problems", tags=["Problems"])

@router.post("/{problem_id}")
def submit_solution(
    problem_id: int,
    solution: SolutionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cost_efficiency = 5 if solution.estimated_cost.lower() == "low" else 3

    final_score = calculate_final_score(
        solution.impact_score,
        solution.feasibility_score,
        cost_efficiency,
        current_user.credibility_score
    )

    new_solution = Solution(
        problem_id=problem_id,
        proposed_by=current_user.id,
        cost_efficiency_score=cost_efficiency,
        final_score=final_score,
        **solution.dict()
    )

    db.add(new_solution)
    db.commit()
    return new_solution

#  view

@router.get(
    "/problem/{problem_id}",
    response_model=List[SolutionView]
)
def get_solutions_for_problem(
    problem_id: int,
    db: Session = Depends(get_db)
):
    solutions = (
        db.query(Solution)
        .filter(Solution.problem_id == problem_id)
        .order_by(Solution.final_score.desc())
        .all()
    )

    return solutions

