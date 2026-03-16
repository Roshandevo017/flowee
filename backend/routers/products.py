"""
Products Router - Browse/search products across all shops
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from database import get_db
import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.ProductResponse])
def search_products(
    q: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None, description="jasmine | rose | garland | loose | pooja | decoration"),
    shop_id: Optional[str] = Query(None, description="Filter by specific shop"),
    db: Session = Depends(get_db)
):
    """
    Search/browse products across all approved open shops.
    Used by home.html search bar and category tiles.
    """
    query = db.query(models.Product).join(models.Shop).filter(
        models.Product.is_available == True,
        models.Shop.is_approved == True,
        models.Shop.is_open == True
    )
    if q:
        query = query.filter(models.Product.product_name.ilike(f"%{q}%"))
    if category:
        query = query.filter(models.Product.category == category)
    if shop_id:
        query = query.filter(models.Product.shop_id == shop_id)

    return query.order_by(models.Product.product_name).limit(50).all()


@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get single product by ID"""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_available == True
    ).first()
    if not product:
        raise HTTPException(404, "தயாரிப்பு கிடைக்கவில்லை.")
    return product