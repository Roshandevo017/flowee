"""
Auth Router - Register, Login
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth_utils import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=schemas.TokenResponse, status_code=201)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    # Check phone already exists
    if db.query(models.User).filter(models.User.phone == req.phone).first():
        raise HTTPException(status_code=400, detail="இந்த மொபைல் எண் ஏற்கனவே பதிவு செய்யப்பட்டது.")

    user = models.User(
        name=req.name,
        phone=req.phone,
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.TokenResponse(access_token=token, user_id=user.id, role=user.role, name=user.name)


@router.post("/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone == req.phone).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="தவறான மொபைல் எண் அல்லது கடவுச்சொல்.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="கணக்கு செயலிழக்கப்பட்டது.")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.TokenResponse(access_token=token, user_id=user.id, role=user.role, name=user.name)


@router.get("/me")
def get_me(current_user=Depends(__import__("auth_utils").get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "phone": current_user.phone, "role": current_user.role}
