"""
SQLAlchemy ORM Models - Maps to PostgreSQL tables
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid


def gen_id():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    customer = "customer"
    vendor = "vendor"
    delivery = "delivery"
    admin = "admin"


class OrderStatus(str, enum.Enum):
    placed = "placed"
    accepted = "accepted"
    preparing = "preparing"
    ready = "ready"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"
    rejected = "rejected"


class PaymentMethod(str, enum.Enum):
    cod = "COD"
    upi = "UPI"
    card = "Card"


class ProductCategory(str, enum.Enum):
    jasmine = "jasmine"
    rose = "rose"
    garland = "garland"
    loose = "loose"
    pooja = "pooja"
    decoration = "decoration"


# ─────────────── USERS ───────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True, default=gen_id)
    name          = Column(String(100), nullable=False)
    phone         = Column(String(15), unique=True, nullable=False, index=True)
    email         = Column(String(150), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.customer, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    orders        = relationship("Order", back_populates="customer", foreign_keys="Order.user_id")
    shop          = relationship("Shop", back_populates="owner", uselist=False)


# ─────────────── SHOPS ───────────────
class Shop(Base):
    __tablename__ = "shops"

    id           = Column(String, primary_key=True, default=gen_id)
    owner_id     = Column(String, ForeignKey("users.id"), nullable=False)
    shop_name    = Column(String(150), nullable=False)
    description  = Column(Text, nullable=True)
    phone        = Column(String(15), nullable=False)
    address      = Column(Text, nullable=False)
    latitude     = Column(Float, nullable=True)
    longitude    = Column(Float, nullable=True)
    is_approved  = Column(Boolean, default=False)
    is_open      = Column(Boolean, default=True)
    rating       = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    image_url    = Column(String(500), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    owner        = relationship("User", back_populates="shop")
    products     = relationship("Product", back_populates="shop")
    orders       = relationship("Order", back_populates="shop")


# ─────────────── PRODUCTS ───────────────
class Product(Base):
    __tablename__ = "products"

    id           = Column(String, primary_key=True, default=gen_id)
    shop_id      = Column(String, ForeignKey("shops.id"), nullable=False)
    product_name = Column(String(150), nullable=False)
    category     = Column(SAEnum(ProductCategory), nullable=False)
    price        = Column(Float, nullable=False)
    stock        = Column(Integer, default=0)
    unit         = Column(String(20), default="piece")  # kg, bunch, piece, meter
    description  = Column(Text, nullable=True)
    image_url    = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    shop         = relationship("Shop", back_populates="products")
    order_items  = relationship("OrderItem", back_populates="product")


# ─────────────── ORDERS ───────────────
class Order(Base):
    __tablename__ = "orders"

    id                  = Column(String, primary_key=True, default=gen_id)
    user_id             = Column(String, ForeignKey("users.id"), nullable=False)
    shop_id             = Column(String, ForeignKey("shops.id"), nullable=False)
    delivery_partner_id = Column(String, ForeignKey("users.id"), nullable=True)

    delivery_name       = Column(String(100), nullable=False)
    delivery_phone      = Column(String(15), nullable=False)
    delivery_address    = Column(Text, nullable=False)
    delivery_city       = Column(String(100), nullable=True)
    delivery_pincode    = Column(String(10), nullable=True)
    delivery_lat        = Column(Float, nullable=True)
    delivery_lng        = Column(Float, nullable=True)
    delivery_slot       = Column(String(50), default="asap")

    subtotal            = Column(Float, nullable=False)
    delivery_fee        = Column(Float, default=30.0)
    total_amount        = Column(Float, nullable=False)
    payment_method      = Column(SAEnum(PaymentMethod), nullable=False)
    payment_status      = Column(String(20), default="pending")  # pending, paid

    status              = Column(SAEnum(OrderStatus), default=OrderStatus.placed)
    notes               = Column(Text, nullable=True)

    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())
    delivered_at        = Column(DateTime(timezone=True), nullable=True)

    customer            = relationship("User", back_populates="orders", foreign_keys=[user_id])
    shop                = relationship("Shop", back_populates="orders")
    items               = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tracking            = relationship("OrderTracking", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(String, primary_key=True, default=gen_id)
    order_id   = Column(String, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(150))  # snapshot at order time
    quantity   = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal   = Column(Float, nullable=False)

    order      = relationship("Order", back_populates="items")
    product    = relationship("Product", back_populates="order_items")


class OrderTracking(Base):
    __tablename__ = "order_tracking"

    id         = Column(String, primary_key=True, default=gen_id)
    order_id   = Column(String, ForeignKey("orders.id"), nullable=False)
    status     = Column(SAEnum(OrderStatus), nullable=False)
    message    = Column(String(300), nullable=True)
    updated_by = Column(String, nullable=True)  # user_id who changed status
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order      = relationship("Order", back_populates="tracking")


# ─────────────── DELIVERY LOCATION ───────────────
class DeliveryLocation(Base):
    """Real-time delivery partner GPS location"""
    __tablename__ = "delivery_locations"

    id         = Column(String, primary_key=True, default=gen_id)
    partner_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    latitude   = Column(Float, nullable=False)
    longitude  = Column(Float, nullable=False)
    accuracy   = Column(Float, nullable=True)
    is_online  = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
