from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from scrape.core.logger import logger
from scrape.db.database import get_repository
from scrape.db.repositories.products.product import ProductRepository
from scrape.models.products.product import ProductCreate, ProductUpdate, Product, ProductList

router = APIRouter()


@router.get("/", response_model=ProductList)
async def get_products(
    limit: int = 10,
    offset: int = 0,
    repo: ProductRepository = Depends(get_repository(ProductRepository)),
) -> ProductList:
    try:
        logger.info("Getting products")
        products = await repo.get_products(limit=limit, offset=offset)
        return products
    except Exception as e:
        logger.exception("Error getting products. Exception: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting products"
        )


@router.get("/{product_id}", response_model=Product)
async def get_product_by_id(
    product_id: UUID,
    repo: ProductRepository = Depends(get_repository(ProductRepository)),
) -> Product:
    try:
        logger.info("Getting product by ID: %s", product_id)
        product = await repo.get_product_by_id(product_id=product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error getting product by ID: %s. Exception: %s",
            product_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting product by ID"
        ) from e


@router.get("/url/{product_url}", response_model=Product)
async def get_product_by_url(
    product_url: str,
    repo: ProductRepository = Depends(get_repository(ProductRepository)),
) -> Product:
    try:
        logger.info("Getting product by URL: %s", product_url)
        product = await repo.get_product_by_url(product_url=product_url)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error getting product by URL: %s. Exception: %s",
            product_url, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting product by URL"
        ) from e


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    repo: ProductRepository = Depends(get_repository(ProductRepository)),
) -> Product:
    try:
        logger.info("Creating product: %s", product.name)
        product_data = await repo.create_product(product_data=product)

        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already exists"
            )

        return product_data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error creating product: %s. Exception: %s",
            product.name, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating product"
        ) from e


@router.put("/{product_id}", response_model=Product)
async def update_product_by_id(
    product_id: UUID,
    product: ProductUpdate,
    repo: ProductRepository = Depends(get_repository(ProductRepository)),
) -> Product:
    try:
        logger.info("Updating product by ID: %s", product_id)
        product_data = await repo.update_product_by_id(product_id=product_id, product_data=product)

        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        return product_data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error updating product by ID: %s. Exception: %s",
            product_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating product by ID"
        ) from e


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_by_id(
    product_id: UUID,
    repo: ProductRepository = Depends(get_repository(ProductRepository)),
):
    try:
        logger.info("Deleting product by ID: %s", product_id)
        product = await repo.delete_product_by_id(product_id=product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        return
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error deleting product by ID: %s. Exception: %s",
            product_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting product by ID"
        ) from e
