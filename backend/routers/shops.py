"""
Shops Router - Nearby shops using Haversine distance
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import math

from database import get_db
import models, schemas
from auth_utils import get_current_user, require_role

router = APIRouter()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in km"""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


@router.get("/nearby", response_model=List[schemas.ShopResponse])
def get_nearby_shops(
    lat: float = Query(..., ge=-90, le=90, description="User latitude"),
    lng: float = Query(..., ge=-180, le=180, description="User longitude"),
    radius_km: float = Query(10.0, ge=0.5, le=50.0, description="Search radius in km"),
    db: Session = Depends(get_db)
):
    """
    Fetch approved, open shops within radius_km of (lat, lng).
    Uses Haversine formula - no external API needed.
    Sorted by distance ascending.
    """
    shops = db.query(models.Shop).filter(
        models.Shop.is_approved == True,
        models.Shop.is_open == True,
        models.Shop.latitude.isnot(None),
        models.Shop.longitude.isnot(None)
    ).all()

    result = []
    for shop in shops:
        dist = haversine_km(lat, lng, shop.latitude, shop.longitude)
        if dist <= radius_km:
            shop_data = schemas.ShopResponse.from_orm(shop)
            shop_data.distance_km = round(dist, 2)
            result.append(shop_data)

    result.sort(key=lambda s: s.distance_km)
    return result


@router.get("/{shop_id}", response_model=schemas.ShopResponse)
def get_shop(shop_id: str, db: Session = Depends(get_db)):
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(404, "கடை கிடைக்கவில்லை")
    return shop


@router.get("/{shop_id}/products", response_model=List[schemas.ProductResponse])
def get_shop_products(
    shop_id: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(
        models.Product.shop_id == shop_id,
        models.Product.is_available == True
    )
    if category:
        query = query.filter(models.Product.category == category)
    return query.order_by(models.Product.product_name).all()
