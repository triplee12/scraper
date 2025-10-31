from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., description="Product name")
    url: str = Field(..., description="Product URL")
    price: Optional[float] = Field(None, description="Product price")
    category: str = Field(..., description="Product category")
    retailer: str = Field(..., description="Retailer name")


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: UUID = Field(..., description="Product ID")
    price: Optional[float] = Field(None, description="Product price")
    created_at: datetime = Field(..., description="Product created at")
    updated_at: datetime = Field(..., description="Product updated at")


class ProductList(BaseModel):
    products: List[Product]
    total: int