from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.config.db import get_db
from src.backend.models.user_model import User as Users
from src.backend.validations.validation import UserCreate, LoginUser
from src.backend.utils.util_helper import (
    create_access_token,
    hash_password,
    verify_password,
)

user_route = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@user_route.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email or username already exists
    existing_user = db.query(Users).filter(
        (Users.email == user.email) | (Users.username == user.username)
    ).first()

    if existing_user:
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    try:
        hashed_password = hash_password(user.password)

        new_user = Users(
            username=user.username,
            email=user.email,
            password=hashed_password,
            designation=user.designation,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(
            data={
                "email": new_user.email,
                "username": new_user.username,
                "user_id": new_user.id,
                "designation": new_user.designation.value,
            }
        )

        return {
            "status": "success",
            "message": "User registered successfully",
            "data": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "designation": new_user.designation.value,
                "token": token,
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating user: {str(e)}",
        )


@user_route.post("/login", status_code=status.HTTP_200_OK)
def login_user(user: LoginUser, db: Session = Depends(get_db)):
    # Fetch user by email
    db_user = db.query(Users).filter(Users.email == user.email).first()

    # Validate existence and password in one step (prevents user-enumeration)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check active status
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account. Please contact support.",
        )

    token = create_access_token(
        data={
            "email": db_user.email,
            "username": db_user.username,
            "user_id": db_user.id,
            "designation": db_user.designation.value,
        }
    )

    return {
        "status": "success",
        "message": "User logged in successfully",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "designation": db_user.designation.value,
            "token": token,
        },
    }