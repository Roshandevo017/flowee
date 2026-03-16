"""
பூ மார்ட் - Poo Mart Hyperlocal Flower Platform
FastAPI Backend - Professional Grade
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn

from database import engine, Base
from routers import auth, shops, products, orders, vendor, delivery, admin

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="பூ மார்ட் API",
    description="Hyperlocal Flower Ordering Platform - Tamil Nadu",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - allow frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod: ["https://poomart.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router,       prefix="/api/auth",     tags=["Auth"])
app.include_router(shops.router,      prefix="/api/shops",    tags=["Shops"])
app.include_router(products.router,   prefix="/api/products", tags=["Products"])
app.include_router(orders.router,     prefix="/api/orders",   tags=["Orders"])
app.include_router(vendor.router,     prefix="/api/vendor",   tags=["Vendor"])
app.include_router(delivery.router,   prefix="/api/delivery", tags=["Delivery"])
app.include_router(admin.router,      prefix="/api/admin",    tags=["Admin"])

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "பூ மார்ட் API is running 🌸",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
