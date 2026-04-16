from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app_backend.database import get_db
from app_backend.models.user import User
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from app_backend.schemas.user import ForgotPasswordRequest, ResetPasswordRequest
from app_backend.schemas.user import UserCreate, Token
from app_backend.models.token_blacklist import TokenBlacklist
from app_backend.utils.dependencies import get_current_user
from fastapi.security import OAuth2PasswordBearer
from app_backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_reset_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# registration
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password length before hashing
    if len(user.password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 72 characters or less"
        )

    if len(user.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "email": new_user.email
    }


# login
@router.post("/login", response_model=Token)
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    print(f"Login attempt for email: {form_data.username}")
    print(f"User found: {user is not None}")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    password_match = verify_password(form_data.password, user.password_hash)
    print(f"Password match: {password_match}")

    if not password_match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    print(f"Login successful for user: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# logout
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/logout")
def logout(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    revoked = TokenBlacklist(token=token)
    db.add(revoked)
    db.commit()
    return {"message": "Logged out successfully"}


# forgot-password
@router.post("/forgot-password")
def forgot_password(
        request: ForgotPasswordRequest,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        return {"message": "If the email exists, a reset link has been sent"}

    token = generate_reset_token()
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    return {
        "message": "Password reset token generated",
        "reset_token": token
    }


# reset-password
@router.post("/reset-password")
def reset_password(
        request: ResetPasswordRequest,
        db: Session = Depends(get_db)
):
    # Validate password length before processing
    if len(request.new_password) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must be 72 characters or less"
        )

    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )

    user = db.query(User).filter(
        User.reset_token == request.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    if user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired"
        )

    # Hash the new password
    user.password_hash = hash_password(request.new_password)
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return {"message": "Password reset successful"}