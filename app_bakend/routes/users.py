from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime

from app_backend.database import get_db
from app_backend.utils.dependencies import get_current_user
from app_backend.schemas.user import UserProfileOut, UserProfileUpdate
from app_backend.models.user import User
from app_backend.models.problem import Problem
from app_backend.models.solution import Solution
from app_backend.utils.storage import upload_profile_image, delete_image

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/me", response_model=UserProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    # Convert datetime to ISO format string for JSON serialization
    user_data = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "address": current_user.address,
        "bio": current_user.bio,
        "role": current_user.role,
        "credibility_score": current_user.credibility_score,
        "profile_image": current_user.profile_image,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
    return user_data


@router.put("/me", response_model=UserProfileOut)
def update_my_profile(
        updates: UserProfileUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    for field, value in updates.dict(exclude_unset=True).items():
        if value is not None:
            setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    # Return serialized response
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "address": current_user.address,
        "bio": current_user.bio,
        "role": current_user.role,
        "credibility_score": current_user.credibility_score,
        "profile_image": current_user.profile_image,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.get("/dashboard")
def user_dashboard(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    problems = db.query(Problem).filter(
        Problem.created_by == current_user.id
    ).all()

    solutions = db.query(Solution).filter(
        Solution.proposed_by == current_user.id
    ).all()

    return {
        "profile": {
            "name": current_user.name,
            "email": current_user.email,
            "credibility_score": current_user.credibility_score
        },
        "stats": {
            "problems_posted": len(problems),
            "solutions_submitted": len(solutions)
        },
        "my_problems": problems,
        "my_solutions": solutions
    }


@router.post("/me/profile-picture")
def upload_or_replace_profile_picture(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400,
            detail="Only JPG or PNG images are allowed"
        )

    # 🔥 Delete old image if exists
    if current_user.profile_image:
        delete_image(
            path=current_user.profile_image,
            bucket="profile-images"
        )

    # Upload new image
    image_path = upload_profile_image(file, current_user.id)

    current_user.profile_image = image_path
    db.commit()

    return {
        "message": "Profile picture updated successfully",
        "profile_image": image_path
    }


@router.delete("/me/profile-picture")
def delete_profile_picture(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.profile_image:
        raise HTTPException(
            status_code=400,
            detail="No profile picture to delete"
        )

    delete_image(
        path=current_user.profile_image,
        bucket="profile-images"
    )

    current_user.profile_image = None
    db.commit()

    return {
        "message": "Profile picture deleted successfully"
    }