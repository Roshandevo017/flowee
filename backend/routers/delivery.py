"""
Delivery Router - Assigned orders, pickup/delivery confirmation, GPS location
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
import models, schemas
from auth_utils import require_role

router = APIRouter()

delivery_required = require_role(models.UserRole.delivery)


@router.get("/orders", response_model=List[schemas.OrderResponse])
def get_assigned_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(delivery_required)
):
    """Get orders assigned to this delivery partner"""
    return db.query(models.Order).filter(
        models.Order.delivery_partner_id == current_user.id,
        models.Order.status.in_(["ready", "out_for_delivery"])
    ).order_by(models.Order.created_at.desc()).all()


@router.put("/orders/{order_id}/pickup")
def confirm_pickup(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(delivery_required)
):
    """Delivery partner confirms they picked up the order from shop"""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.delivery_partner_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(404, "ஆர்டர் கிடைக்கவில்லை.")
    if order.status != models.OrderStatus.ready:
        raise HTTPException(400, f"Pickup செய்ய முடியாது. தற்போதைய நிலை: {order.status}")

    order.status = models.OrderStatus.out_for_delivery
    tracking = models.OrderTracking(
        order_id=order_id,
        status=models.OrderStatus.out_for_delivery,
        message="டெலிவரி பார்ட்னர் பூக்களை எடுத்துள்ளார். வழியில் உள்ளார்.",
        updated_by=current_user.id
    )
    db.add(tracking)
    db.commit()
    return {"message": "Pickup உறுதிப்படுத்தப்பட்டது."}


@router.put("/orders/{order_id}/delivered")
def confirm_delivery(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(delivery_required)
):
    """Confirm order delivered to customer"""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.delivery_partner_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(404, "ஆர்டர் கிடைக்கவில்லை.")
    if order.status != models.OrderStatus.out_for_delivery:
        raise HTTPException(400, f"வழங்கல் உறுதிப்படுத்த முடியாது. தற்போதைய நிலை: {order.status}")

    order.status = models.OrderStatus.delivered
    order.delivered_at = datetime.utcnow()
    if order.payment_method == models.PaymentMethod.cod:
        order.payment_status = "paid"

    tracking = models.OrderTracking(
        order_id=order_id,
        status=models.OrderStatus.delivered,
        message="ஆர்டர் வழங்கப்பட்டது. நன்றி!",
        updated_by=current_user.id
    )
    db.add(tracking)
    db.commit()
    return {"message": "டெலிவரி உறுதிப்படுத்தப்பட்டது."}


@router.put("/location")
def update_location(
    req: schemas.LocationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(delivery_required)
):
    """
    Update delivery partner's real-time GPS location.
    Called every ~5-10 seconds from delivery_orders.html.
    Stored in delivery_locations table (upsert).
    """
    location = db.query(models.DeliveryLocation).filter(
        models.DeliveryLocation.partner_id == current_user.id
    ).first()

    if location:
        location.latitude = req.latitude
        location.longitude = req.longitude
        location.accuracy = req.accuracy
        location.is_online = True
    else:
        location = models.DeliveryLocation(
            partner_id=current_user.id,
            latitude=req.latitude,
            longitude=req.longitude,
            accuracy=req.accuracy,
            is_online=True
        )
        db.add(location)

    db.commit()
    return {"message": "இடம் புதுப்பிக்கப்பட்டது.", "lat": req.latitude, "lng": req.longitude}


@router.get("/location/{partner_id}", response_model=schemas.DeliveryLocationResponse)
def get_partner_location(
    partner_id: str,
    db: Session = Depends(get_db)
    # In prod, restrict: current_user = Depends(get_current_user)
):
    """
    Get real-time location of a delivery partner.
    Used by customer ordertrack.html to show live delivery position.
    """
    location = db.query(models.DeliveryLocation).filter(
        models.DeliveryLocation.partner_id == partner_id
    ).first()
    if not location:
        raise HTTPException(404, "இடம் கிடைக்கவில்லை.")
    return location


@router.put("/offline")
def go_offline(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(delivery_required)
):
    location = db.query(models.DeliveryLocation).filter(
        models.DeliveryLocation.partner_id == current_user.id
    ).first()
    if location:
        location.is_online = False
        db.commit()
    return {"message": "Offline ஆனீர்கள்."}
