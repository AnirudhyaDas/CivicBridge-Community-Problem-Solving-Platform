from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app_backend.utils.storage import upload_image
from sqlalchemy.orm import Session
from app_backend.database import get_db
from app_backend.utils.dependencies import admin_only
from app_backend.models.solution import Solution
from app_backend.models.problem import Problem
from sqlalchemy import func
from app_backend.models.user import User
from datetime import datetime, timedelta
import csv
from fastapi.responses import StreamingResponse
from io import StringIO

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(admin_only)]
)

# ACCEPT PROBLEM (mark as UNDER_PROCESS)

@router.post("/problems/{problem_id}/accept")
def accept_problem(
    problem_id: int,
    db: Session = Depends(get_db)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if problem.status != "open":
        raise HTTPException(
            status_code=400,
            detail="Problem is already under process or resolved"
        )

    problem.status = "under_process"
    db.commit()

    return {
        "message": "Problem accepted and marked as under process",
        "problem_id": problem.id,
        "status": problem.status
    }

# ADOPT SOLUTION (mark problem as RESOLVED)

@router.post("/adopt/{solution_id}")
def adopt_solution(
    solution_id: int,
    db: Session = Depends(get_db)
):
    solution = db.query(Solution).filter(
        Solution.id == solution_id
    ).first()

    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    solution.is_adopted = True

    problem = db.query(Problem).filter(
        Problem.id == solution.problem_id
    ).first()

    if problem:
        problem.status = "resolved"

    db.commit()

    return {
        "message": "Solution adopted and problem marked as resolved",
        "solution_id": solution.id,
        "problem_id": solution.problem_id
    }

# DELETE PROBLEM (ADMIN MODERATION)

@router.delete("/problems/{problem_id}")
def delete_problem(
    problem_id: int,
    db: Session = Depends(get_db)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    db.delete(problem)
    db.commit()

    return {
        "message": "Problem deleted successfully",
        "problem_id": problem_id
    }

# Upload after image

@router.post("/solutions/{solution_id}/upload-after-image")
def upload_after_image(
    solution_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin = Depends(admin_only)
):
    solution = db.query(Solution).filter(Solution.id == solution_id).first()

    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    image_path = upload_image(file, "after")
    solution.after_image_path = image_path

    db.commit()

    return {"message": "After image uploaded successfully"}

# ADMIN DASHBOARD SUMMARY

@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_problems = db.query(func.count(Problem.id)).scalar()
    open_problems = db.query(func.count(Problem.id)).filter(
        Problem.status == "open"
    ).scalar()
    under_process_problems = db.query(func.count(Problem.id)).filter(
        Problem.status == "under_process"
    ).scalar()
    resolved_problems = db.query(func.count(Problem.id)).filter(
        Problem.status == "resolved"
    ).scalar()

    total_solutions = db.query(func.count(Solution.id)).scalar()
    adopted_solutions = db.query(func.count(Solution.id)).filter(
        Solution.is_adopted == True
    ).scalar()

    total_users = db.query(func.count(User.id)).scalar()

    return {
        "problems": {
            "total": total_problems,
            "open": open_problems,
            "under_process": under_process_problems,
            "resolved": resolved_problems
        },
        "solutions": {
            "total": total_solutions,
            "adopted": adopted_solutions
        },
        "users": {
            "total": total_users
        }
    }

@router.get("/dashboard/problems/open")
def open_problems(db: Session = Depends(get_db)):
    return db.query(Problem).filter(
        Problem.status == "open"
    ).order_by(Problem.id.desc()).all()

@router.get("/dashboard/problems/under-process")
def under_process_problems(db: Session = Depends(get_db)):
    return db.query(Problem).filter(
        Problem.status == "under_process"
    ).order_by(Problem.id.desc()).all()

@router.get("/dashboard/problems/resolved")
def resolved_problems(db: Session = Depends(get_db)):
    return db.query(Problem).filter(
        Problem.status == "resolved"
    ).order_by(Problem.id.desc()).all()

@router.get("/dashboard/solutions")
def solutions_overview(db: Session = Depends(get_db)):
    return {
        "total": db.query(Solution).count(),
        "adopted": db.query(Solution).filter(
            Solution.is_adopted == True
        ).count(),
        "pending": db.query(Solution).filter(
            Solution.is_adopted == False
        ).count()
    }

# CHARTS

@router.get("/charts/problems/status")
def problem_status_distribution(db: Session = Depends(get_db)):
    data = (
        db.query(Problem.status, func.count(Problem.id))
        .group_by(Problem.status)
        .all()
    )

    return {
        "labels": [row[0] for row in data],
        "values": [row[1] for row in data]
    }

@router.get("/charts/solutions/adoption")
def solution_adoption_distribution(db: Session = Depends(get_db)):
    adopted = db.query(Solution).filter(
        Solution.is_adopted == True
    ).count()

    pending = db.query(Solution).filter(
        Solution.is_adopted == False
    ).count()

    return {
        "labels": ["adopted", "pending"],
        "values": [adopted, pending]
    }

@router.get("/charts/problems/time-series")
def problems_time_series(
    days: int = 7,
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)

    data = (
        db.query(
            func.date(Problem.created_at),
            func.count(Problem.id)
        )
        .filter(Problem.created_at >= start_date)
        .group_by(func.date(Problem.created_at))
        .order_by(func.date(Problem.created_at))
        .all()
    )

    return {
        "labels": [str(row[0]) for row in data],
        "values": [row[1] for row in data]
    }

@router.get("/charts/problems/growth")
def problem_growth_chart(
    days: int = 30,
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)

    daily_counts = (
        db.query(
            func.date(Problem.created_at),
            func.count(Problem.id)
        )
        .filter(Problem.created_at >= start_date)
        .group_by(func.date(Problem.created_at))
        .order_by(func.date(Problem.created_at))
        .all()
    )

    cumulative = []
    total = 0

    for _, count in daily_counts:
        total += count
        cumulative.append(total)

    return {
        "labels": [str(row[0]) for row in daily_counts],
        "values": cumulative
    }

@router.get("/dashboard/admin-performance")
def admin_performance(db: Session = Depends(get_db)):
    accepted = db.query(Problem).filter(
        Problem.status == "under_process"
    ).count()

    resolved = db.query(Problem).filter(
        Problem.status == "resolved"
    ).count()

    total_handled = accepted + resolved

    resolution_rate = (
        (resolved / total_handled) * 100
        if total_handled > 0 else 0
    )

    return {
        "accepted_problems": accepted,
        "resolved_problems": resolved,
        "resolution_rate_percent": round(resolution_rate, 2)
    }


@router.get("/export/problems")
def export_problems_csv(db: Session = Depends(get_db)):
    problems = db.query(Problem).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Title", "Description", "Category", "Location",
        "Severity", "Status", "Created By"
    ])

    for p in problems:
        writer.writerow([
            p.id,
            p.title,
            p.description,
            p.category,
            p.location,
            p.severity,
            p.status,
            p.created_by
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=problems_report.csv"
        }
    )