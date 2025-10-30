from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., description="Product name")
    url: str = Field(..., description="Product URL")
    price: Optional[float] = Field(None, description="Product price")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Product name")
    url: Optional[str] = Field(None, description="Product URL")
    price: Optional[float] = Field(None, description="Product price")


class Product(BaseModel):
    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    url: str = Field(..., description="Product URL")
    price: Optional[float] = Field(None, description="Product price")
    created_at: datetime = Field(..., description="Product created at")
    updated_at: datetime = Field(..., description="Product updated at")


class ProductList(BaseModel):
    products: List[Product]
    total: int