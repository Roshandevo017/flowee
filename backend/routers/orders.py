"""
Orders Router - Place order, track order
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
import models, schemas
from auth_utils import get_current_user, require_role

router = APIRouter()


@router.post("/place", response_model=schemas.OrderResponse, status_code=201)
def place_order(
    req: schemas.PlaceOrderRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate shop
    shop = db.query(models.Shop).filter(
        models.Shop.id == req.shop_id,
        models.Shop.is_approved == True,
        models.Shop.is_open == True
    ).first()
    if not shop:
        raise HTTPException(400, "கடை கிடைக்கவில்லை அல்லது மூடப்பட்டுள்ளது.")

    # Build order items & calculate total
    order_items = []
    subtotal = 0.0
    for item_in in req.items:
        product = db.query(models.Product).filter(
            models.Product.id == item_in.product_id,
            models.Product.shop_id == req.shop_id,
            models.Product.is_available == True
        ).first()
        if not product:
            raise HTTPException(400, f"தயாரிப்பு {item_in.product_id} கிடைக்கவில்லை.")
        if product.stock < item_in.quantity:
            raise HTTPException(400, f"{product.product_name} - இருப்பு போதாது.")

        item_sub = product.price * item_in.quantity
        subtotal += item_sub
        order_items.append(models.OrderItem(
            product_id=product.id,
            product_name=product.product_name,
            quantity=item_in.quantity,
            unit_price=product.price,
            subtotal=item_sub
        ))
        # Decrement stock
        product.stock -= item_in.quantity

    delivery_fee = 30.0
    total = subtotal + delivery_fee

    order = models.Order(
        user_id=current_user.id,
        shop_id=req.shop_id,
        delivery_name=req.delivery_name,
        delivery_phone=req.delivery_phone,
        delivery_address=req.delivery_address,
        delivery_city=req.delivery_city,
        delivery_pincode=req.delivery_pincode,
        delivery_lat=req.delivery_lat,
        delivery_lng=req.delivery_lng,
        delivery_slot=req.delivery_slot,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total,
        payment_method=req.payment_method,
        notes=req.notes,
        status=models.OrderStatus.placed
    )
    order.items = order_items

    # Initial tracking entry
    order.tracking = [
        models.OrderTracking(
            status=models.OrderStatus.placed,
            message="ஆர்டர் பெறப்பட்டது. கடை உறுதிப்படுத்தும் வரை காத்திருக்கவும்.",
            updated_by=current_user.id
        )
    ]

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}/track", response_model=schemas.OrderResponse)
def track_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "ஆர்டர் கிடைக்கவில்லை.")
    if order.user_id != current_user.id and current_user.role not in [
        models.UserRole.admin, models.UserRole.vendor, models.UserRole.delivery
    ]:
        raise HTTPException(403, "அணுகல் மறுக்கப்பட்டது.")
    return order


@router.get("/my/orders", response_model=List[schemas.OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Order).filter(
        models.Order.user_id == current_user.id
    ).order_by(models.Order.created_at.desc()).all()
