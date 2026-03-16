"""
Pydantic Schemas - Request/Response validation
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
from models import UserRole, OrderStatus, PaymentMethod, ProductCategory


# ─────────────── AUTH ───────────────
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^[6-9][0-9]{9}$")
    password: str = Field(..., min_length=4)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.customer

class LoginRequest(BaseModel):
    phone: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole
    name: str


# ─────────────── SHOPS ───────────────
class ShopCreate(BaseModel):
    shop_name: str = Field(..., min_length=2)
    phone: str
    address: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ShopResponse(BaseModel):
    id: str
    shop_name: str
    phone: str
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    is_approved: bool
    is_open: bool
    rating: float
    rating_count: int
    image_url: Optional[str]
    created_at: datetime
    distance_km: Optional[float] = None  # Computed

    class Config:
        from_attributes = True


# ─────────────── PRODUCTS ───────────────
class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=1)
    category: ProductCategory
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    unit: str = "piece"
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    is_available: Optional[bool] = None
    description: Optional[str] = None

class ProductResponse(BaseModel):
    id: str
    shop_id: str
    product_name: str
    category: ProductCategory
    price: float
    stock: int
    unit: str
    is_available: bool
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────── ORDERS ───────────────
class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1)

class PlaceOrderRequest(BaseModel):
    shop_id: str
    items: List[OrderItemInput]
    delivery_name: str
    delivery_phone: str = Field(..., pattern=r"^[6-9][0-9]{9}$")
    delivery_address: str
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    delivery_slot: str = "asap"
    payment_method: PaymentMethod
    notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True

class OrderTrackingResponse(BaseModel):
    status: OrderStatus
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    user_id: str
    shop_id: str
    delivery_address: str
    delivery_name: str
    delivery_phone: str
    delivery_slot: str
    subtotal: float
    delivery_fee: float
    total_amount: float
    payment_method: PaymentMethod
    payment_status: str
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse] = []
    tracking: List[OrderTrackingResponse] = []

    class Config:
        from_attributes = True


# ─────────────── VENDOR ───────────────
class VendorOrderStatusUpdate(BaseModel):
    status: OrderStatus
    message: Optional[str] = None


# ─────────────── DELIVERY ───────────────
class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None

class DeliveryLocationResponse(BaseModel):
    partner_id: str
    latitude: float
    longitude: float
    is_online: bool
    updated_at: datetime

    class Config:
        from_attributes = True
