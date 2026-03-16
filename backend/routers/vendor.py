"""
Vendor Router - Shop management, products, orders
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
import models, schemas
from auth_utils import require_role

router = APIRouter()

vendor_required = require_role(models.UserRole.vendor)


@router.get("/orders", response_model=List[schemas.OrderResponse])
def get_vendor_orders(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(vendor_required)
):
    """Get all orders for vendor's shop"""
    if not current_user.shop:
        raise HTTPException(404, "கடை கண்டுபிடிக்கவில்லை.")
    query = db.query(models.Order).filter(models.Order.shop_id == current_user.shop.id)
    if status:
        query = query.filter(models.Order.status == status)
    return query.order_by(models.Order.created_at.desc()).all()


@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: str,
    req: schemas.VendorOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(vendor_required)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.shop_id == current_user.shop.id
    ).first()
    if not order:
        raise HTTPException(404, "ஆர்டர் கிடைக்கவில்லை.")

    order.status = req.status
    if req.status == models.OrderStatus.delivered:
        order.delivered_at = datetime.utcnow()

    tracking = models.OrderTracking(
        order_id=order_id,
        status=req.status,
        message=req.message,
        updated_by=current_user.id
    )
    db.add(tracking)
    db.commit()
    return {"message": "நிலை புதுப்பிக்கப்பட்டது.", "status": req.status}


@router.post("/products", response_model=schemas.ProductResponse, status_code=201)
def add_product(
    req: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(vendor_required)
):
    if not current_user.shop:
        raise HTTPException(404, "கடை கண்டுபிடிக்கவில்லை.")
    product = models.Product(shop_id=current_user.shop.id, **req.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: str,
    req: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(vendor_required)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.shop_id == current_user.shop.id
    ).first()
    if not product:
        raise HTTPException(404, "தயாரிப்பு கிடைக்கவில்லை.")
    for field, value in req.dict(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(vendor_required)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.shop_id == current_user.shop.id
    ).first()
    if not product:
        raise HTTPException(404, "தயாரிப்பு கிடைக்கவில்லை.")
    db.delete(product)
    db.commit()
    return {"message": "தயாரிப்பு நீக்கப்பட்டது."}


@router.get("/dashboard/stats")
def get_vendor_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(vendor_required)
):
    if not current_user.shop:
        raise HTTPException(404, "கடை கண்டுபிடிக்கவில்லை.")
    shop_id = current_user.shop.id
    from sqlalchemy import func

    total_orders = db.query(func.count(models.Order.id)).filter(models.Order.shop_id == shop_id).scalar()
    pending_orders = db.query(func.count(models.Order.id)).filter(
        models.Order.shop_id == shop_id,
        models.Order.status.in_(["placed", "accepted", "preparing"])
    ).scalar()
    total_revenue = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.shop_id == shop_id,
        models.Order.status == "delivered"
    ).scalar() or 0

    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_revenue": total_revenue,
        "shop_rating": current_user.shop.rating,
        "product_count": len(current_user.shop.products)
    }
