"""
Admin Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from auth_utils import require_role

router = APIRouter()
admin_required = require_role(models.UserRole.admin)


@router.get("/shops/pending")
def get_pending_shops(db: Session = Depends(get_db), _=Depends(admin_required)):
    return db.query(models.Shop).filter(models.Shop.is_approved == False).all()


@router.put("/shops/{shop_id}/approve")
def approve_shop(shop_id: str, db: Session = Depends(get_db), _=Depends(admin_required)):
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(404, "கடை கிடைக்கவில்லை.")
    shop.is_approved = True
    db.commit()
    return {"message": f"{shop.shop_name} அங்கீகரிக்கப்பட்டது."}


@router.get("/users")
def list_users(role: str = None, db: Session = Depends(get_db), _=Depends(admin_required)):
    q = db.query(models.User)
    if role:
        q = q.filter(models.User.role == role)
    return q.all()


@router.get("/orders")
def list_orders(status: str = None, db: Session = Depends(get_db), _=Depends(admin_required)):
    q = db.query(models.Order)
    if status:
        q = q.filter(models.Order.status == status)
    return q.order_by(models.Order.created_at.desc()).limit(100).all()


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _=Depends(admin_required)):
    from sqlalchemy import func
    return {
        "total_users": db.query(func.count(models.User.id)).scalar(),
        "total_shops": db.query(func.count(models.Shop.id)).scalar(),
        "pending_shops": db.query(func.count(models.Shop.id)).filter(models.Shop.is_approved == False).scalar(),
        "total_orders": db.query(func.count(models.Order.id)).scalar(),
        "total_revenue": db.query(func.sum(models.Order.total_amount)).filter(models.Order.status == "delivered").scalar() or 0
    }
