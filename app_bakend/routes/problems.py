from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
from typing import Optional
from datetime import datetime, timedelta
from app_backend.utils.storage import upload_image
from app_backend.database import get_db
from app_backend.models.user import User
from app_backend.models.problem import Problem
from app_backend.models.solution import Solution
from app_backend.schemas.problem import ProblemCreate, ProblemOut
from app_backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/problems",
    tags=["Problems"],
)


@router.post("/", response_model=ProblemOut)
def create_problem(
        problem: ProblemCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    new_problem = Problem(
        **problem.dict(),
        created_by=current_user.id,
        status="open",
        created_at = datetime.utcnow()
    )
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)
    return new_problem


@router.get("/")
def list_problems(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        category: Optional[str] = None,
        search: Optional[str] = Query(None),
        severity: Optional[str] = None,
        status: Optional[str] = None,
        sort: Optional[str] = "latest"
):
    query = db.query(Problem)

    if search:
        query = query.filter(
            or_(
                Problem.title.ilike(f"%{search}%"),
                Problem.description.ilike(f"%{search}%")
            )
        )

    if category:
        query = query.filter(Problem.category.ilike(f"%{category}%"))

    if severity:
        query = query.filter(Problem.severity == severity)

    if status:
        query = query.filter(Problem.status == status)

    if sort == "oldest":
        query = query.order_by(Problem.id.asc())
    else:
        query = query.order_by(Problem.id.desc())

    total_records = query.count()
    problems = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": (total_records + page_size - 1) // page_size,
        "data": problems
    }


@router.get("/featured")
def get_featured_problems(
        db: Session = Depends(get_db),
        limit: int = Query(3, ge=1, le=10)
):
    # Get recent problems that are open or under process (most relevant)
    featured = (
        db.query(Problem)
        .filter(Problem.status.in_(["open", "under_process"]))
        .order_by(desc(Problem.id))  # Get newest first
        .limit(limit)
        .all()
    )

    # If not enough recent problems, fill with any problems
    if len(featured) < limit:
        remaining = limit - len(featured)
        additional = (
            db.query(Problem)
            .filter(~Problem.id.in_([p.id for p in featured] if featured else []))
            .order_by(desc(Problem.id))
            .limit(remaining)
            .all()
        )
        featured.extend(additional)

    return featured


@router.get("/{problem_id}")
def get_problem(
        problem_id: int,
        db: Session = Depends(get_db)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    return problem


@router.post("/{problem_id}/upload-before-image")
def upload_before_image(
        problem_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if problem.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    image_path = upload_image(file, "before")
    problem.before_image_path = image_path
    db.commit()

    return {"message": "Before image uploaded successfully"}


@router.get("/stats")
def get_problems_stats(db: Session = Depends(get_db)):
    """Get comprehensive statistics for the dashboard"""
    try:
        # Get problem statistics
        total_problems = db.query(func.count(Problem.id)).scalar() or 0
        open_problems = db.query(func.count(Problem.id)).filter(
            Problem.status == "open"
        ).scalar() or 0
        under_process_problems = db.query(func.count(Problem.id)).filter(
            Problem.status == "under_process"
        ).scalar() or 0
        resolved_problems = db.query(func.count(Problem.id)).filter(
            Problem.status == "resolved"
        ).scalar() or 0

        # Get solution statistics
        total_solutions = db.query(func.count(Solution.id)).scalar() or 0
        adopted_solutions = db.query(func.count(Solution.id)).filter(
            Solution.is_adopted == True
        ).scalar() or 0

        # Get user statistics
        total_users = db.query(func.count(User.id)).scalar() or 0

        # Get recent problems for featured section
        recent_problems = db.query(Problem).filter(
            Problem.status.in_(["open", "under_process"])
        ).order_by(Problem.id.desc()).limit(3).all()

        # Convert problems to dictionaries
        featured_problems = []
        for p in recent_problems:
            problem_dict = {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "category": p.category,
                "location": p.location,
                "severity": p.severity,
                "status": p.status,
                "before_image_path": p.before_image_path,
                "created_by": p.created_by
            }
            # Handle created_at safely
            if hasattr(p, 'created_at') and p.created_at:
                if isinstance(p.created_at, str):
                    problem_dict["created_at"] = p.created_at
                else:
                    problem_dict["created_at"] = p.created_at.isoformat() if hasattr(p.created_at,
                                                                                     'isoformat') else str(p.created_at)
            else:
                problem_dict["created_at"] = None

            featured_problems.append(problem_dict)

        return {
            "stats": {
                "total_problems": total_problems,
                "open_problems": open_problems,
                "under_process_problems": under_process_problems,
                "resolved_problems": resolved_problems,
                "total_solutions": total_solutions,
                "adopted_solutions": adopted_solutions,
                "total_users": total_users
            },
            "featured_problems": featured_problems
        }
    except Exception as e:
        print(f"Error fetching stats: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return default values if there's an error
        return {
            "stats": {
                "total_problems": 0,
                "open_problems": 0,
                "under_process_problems": 0,
                "resolved_problems": 0,
                "total_solutions": 0,
                "adopted_solutions": 0,
                "total_users": 0
            },
            "featured_problems": []
        }